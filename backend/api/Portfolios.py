import abc
from datetime import date, datetime, timedelta
from logging import DEBUG, INFO, Logger
import unittest
from numpy import ndarray, number
import numpy
import pandas as pd
from Transaction import Transaction, BUY, SELL
from dateutils import strtodatetime, todatetime
from exceptions import PMException
from PositionIdentifier import Currency, PositionIdentifier, CASH, EQUITY, Ticker, check_currency
from Positions import Positions
from TimeSeries import TimeSeries
from pmdata import fx_convert
from pmdata import get_timeseries, get_ticker, get_fx_timeseries
from config import init_logging
from copy import deepcopy


#List of currencies supported by the system
DEFAULT_VALUATION_DATAPOINT='adjusted_close'
DEFAULT_CURRENCY='USD'
DEFAULT_INSTRUMENT_TYPE='Common Stock'
DEFAULT_MARKET_CODE='US'
DEFAULT_ORIGIN = datetime(2000,1,1)

logger:Logger = init_logging("api")


class Portfolio:
    '''
    A portfolio is:
    . A collection of instruments
    . Quantities of these instruments
    '''
    def __init__(self, name:str="DEFAULT", origin_date:datetime=DEFAULT_ORIGIN) -> None:
        self.positions={}
        self.positions[origin_date]= {"positions":Positions(), "transactions":[]}
        self.name = name
        self.origin = origin_date
        idx=pd.date_range(origin_date, date.today(), freq='D')
        self.constituents_eval_dates = pd.Series(data=numpy.zeros(idx.shape, dtype=bool), index=idx)
        # The origin is always evaluated
        self.constituents_eval_dates[self.origin] = True

    def copy(self):
        return deepcopy(self)

    def state(self)->dict:
        '''
        Returns a serializable state (a dictionary) containing the portfolio state
        '''
        toreturn:dict={}
        # Evaluate the portfolio constituents before serialization
        self._evaluate_constituents()
        toreturn['name']=self.name
        toreturn['positions'] = self._serialize_positions()
        toreturn['origin'] = self.origin
        return toreturn

    def _serialize_positions(self)->list:
        to_return = []
        dates = sorted(self.positions.keys())
        for date in dates:
            state={'positions':self._serialize_constituents(self.positions[date]['positions']), 'transactions':self._serialize_transactions(self.positions[date]['transactions']), 'date':date}
            to_return.append(state)
        return to_return

    def _serialize_constituents(self, pos:Positions):
        return pos.state()

    def _serialize_transactions(self, transactions:list)->list:
        toreturn = []
        for transaction in transactions:
            toreturn.append(transaction.state())
        return toreturn

    def get_name(self)->str:
        '''
        Returns the name of the portfolio
        '''
        return self.name

    def get_start_date(self)->datetime:
        '''
        Returns the start date of the portfolio
        '''
        return self.origin

    def _invalidate_constituents_evaluation(self, date:datetime):
        self.constituents_eval_dates.iloc[(date-self.origin).days:]=False

    def _evaluate_constituents(self):
        #Find the most recent evaluated date
        fromdate = self.constituents_eval_dates[self.constituents_eval_dates==True].last_valid_index()
        if(fromdate != None):
            self._evaluate_constituents_from(fromdate+timedelta(days=1), self.get_positions(fromdate))
            self.constituents_eval_dates[fromdate:]=True
    
    def _evaluate_constituents_from(self,fromdate:datetime, initial_positions):
        logger.debug(f"Evaluating constituents from {fromdate}")
        eval_dates = sorted(self.positions.keys())
        previous_positions = initial_positions   
        for eval_date in eval_dates:
            if(eval_date >= fromdate):
                logger.debug(f"Evaluating portfolio constituents for {eval_date}")
                portfolio_positions = self._evaluate_constituents_for(previous_positions, self.positions[eval_date]["transactions"], eval_date)
                self.positions[eval_date]["positions"]=portfolio_positions
                previous_positions = portfolio_positions


    def _find_latest_evaluation(self, date):
        eval_dates = sorted(self.positions.keys())
        toreturn=self.get_start_date()

        for eval_date in eval_dates:
            if(eval_date > date): return toreturn
            toreturn = eval_date
        return toreturn

    def _evaluate_constituents_for(self,previous_positions:Positions, transactions:list, date:datetime):
        # Compute the new portfolio constituents from the list of transactions
        # Create a set of positions from the current set
        # Apply the transactions
        # Get and return the resulting positions
        logger.debug(f"Applying {len(transactions)} transactions to portfolio on {date}")
        p:Positions = previous_positions.copy()
        for transaction in transactions:
            p.apply_transaction(transaction)
        return p

    def get_positions(self, posdate:datetime=None) -> Positions:
        '''
        Returns the list of positions of the portfolio in a dictionary keyed by ticker.
        If the date is not given, will return the portfolio positions at inception date (origin)
        '''
        if(posdate == None):
            return self.positions[self.origin]['positions']
        else: posdate = todatetime(posdate)
        # Check if the positions have to be evaluated
        if(self.constituents_eval_dates.index[0] > posdate):
            raise PMException(f"Cannot return the positions of portfolio {self.get_name()} at {posdate} because this portfolio start date is {self.get_start_date()}.")
        if(self.constituents_eval_dates.at[posdate] == False):
            #Evaluate constituents
            self._evaluate_constituents()
        #Find the latest evaluation date
        eval_date=self._find_latest_evaluation(posdate)
        return self.positions[eval_date]['positions']


    def add(self, currency:str, quantity:number, date:datetime = None, tags:set=None, eval:bool=False):
        '''
        Adds a quantify of cash in the portfolio
        currency: The currency of the cash
        quantity: The amount of cash
        date: The date of the transaction. Pass None and it will default to the start date of the portfolio for convenience
        tags: tags associated with the cash position.
        if eval is true will return the evaluated price in the transaction's currency, otherwise returns 0
        '''
        check_currency(currency)
        to_return =0
        if date == None: date=self.get_start_date()
        else: date = todatetime(date)
        to_return = self._buy(PositionIdentifier(CASH, Currency(currency), tags), quantity, date, eval)
        logger.debug(f"Bought {quantity} {currency} at {date}")
        return to_return

    def buy(self, ticker_code:str, quantity:number, date:datetime=None, tags:set=None, eval:bool=False)->number:
        '''
        Adds an instrument in the portfolio.
        Ticker code can be relative (without an exchange, which will then default to the US virtual exchange) or absolute (fully qualified)
        quantify if the amount of equity to buy, typically a number of shares
        date is the transaction date. Pass None to set it at the start of the porfolio
        tags are the tags associated with the transaction. Used for filtering or other portfolio manipulation.
        if eval is true will return the evaluated price in the transaction's currency, otherwise returns 0
        '''  
        if(ticker_code.find(".") != -1):
            (ticker,exchange) = ticker_code.split('.')
            full_ticker = ticker+"."+exchange
        else:
            full_ticker = ticker_code+"." + DEFAULT_MARKET_CODE
        # Get meta data for the ticker
        try:
            to_return = 0
            ticker = get_ticker(full_ticker)
            if(date == None): date = self.get_start_date()
            else: date = todatetime(date)
            to_return = self._buy(PositionIdentifier(EQUITY, ticker, tags), quantity, date, eval)
            logger.debug(f"Bought {quantity} {ticker_code} at {date}")
            return to_return
        except Exception as e:
            raise PMException(f"Cannot find or process the instrument identified by ticker code {ticker_code} - {str(e)}")
        
    def create(self, name:str, date:datetime=DEFAULT_ORIGIN, tags:set=None):
        '''
        Ceated a new portfolio from the positions of this portfolio using the tags given.
        The returning portfolio will contained the corresponding tagged positions.
        Tags are evaluated using OR statement: A position is returned if it contains one of the given tags.
        '''
        if(date < self.get_start_date()): date = self.get_start_date()
        positions:Positions = self.get_positions(date).get_tagged_positions(tags)
        toreturn= Portfolio(name, date)
        # Re-create the portfolio with buy transactions
        for position in positions:
            toreturn._add_position(position, self.get_position_amount(position, date), date)
        return toreturn

    def _add_position(self, position:PositionIdentifier, amount:number, date:datetime):
        self._buy(position, amount ,date, False)

    def _process_transaction(self, transaction:Transaction, eval:bool=False)->number:
        '''
        Process a transaction (recomputes the composition of the portfolio) and if eval is true evaluate the value of the transaction in its local currency
        Returns 0 if eval is false
        '''
        to_return =0
        # get the portfolio positions for the given date
        date:datetime = transaction.get_date()
        positions = self.get_positions(date)
        # Copy the positions and save the new portfolio at date
        new_positions = positions.copy()
        new_positions.apply_transaction(transaction)
        if eval : to_return = self.value_position(transaction.get_position_identifier(), date, transaction.get_quantity(), transaction.get_position_identifier().id.get_currency().get_identifier())
        # Record the transaction
        txs:list = self._get_transactions(date)
        txs.append(transaction)
        self.positions[date]= {"positions":new_positions, "transactions":txs}
        # Invalidate the portfolio constituents from date
        self._invalidate_constituents_evaluation(date+timedelta(days=1))
        return to_return

    def get_earliest_valuation(self, pi:PositionIdentifier)->date|None:
        '''
        Return the ealiest date at which we can value the position (regardless of whether it was in the portfolio at that date or not)
        '''
        if pi.type == CASH and pi.id.get_identifier() != "USD":
            return get_fx_timeseries(pi.id.get_identifier()).get_start_date()
        if pi.type == EQUITY:
            return get_timeseries(pi.id.get_full_ticker()).get_start_date()
        return None

    def value_position(self, pi:PositionIdentifier, date:datetime, quantity:number = None, target_currency:str=None)->number:
        '''
        Value the position. If quantity is None, then it is taken from the portfolio
        '''
        if(quantity == None): quantity = self.get_position_amount(pi, date)
        if target_currency == None: raise PMException("You must specify the target currency when you value a position")
        if pi.type == CASH:
            return CashValuator.value_position(pi, quantity, date, Currency(target_currency))
        if pi.type == EQUITY:
            return EquityValuator.value_position(pi, quantity, date, DEFAULT_VALUATION_DATAPOINT, Currency(target_currency))
        raise NotImplementedError(f"position type {pi.type} not implemented for position valuation.")


    def _buy(self, ticker:PositionIdentifier, quantity:number, date:datetime, eval:bool)->number:
        
        # Tagged positions are not aggregared with non-tagged positions. They are aggregated together 
        # if they have the same tickers and tags
        transaction = Transaction(BUY, ticker, quantity, date)
        return self._process_transaction(transaction, eval)

    def _get_transactions(self, date:datetime):
        if date in self.positions:
            return self.positions[date]['transactions']
        return []

    def sell(self, ticker_code:str, quantity:number, date:datetime=None, eval:bool=False):
        '''
        Sells an equity from the portfolio
        Ticker code can be relative (without an exchange, which will then default to the US virtual exchange) or absolute (fully qualified)
        quantify if the amount of equity to buy, typically a number of shares
        date is the transaction date. Pass None to set it at the start of the porfolio
        if eval is true will return the evaluated price in the transaction's currency, otherwise returns 0
        '''
        if(date == None): date = self.get_start_date()
        else: date = todatetime(date)
        if(ticker_code.find(".") != -1):
            (ticker,exchange) = ticker_code.split('.')
            full_ticker = ticker+"."+exchange
        else:
            full_ticker = ticker_code+"." + DEFAULT_MARKET_CODE
        # Get meta data for the ticker
        try:
            to_return = 0
            ticker = get_ticker(full_ticker)
            to_return = self._sell(PositionIdentifier(EQUITY, ticker), quantity, date, eval)
            logger.debug(f"Sold {quantity} {full_ticker} at {date}")
            return to_return
        except Exception:
            raise PMException("Cannot find or process the instrument identified by ticker code " + ticker_code)


    def withdraw(self, currency:str, quantity:number, date:datetime=None, eval:bool=False):
        '''
        Withdraws some cash from the portfolio
        '''
        check_currency(currency)
        to_return =0
        if date == None: date = self.get_start_date()
        else: date = todatetime(date)
        to_return = self._sell(PositionIdentifier(CASH, Currency(currency)), quantity, date, eval)
        logger.debug(f"Sold {quantity} {currency} at {date}")
        return to_return
     
    def _sell(self, ticker:PositionIdentifier, quantity:number, date:datetime, eval:bool=False):
        transaction = Transaction(SELL, ticker, quantity,date)
        return self._process_transaction(transaction, eval)

    def get_position_amount(self, pi:PositionIdentifier, date:datetime=None)->number:
        '''
        Returns the number of shares of an equity positions, or the quantify of cash of a cash position.
        '''
        if date == None: date = self.get_start_date()
        else: date = todatetime(date)
        positions = self.get_positions(date)
        return positions[pi]

    def get_cash(self, currency:str, date:datetime=None, tags:set=None)->number:
        '''
        Returns the amount of cash of the given currency.
        '''
        check_currency(currency)
        if date == None: date = self.get_start_date()
        return self.get_position_amount(PositionIdentifier(CASH,Currency(currency), tags), date)

    def valuator(self):
        '''
        Returns the valuator object able to value the portfolio
        '''
        return PortfolioValuator(self)

    def get_shares(self, ticker:str, exchange:str="US", date:datetime=None, tags:set=None)->number:
        '''
        Returns the amount of shares of a given equity position
        '''
        if date == None: date = self.get_start_date()
        return self.get_positions(date)[PositionIdentifier(EQUITY, Ticker(ticker, exchange), tags)]

    def pretty_print(self) -> str:
        '''
        Returns a readable string of the portfolio
        '''
        return "Portfolio " + self.name +" \n" + self.get_positions().pretty_print()

    def size(self):
        '''
        Returns the number of positions of the portfolio
        '''
        return len(self.positions)

class PortfolioGroup:
    def __init__(self, name:str="DEFAULT") -> None:
        self.__name = name
        self.__portfolios = {}

    def get_name(self):
        return self.__name

    def add(self, p:Portfolio):
        if p.get_name() in self.__portfolios:
            raise PMException(f"Portfolio {p.get_name()} exists in the portfolio group {self.__name}. It cannot be added twice. Please remove or rename it")
        self.__portfolios[p.get_name()] = p

    def __len__(self):
        '''
        Returns the number of groups, not the number of portfolios
        '''
        return len(self.__portfolios.keys())
    
    def state(self):
        return {'name':self.__name, 'portfolios':self._marshall_portfolios()}

    def _marshall_portfolios(self)->list:
        to_return=[]
        for name, porfolio in self.__portfolios.items():
            to_return.append({"portfolio_name":name, "portfolio":porfolio.state()})
        return to_return

    def get(self, name:str)->Portfolio:
        return self.__portfolios(name)

    def __iter__(self):
        # Flatten all portfolio in a single list and return an iterator on this list
        portfolio_list = self.flatten()
        return portfolio_list.__iter__()

    def flatten(self)->list:
        '''
        Returns a flattened list of portfolios
        '''
        toreturn = list()
        for portfolio_name in self.__portfolios.keys():
            portfolio = self.__portfolios[portfolio_name]
            toreturn.append(portfolio)
        return toreturn

    def __repr__(self) -> str:
        toreturn = "Portfolio Group " + self.__name +" containing " + str(self.__len__())+" portfolios: \n"
        for portfolio_name in self.__portfolios.keys():
            p:Portfolio = self.__portfolios[portfolio_name]
            toreturn += p.pretty_print()
        return toreturn
    
    def valuator(self):
        return PortfolioGroupValuator(self)

class InstrumentValuator:
    def __init__(self, portfolio:Portfolio, pi:PositionIdentifier) -> None:
        self.portfolio = portfolio
        self.pi = pi

    @abc.abstractmethod
    def get_valuation(self, valdate:datetime, target_currency:Currency)->number:
        raise NotImplementedError("get_valuation should have an implementation in derived classes")

    @staticmethod
    def convert_to_target_currency(value:number, valdate:date, source_currency:str=DEFAULT_CURRENCY, target_currency:str=DEFAULT_CURRENCY)->number:
        return fx_convert(value, source_currency, target_currency, valdate)

    @staticmethod
    def valuator(portfolio:Portfolio, pi:PositionIdentifier, **valuator_args):
        '''
        Returns the correct valuator for the right time of financial instrument.
        Note that for an EquityValuator, you can pass an extra dpname parameter which will indicate which data point to value.
        By default it is DEFAULT_VALUATION_DATAPOINT
        '''
        if(pi.type == CASH):
            return CashValuator(portfolio, pi)
        if(pi.type == EQUITY):
            return EquityValuator(portfolio, pi, **valuator_args)
        raise PMException("Could not create valuator for " + pi.pretty_print())
    
class EquityValuator(InstrumentValuator):
    def __init__(self, portfolio:Portfolio, pi:PositionIdentifier, dpname=DEFAULT_VALUATION_DATAPOINT) -> None:
        InstrumentValuator.__init__(self, portfolio, pi)
        self.valuation_data_point = dpname

    def get_valuation(self, valdate:datetime, target_currency:Currency)->number:
        return self.value_position(self.pi, self.portfolio.get_position_amount(self.pi, valdate), valdate, self.valuation_data_point, target_currency)
        
    @staticmethod
    def value_position(pi:PositionIdentifier, position_amount:number, valdate:datetime, valuation_data_point:str, target_currency:Currency)->number:
        try:
            valdate = todatetime(valdate)
            closing_price = get_timeseries(full_ticker=pi.id.get_full_ticker(), datapoint_name=valuation_data_point).get(valdate.date())
            return InstrumentValuator.convert_to_target_currency(closing_price*position_amount, valdate.date(), pi.id.currency.get_identifier(), target_currency.get_identifier())
        except PMException as e:
            raise PMException(f"Cannot get the valuation of {pi.id.get_full_ticker()} at date {valdate} for data point {valuation_data_point} in currency {target_currency.get_identifier()} due to the underlying error: {str(e)}")

class CashValuator(InstrumentValuator):
    def __init__(self, portfolio:Portfolio, pi:PositionIdentifier) -> None:
        InstrumentValuator.__init__(self, portfolio,pi)

    def get_valuation(self, valdate:datetime, target_currency:Currency)->number:
        return self.value_position(self.pi, self.portfolio.get_position_amount(self.pi, valdate), valdate, target_currency)

    @staticmethod
    def value_position(pi:PositionIdentifier, position_amount:number, valdate:datetime, target_currency:Currency)->number:
        valdate = todatetime(valdate)
        return InstrumentValuator.convert_to_target_currency(position_amount, valdate.date(), pi.id.get_identifier(), target_currency.get_identifier())

class IPorfolioValuator:
  
    @abc.abstractmethod
    def get_valuations(self, start_date:datetime=None, end_date:datetime=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
        raise NotImplementedError("get_valuations should have an implementation in derived classes")

    @abc.abstractmethod
    def get_valuation(self, valdate:datetime=None, dpname:str = DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->number:
        raise NotImplementedError("get_valuation should have an implementation in derived classes")

class PortfolioGroupValuator(IPorfolioValuator):
    def __init__(self, portfolio_group:PortfolioGroup) -> None:
        self.portfolio_group = portfolio_group

    def get_valuations(self, start_date:datetime=None, end_date:datetime=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
        start_date=todatetime(start_date)
        end_date=todatetime(end_date)
        #For each portfolio in the group, value it
        ts:TimeSeries|None = None
        for (i,portfolio) in enumerate(self.portfolio_group):
            pv = PortfolioValuator(portfolio)
            if(i==0):
                ts = pv.get_valuations(start_date, end_date, dp_name,ccy)
            else:
                ts += pv.get_valuations(start_date, end_date, dp_name,ccy)
        return ts

    def get_valuation(self, valdate:datetime=None, dpname:str = DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->number:
        toreturn =0
        for (i,portfolio) in enumerate(self.portfolio_group):
            pv = PortfolioValuator(portfolio)
            if(i==0):
                toreturn = pv.get_valuation(valdate, dpname,ccy)
            else:
                toreturn += pv.get_valuation(valdate, dpname,ccy)
        return toreturn

class PortfolioValuator(IPorfolioValuator):
    '''
    PortfolioValuator is a key class in the pricing infrastructure. It is used to value a portfolio for any point in time.
    It supports multiple instrument types. Each instrument time is valuated using the InstrumentValuator subclass corresponding to the instrument.
    get_valuations iterate over a range of dates
    get_valuation values the portfolio for a single date
    '''
    def __init__(self, portfolio:Portfolio) -> None:
        self.portfolio = portfolio

    def get_valuations(self, start_date:datetime=None, end_date:datetime=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
        '''
        Values the portfolio and returns a time series of valuations.
        Parameters are:
        start_date: Inclusive start date of the valuation period. If None, the portfolio will be valued from the earliest possible valuation date, which is the date from which we have prices for all positions of the portfolio.
        end_date: Inclusive end date of the valuation period. If None, the portfolio will be valued up to the latest possible valuation date, which is the date to which we have prices for all positions of the portfolio.
        dp_name: Is the data point name used to value the portfolio. Can be closing price, adjusted closing price etc... It allows for multiple variation variants.
        ccy: currency in which the portfolio will be valued.
        '''
        if(start_date == None):
            start_date = self.get_start_date(dp_name=dp_name)
        if(end_date == None):
            end_date = self.get_end_date(dp_name=dp_name)
        start_date=todatetime(start_date)
        end_date = todatetime(end_date)
        period:pd.DatetimeIndex = pd.date_range(start_date, end_date, freq='D')
        toreturn:ndarray = numpy.zeros((end_date - start_date).days+1)
        for i, d in enumerate(period):
            toreturn[i]=self.get_valuation(start_date+timedelta(days=i), dpname=dp_name, ccy=ccy)
        return TimeSeries(toreturn, start_date=start_date.date(), end_date=end_date.date())

    def get_valuation(self, valdate:datetime=None, dpname:str = DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->number:
        valdate=todatetime(valdate)
        portfolio_valuation:number = 0.0
        positions = self.portfolio.get_positions(valdate)
        if(logger.isEnabledFor(DEBUG)): logger.debug(f"Valuing portfolio {self.portfolio.get_name()} containing {len(positions)} positions at {valdate}")
        for position_identifier in positions:
            try:
                instrument_value:number = InstrumentValuator.valuator(self.portfolio, position_identifier, dpname=dpname).get_valuation(valdate, Currency(ccy))
                portfolio_valuation = portfolio_valuation + instrument_value
                if(logger.isEnabledFor(DEBUG)): logger.debug(f"{position_identifier.pretty_print()} valued at {instrument_value} {ccy}")
            except Exception as e:
                raise PMException(f"Could not value position {position_identifier.pretty_print()} in portfolio {self.portfolio.get_name()} at {valdate} in {ccy} due to the underlying error: {str(e)}")
        if(logger.isEnabledFor(DEBUG)): logger.debug(f"Portfolio {self.portfolio.get_name()} evaluated at {portfolio_valuation} {ccy} at {valdate}")
        return portfolio_valuation

    def get_start_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT)->datetime:
        '''
        Returns the earliest date for which we can value the portfolio. This is the date for which all
        constituents have pricing data.
        '''
        # Check the earliest start date of all instruments
        start_date:datetime|None = None
        portfolio_start_date = self.portfolio.get_start_date()
        for position_identifier in self.portfolio.get_positions(portfolio_start_date):
            if(position_identifier.type == CASH): 
                # Skip UDS
                if position_identifier.id.get_identifier() == "USD": continue
                ts = get_fx_timeseries(position_identifier.id.get_identifier())
            if(position_identifier.type == EQUITY):
                ts = get_timeseries(full_ticker=position_identifier.id.get_full_ticker(), datapoint_name=dp_name)
            sd = ts.get_start_date()
            sdt = datetime(sd.year, sd.month, sd.day)
            if((start_date == None) or (start_date < sdt)):
                start_date = sdt
        if(start_date == None): return portfolio_start_date.date()
        # Return the latest between the portfolio start date and the data start dat
        return max(start_date, portfolio_start_date)


    def get_end_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT)->datetime:
        '''
        Returns the latest date for which the portfolio has pricing data for at least one of its constituents.
        '''
        end_date:date|None = None
        d:date = date.today()
        for position_identifier in self.portfolio.get_positions(datetime(d.year, d.month, d.day)):
            # Ignore cash positions to compute earliest start date of the portfolio
            if(position_identifier.type == CASH): 
                # Skip UDS
                if position_identifier.id.get_identifier() == "USD": continue
                ts = get_fx_timeseries(position_identifier.id.get_identifier())
            if(position_identifier.type == EQUITY):
                ts = get_timeseries(full_ticker=position_identifier.id.get_full_ticker(), datapoint_name=dp_name)
            ed = ts.get_end_date()
            if((end_date == None) or (end_date > ed)):
                end_date = ed
            if(end_date == None):
                raise PMException("Could not determine the latest end date of the portfolio. Please specify the end date explicitly.")
        return datetime(end_date.year, end_date.month, end_date.day)

class IndexValuator(PortfolioValuator):
    def __init__(self, portfolio:Portfolio, base_date:date, base_value:number) -> None:
        super().__init__(portfolio=portfolio)
        self.base_date = base_date
        self.base_value = base_value

    def get_index_valuations(self, end_date:date=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
        if(end_date == None):
            end_date = self.get_end_date(dp_name=dp_name)
        
        period:pd.DatetimeIndex = pd.date_range(self.base_date, end_date, freq='D')
        toreturn:ndarray = numpy.zeros((end_date - self.base_date).days+1)
        toreturn[0]=self.base_value
        for i, d in enumerate(period):
            if(i==0): continue #Skip the first date since it is valued as base_value
            toreturn[i]=toreturn[i-1] * self.get_valuation(todatetime(self.base_date+timedelta(days=i)), dpname=dp_name, ccy=ccy) / self.get_valuation(todatetime(self.base_date+timedelta(days=i-1)), dpname=dp_name, ccy=ccy)
        return TimeSeries(toreturn, start_date=self.base_date, end_date=end_date)

class UnitTestPortfolio(unittest.TestCase):
    def test_buy(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        p.buy('MSFT', 30)
        self.assertEqual(p.get_shares('MSFT'), 40)
        self.assertEqual(p.get_shares('CSCO'), 20)

    def test_cryptos(self):
        p:Portfolio = Portfolio()
        p.add('ETH', 10)
        self.assertEqual(p.get_cash('ETH'), 10)

    def test_positions(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        p.buy('MSFT', 30)
        self.assertEqual(len(p.get_positions()),2)

    def test_sell_short(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 40)
        p.buy('CSCO', 20)
        p.sell('MSFT', 40)
        self.assertEqual(p.get_shares('MSFT'), 0)
        try:
            p.sell('MSFT', 1)
            self.assertFalse(True) # Fail the test since exception should have been raised
        except PMException:
            self.assertTrue(True)

    def test_cash(self):
        p:Portfolio = Portfolio()
        p.add("USD", 10000)
        p.add("CHF", 50000)
        p.withdraw("USD", 4000)
        p.buy('MSFT', 40)
        self.assertEqual(p.get_cash('USD'), 6000)
        self.assertEqual(p.get_cash('CHF'), 50000)
        p.withdraw("USD", 1000)
        self.assertEqual(p.get_cash('USD'), 5000)
        self.assertEqual(p.get_cash('CHF'), 50000)
        p.withdraw("CHF", 20000)
        self.assertEqual(p.get_cash('USD'), 5000)
        self.assertEqual(p.get_cash('CHF'), 30000)
        self.assertEqual(p.get_shares('MSFT'), 40)
        p.add('USD', 2000)
        self.assertEqual(p.get_cash('USD'), 7000)

    def test_multiple_currencies(self):
        p:Portfolio = Portfolio()
        p.add("USD", 10000)
        p.add("CHF", 50000)
        # The exchange rate on November 8 is 0.9889 (USDCHF= <-> CHF= 0.9889 = 1 USD is 0.9889 CHF)
        self.assertAlmostEqual((PortfolioValuator(portfolio=p).get_valuation(datetime(2022,11,8))), 60561, delta=1)


    def test_cash_short(self):
        p:Portfolio = Portfolio()
        p.add("USD", 10000)
        try:
            p.withdraw("USD", 10000) #Should be fine
        except PMException:
            #Should not be raised
            self.assertTrue(False)
        try:
            p.withdraw("USD", 1) #Not enough money
            self.assertTrue(False) #Should never be reached
        except PMException:
            self.assertTrue(True)

        
    def test_sell_what_you_do_not_have(self):
        p:Portfolio = Portfolio()
        try:
            p.sell('MSFT', 40)
            self.assertFalse(True) # Fail the test since exception should have been raised
        except PMException:
            self.assertTrue(True)

    def test_portfolio_group1(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('MSFT', 20)
        pg:PortfolioGroup = PortfolioGroup("My Investments1")
        p2:Portfolio = Portfolio("My cash")
        p2.add('USD', 67000)
        p2.add('CHF', 480000)
        pg.add(p)
        pg.add(p2)
        self.assertTrue(len(pg), 2)
        p3:Portfolio = Portfolio("My cash 2")
        p3.add('EUR', 25000)
        pg.add(p3)
        self.assertTrue(len(pg), 3)

    def test_portfolio_group2(self):
        p:Portfolio = Portfolio("My equities")
        p.buy('MSFT', 10)
        p.buy('MSFT', 20)
        pg:PortfolioGroup = PortfolioGroup("My Investments2")
        p2:Portfolio = Portfolio("My cash outside France")
        p2.add('USD', 67000)
        p2.add('CHF', 480000)
        pg.add(p)
        pg.add(p2)
        self.assertTrue(len(pg), 2)
        p3:Portfolio = Portfolio("Cash in Europe")
        p3.add('EUR', 25000)
        pg.add(p3)
        self.assertTrue(len(pg), 3)


    def test_portfolio_tags(self):
        p:Portfolio = Portfolio("My equities")
        p.buy('MSFT', 10, tags={"INITIAL"})
        p.buy('MSFT', 20, tags={"BONUS"})
        p.add('USD', 67000, tags={"BONUS"})
        p.add('USD', 74000, tags={"BONUS", "YEAR2"})
        p.add('CHF', 480000, tags={"YEAR2"})
        p.add('EUR', 25000, tags={"ASSURANCE VIE", "BONUS", "YEAR2"})
        self.assertEqual(p.get_shares('MSFT', tags={"INITIAL"}), 10)
        self.assertEqual(p.get_shares('MSFT', tags={"BONUS"}), 20)
        self.assertEqual(p.get_shares('MSFT', tags={"BONUS"}), 20)  
        self.assertEqual(p.get_cash('USD', tags={'BONUS'}), 67000)
        self.assertEqual(p.get_cash('USD', tags={'BONUS', "YEAR2"}), 74000)
        #Check selling/withdrawing

class UnitTestValuations(unittest.TestCase):

    def create_sample_portfolio(self, name:str, portfolio_start_date:datetime = None, transaction_date:datetime= None):
        if(portfolio_start_date == None): portfolio_start_date = DEFAULT_ORIGIN
        my_portfolio:Portfolio = Portfolio(name, portfolio_start_date)
        my_portfolio.buy('MSCI', 2578, transaction_date, tags={'PERFORMANCE SHARES'}) #Performance shares
        my_portfolio.buy('MSCI', 3916, transaction_date, tags={'RESTRICTED SHARES'}) #Restricted shares
        my_portfolio.buy('MSCI', 3916, transaction_date, tags={'STOCK OPTIONS'}) #Stock options
        my_portfolio.buy('MSCI', 807, transaction_date, tags={'BROADRIDGE SHARES'})  #Bradridge shares
        my_portfolio.buy('MSCI', 3000, transaction_date, tags={'MORGAN STANLEY SHARES'})  #Bradridge shares
        my_portfolio.add('CHF', 14845, transaction_date)  # BCGE
        my_portfolio.add('EUR', 5604, transaction_date)   # N26
        my_portfolio.add('EUR', 1169,transaction_date)   # Boursorama
        my_portfolio.add('CHF', 401598, transaction_date) # UBS
        my_portfolio.add('CHF', 37640, transaction_date)  # Liechsteinstein
        my_portfolio.add('ETH', 32.9123, transaction_date, tags={'CRYPTOS'})
        my_portfolio.add('BTC', 2.2347, transaction_date, tags={'CRYPTOS'})
        my_portfolio.add('DOT', 1214.4988, transaction_date,tags={'CRYPTOS'})
        my_portfolio.add('EUR', 1462.32, transaction_date,tags={'SWISSQUOTE'})
        my_portfolio.add('USD', 165928.14, transaction_date,tags={'SWISSQUOTE'})
        my_portfolio.buy('IPRP.SW', 235, transaction_date,tags={'SWISSQUOTE'})
        my_portfolio.buy('VUSA.SW', 800, transaction_date,tags={'SWISSQUOTE'})
        my_portfolio.buy('WSRUSA.SW', 489, transaction_date,tags={'SWISSQUOTE'})
        my_portfolio.buy('EFA', 428, transaction_date,tags={'SWISSQUOTE'})
        my_portfolio.buy('LCTU', 428, datetime(2021,4,8),tags={'SWISSQUOTE'})
        my_portfolio.buy('STLA.PA', 2923, datetime(2021,1,18),tags={'SWISSQUOTE'})
        return my_portfolio

    def test_mac_portfolio(self):
        my_portfolio:Portfolio = Portfolio()
        my_portfolio.buy('MSCI', 2578, tags={'PERFORMANCE SHARES'}) #Performance shares
        my_portfolio.buy('MSCI', 3916, tags={'RESTRICTED SHARES'}) #Restricted shares
        my_portfolio.buy('MSCI', 3916, tags={'STOCK OPTIONS'}) #Stock options
        my_portfolio.buy('MSCI', 807, tags={'BROADRIDGE SHARES'})  #Bradridge shares
        my_portfolio.buy('MSCI', 3000, tags={'MORGAN STANLEY SHARES'})  #Bradridge shares
        my_portfolio.add('CHF', 14845)  # BCGE
        my_portfolio.add('EUR', 5604)   # N26
        my_portfolio.add('EUR', 1169)   # Boursorama
        my_portfolio.add('CHF', 401598) # UBS
        my_portfolio.add('CHF', 37640)  # Liechsteinstein
        with_cash = PortfolioValuator(portfolio=my_portfolio).get_valuation(datetime(2022,9,1))
        my_portfolio.add('ETH', 32.9123, tags={'CRYPTOS'})
        my_portfolio.add('BTC', 2.2347, tags={'CRYPTOS'})
        my_portfolio.add('DOT', 1214.4988, tags={'CRYPTOS'})
        with_cryptos = PortfolioValuator(portfolio=my_portfolio).get_valuation(datetime(2022,9,1))
        self.assertAlmostEqual(with_cryptos - with_cash, 105911, delta=1)

        my_portfolio.add('EUR', 1462.32, tags={'SWISSQUOTE'})
        my_portfolio.add('USD', 165928.14, tags={'SWISSQUOTE'})
        my_portfolio.buy('IPRP.SW', 235, tags={'SWISSQUOTE'})
        my_portfolio.buy('VUSA.SW', 800, tags={'SWISSQUOTE'})
        my_portfolio.buy('WSRUSA.SW', 489, tags={'SWISSQUOTE'})
        my_portfolio.buy('EFA', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('LCTU', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('STLA.PA', 2923, tags={'SWISSQUOTE'})

        with_swissquote = PortfolioValuator(portfolio=my_portfolio).get_valuation(datetime(2022,9,1))
        swissquote = my_portfolio.create("swissquote", tags={'SWISSQUOTE'})
        self.assertEqual(len(swissquote.get_positions()), 8)
        sqvalue = PortfolioValuator(portfolio=swissquote).get_valuation(datetime(2022,9,1))
        self.assertAlmostEqual(with_swissquote - with_cryptos, sqvalue, delta=1)

#    @time_func
    def test_get_valuations(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_valuations(datetime(2020,1,1), datetime(2020,12,31)).size(), (date(2020,12,31) - date(2020,1,1)).days+1)

#    @time_func
    def test_get_start_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_start_date(), datetime.strptime('2000-01-01', '%Y-%m-%d'))

    
    def test_msci_valuation(self):
        p:Portfolio = Portfolio()
        p.buy('MSCI', 10)
        self.assertEqual(PortfolioValuator(p).get_valuations().get(date(2022,9,1)),get_timeseries("MSCI.US", "adjusted_close").get(date(2022,9,1))*10)
        # This valuation should not change unless the historical time series is restated.
        self.assertAlmostEqual(PortfolioValuator(p).get_valuations().get(date(2022,9,1)),4556.9, delta=0.1) 

    def test_portfolio(self):
        my_portfolio:Portfolio = Portfolio()
        my_portfolio.buy('MSCI', 2578) #Performance shares
        my_portfolio.buy('MSCI', 3916) #Restricted shares
        my_portfolio.buy('MSCI', 3916) #Stock options
        my_portfolio.buy('MSCI', 807)  #Bradridge shares
        my_portfolio.add('USD', 1000000)
        PortfolioValuator(portfolio=my_portfolio).get_valuations().get(date(2022,9,1))


    def test_portfolio_group(self):
        p:Portfolio = Portfolio("First investment")
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        pg = PortfolioGroup()
        pg.add(p)
        self.assertAlmostEqual((pg.valuator().get_valuation(datetime(2022,9,1))), 3495, delta=1)
        p2:Portfolio = Portfolio("Second investment")
        p.buy('MSCI', 50)
        pg.add(p2)
        self.assertAlmostEqual((pg.valuator().get_valuation(datetime(2022,9,1))), 26278, delta = 1)

    def test_portfolio_group2(self):
        pg:PortfolioGroup = PortfolioGroup("My Investments")
        p:Portfolio = Portfolio("My cash")
        p.add('USD', 67000)
        p.add('CHF', 480000)
        pg.add(p)
        self.assertAlmostEqual(pg.valuator().get_valuation(datetime(2022,9,1)),557246, delta=1)
        p2:Portfolio = Portfolio()
        p2.buy('MSFT', 10)
        p2.buy('MSFT', 20)
        pg.add(p2)
        self.assertAlmostEqual(pg.valuator().get_valuation(datetime(2022,9,1)), 565036, delta=1)

    def test_portfolio_transaction_evaluation(self):
        p:Portfolio = Portfolio()
        v1 = p.add('USD', 67000, datetime(2020,1,10), eval=True)
        v2 = p.buy('MSFT', 10, datetime(2020,1,15), eval=True)
        self.assertEqual(v1, 67000)
        self.assertAlmostEqual(v2, 1586, delta=1)

 #   @time_func
    def test_get_end_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertGreaterEqual(v.get_end_date(), datetime.strptime('2022-09-22', '%Y-%m-%d'))

 #   @time_func
    def test_dp(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 1)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        ts:TimeSeries = v.get_valuations(start_date=None, end_date=None, dp_name='close')
        tsa:TimeSeries = v.get_valuations(start_date=None, end_date=None, dp_name='adjusted_close')
        self.assertEqual(ts.size(), tsa.size())
        self.assertLessEqual(tsa.get_full_time_series()[0], ts.get_full_time_series()[0])

 #   @time_func
    def test_cash(self):
        p:Portfolio = Portfolio()
        p.buy('MSCI', 1)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        value:number = v.get_valuation(datetime(2022,9,1))
        self.assertAlmostEqual(value, 455.69, delta=0.2)
        p.add('USD', 2000000)
        new_value:number = v.get_valuation(datetime(2022,9,1))
        self.assertEqual(new_value-value, 2000000)

 #   @time_func
    def test_index_valuation(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        p.buy('MSCI', 30)
        v:IndexValuator = IndexValuator(portfolio=p, base_date=date.fromisoformat("2010-01-01"), base_value=100)
        ts:ndarray = v.get_index_valuations(end_date=date.fromisoformat("2021-12-31")).get_full_time_series()
        self.assertAlmostEqual(ts[len(ts)-1], 1576, delta=0.2)

    def test_currency_conversion(self):
        p:Portfolio = Portfolio()
        p.buy('MSCI', 10)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        value:number = v.get_valuation(valdate=datetime(2022,9,1))
        self.assertAlmostEqual(value, 4556.89, delta=1)
        value_chf:number = v.get_valuation(valdate=datetime(2022,9,1), ccy="CHF")
        self.assertAlmostEqual(value_chf, 4461, delta=1)


    def test_tag_selection(self):
        my_portfolio:Portfolio = Portfolio("DEFAULT", datetime(2021,1,18))
        my_portfolio.buy('MSCI', 2578, tags={'PERFORMANCE SHARES'}) #Performance shares
        my_portfolio.buy('MSCI', 3916, tags={'RESTRICTED SHARES'}) #Restricted shares
        my_portfolio.buy('MSCI', 1110, tags={'STOCK OPTIONS'}) #Stock options
        my_portfolio.buy('MSCI', 807, tags={'BROADRIDGE SHARES'})  #Bradridge shares
        my_portfolio.buy('MSCI', 3000, tags={'MORGAN STANLEY SHARES'})  #Bradridge shares
        v:PortfolioValuator = PortfolioValuator(portfolio=my_portfolio)
        # Value the MSCI stocks
        v.get_valuation(date.fromisoformat("2022-11-27"))
        #Add cash
        my_portfolio.add('CHF', 14845)  # BCGE
        my_portfolio.add('EUR', 2000)   # N26
        my_portfolio.add('EUR', 1169)   # Boursorama
        my_portfolio.add('CHF', 387798) # UBS
        my_portfolio.add('CHF', 42233)  # Liechsteinstein
        PortfolioValuator(portfolio=my_portfolio).get_valuation(date.fromisoformat("2022-11-27"))
        # Add crypto currencies
        my_portfolio.add('ETH', 32.9123, tags={'CRYPTOS'})
        my_portfolio.add('BTC', 2.2347, tags={'CRYPTOS'})
        my_portfolio.add('DOT', 1214.4988, tags={'CRYPTOS'})
        with_cryptos = PortfolioValuator(portfolio=my_portfolio).get_valuation(date.fromisoformat("2022-11-27"))
        self.assertGreater(with_cryptos, 0)
        # Explicitly value the crypto positions
        crypto_portfolio = my_portfolio.create(name="CRYPTOS", tags={'CRYPTOS'})
        cryptos_only = PortfolioValuator(portfolio=crypto_portfolio).get_valuation(date.fromisoformat("2022-11-27"))
        self.assertGreater(cryptos_only, 0)
        my_portfolio.add('CHF', 50000) # DEBTORS
        PortfolioValuator(portfolio=my_portfolio).get_valuation(date.fromisoformat("2022-11-27"))
        my_portfolio.add('EUR', 1462.32, tags={'SWISSQUOTE'})
        my_portfolio.add('USD', 165928.14, tags={'SWISSQUOTE'})
        my_portfolio.buy('IPRP.SW', 235, tags={'SWISSQUOTE'})
        my_portfolio.buy('VUSA.SW', 800, tags={'SWISSQUOTE'})
        my_portfolio.buy('WSRUSA.SW', 489, tags={'SWISSQUOTE'})
        my_portfolio.buy('EFA', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('LCTU', 428, datetime(2021,4,8), tags={'SWISSQUOTE'})
        my_portfolio.buy('BCHN.LSE', 460, tags={'SWISSQUOTE'})
        my_portfolio.buy('STLA.PA', 2923, datetime(2021,1,18), tags={'SWISSQUOTE'})
        my_portfolio.buy('C40.PA', 320, tags={'SWISSQUOTE'})
        with_swissquote = PortfolioValuator(portfolio=my_portfolio).get_valuation(date.fromisoformat("2022-11-27"))
        return my_portfolio

    def test_dated_buy(self):
        # valuation_date:datetime = datetime(2022,9,1)
        p = self.create_sample_portfolio("Sample portfolio")
        value = PortfolioValuator(p).get_valuation(datetime(2022,9,1))
        # Add a dated transaction
        # Check that the valuation of the portfolio before the transaction is not affected
        # Check that the new transaction is reflected in the valuation change on and after the transaction date
        self.assertAlmostEqual(value, 7428002, delta=1)
        p.buy("STLA.PA", 100, datetime(2022,9,2))
        value2 = PortfolioValuator(p).get_valuation(datetime(2022,9,2))
        self.assertAlmostEqual(value2, 7359644, delta =1 )
        value3 = PortfolioValuator(p).get_valuation(datetime(2022,9,1))
        self.assertEqual(value, value3)
        # Do the same type of checks with cash positions
        p.add("EUR", 10000, datetime(2022,9,3))
        value4 = PortfolioValuator(p).get_valuation(datetime(2022,9,3))
        self.assertGreater(value4, value2)
        value5 = PortfolioValuator(p).get_valuation(datetime(2022,9,2))
        self.assertEqual(value2, value5)

    def test_dated_buy2(self):
        p:Portfolio = Portfolio("test", datetime(2022,9,1))
        p.add("USD", 100, datetime(2022,9,1))
        p.add("USD", 150, datetime(2022,9,2))
        p.add("USD", 200, datetime(2022,9,5))
        p.withdraw("USD", 250, datetime(2022,9,10))
        v1=p.valuator().get_valuation(datetime(2022,9,1))
        self.assertEqual(v1, 100)
        v2=p.valuator().get_valuation(datetime(2022,9,2))
        self.assertEqual(v2, 250)
        v3=p.valuator().get_valuation(datetime(2022,9,4))
        self.assertEqual(v3, 250)
        v4=p.valuator().get_valuation(datetime(2022,9,5))
        self.assertEqual(v4, 450)
        v5=p.valuator().get_valuation(datetime(2022,9,8))
        self.assertEqual(v5, 450)
        v6=p.valuator().get_valuation(datetime(2022,9,12))
        self.assertEqual(v6, 200)


    def test_dated_buy_disorder(self):
        p:Portfolio = Portfolio("test", datetime(2022,9,1))
        p.add("USD", 200, datetime(2022,9,5))
        p.add("USD", 150, datetime(2022,9,2))
        p.withdraw("USD", 250, datetime(2022,9,10))
        p.add("USD", 100, datetime(2022,9,1))

        v1=p.valuator().get_valuation(datetime(2022,9,1))
        self.assertEqual(v1, 100)
        v2=p.valuator().get_valuation(datetime(2022,9,2))
        self.assertEqual(v2, 250)
        v3=p.valuator().get_valuation(datetime(2022,9,4))
        self.assertEqual(v3, 250)
        v4=p.valuator().get_valuation(datetime(2022,9,5))
        self.assertEqual(v4, 450)
        v5=p.valuator().get_valuation(datetime(2022,9,8))
        self.assertEqual(v5, 450)
        v6=p.valuator().get_valuation(datetime(2022,9,12))
        self.assertEqual(v6, 200)

        

    def test_dated_buy_multiccy(self):
        p:Portfolio = Portfolio("test", datetime(2022,9,1))
        p.add("USD", 200, datetime(2022,9,5))
        p.add("CHF", 150, datetime(2022,9,2))
        p.withdraw("CHF", 50, datetime(2022,9,10))
        p.add("USD", 100, datetime(2022,9,1), tags={'test'})
        p.add("EUR", 100, datetime(2022,9,1), tags={'test'})
        p.add("CHF", 250, datetime(2022,9,5))
        v5=p.valuator().get_valuation(datetime(2022,9,8))
        self.assertAlmostEqual(v5, 809, delta=1)
        v4=p.valuator().get_valuation(datetime(2022,9,5))
        self.assertAlmostEqual(v4, 805, delta=1)
        v6=p.valuator().get_valuation(datetime(2022,9,12))
        self.assertAlmostEqual(v6, 765, delta=1)
        v1=p.valuator().get_valuation(datetime(2022,11,12))
        self.assertAlmostEqual(v1, 764, delta=1)
        v3=p.valuator().get_valuation(datetime(2022,9,4))
        self.assertAlmostEqual(v3, 352, delta=1)
        v2=p.valuator().get_valuation(datetime(2022,9,2))
        self.assertAlmostEqual(v2, 352, delta=1)

    def test_valuation_before_transaction(self):
        p:Portfolio = Portfolio("test", datetime(2022,9,1))
        p.add("USD", 200, datetime(2022,9,5))
        v=p.valuator().get_valuation(datetime(2022,9,2))
        self.assertEqual(v, 0)
        p.add("USD", 300, datetime(2022,9,2))
        v=p.valuator().get_valuation(datetime(2022,9,5))
        self.assertEqual(v, 500)

    def test_stocks_with_tags_portfolio(self):
        my_portfolio:Portfolio = Portfolio()
        my_portfolio.buy('MSCI', 2578, tags={'PERFORMANCE SHARES'}) #Performance shares
        my_portfolio.buy('MSCI', 3916, tags={'RESTRICTED SHARES'}) #Restricted shares
        my_portfolio.buy('MSCI', 1110, tags={'STOCK OPTIONS'}) #Stock options
        my_portfolio.buy('MSCI', 807, tags={'BROADRIDGE SHARES'})  #Bradridge shares
        my_portfolio.buy('MSCI', 3000, tags={'MORGAN STANLEY SHARES'})  #Bradridge shares
        v:PortfolioValuator = PortfolioValuator(portfolio=my_portfolio)
        msci_stocks = v.get_valuation(datetime(2022,11,27))
        self.assertEqual(len(my_portfolio.get_positions()), 5)
        self.assertAlmostEqual(msci_stocks, 5845398.97, delta=0.01)

    def test_portfolio_ts(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        # The index valuation will calculate the value of the index from its base date and base value
        v:IndexValuator = IndexValuator(portfolio=p, base_date=datetime(2010,1,1), base_value=100)
        index_valuations:TimeSeries = v.get_index_valuations()

        # Another way of computing the indexed time series is to rebase the time series itself:
        v:PortfolioValuator = p.valuator()
        adjclose_ts:TimeSeries = v.get_valuations(start_date=datetime(2010,1,1))
        index_valuations2 = adjclose_ts.rebase()
        self.assertEqual(index_valuations2, index_valuations)

    def test_historical_portfolio_valuation(self):
         PortfolioValuator(portfolio=self.create_sample_portfolio("MyPortfolio", datetime(2021,1,18))).get_valuations(datetime(2021,1,18), ccy="CHF")


if __name__ == '__main__':
    unittest.main()
