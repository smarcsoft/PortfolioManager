import abc
from datetime import date, datetime, timedelta
import unittest
from numpy import ndarray, number
import numpy
import pandas as pd
from exceptions import PMException
from PositionIdentifier import PositionIdentifier, Currency, CASH, EQUITY, Ticker,  check_currency
from Positions import Positions
from TimeSeries import TimeSeries
from pmdata import get_fx
from pmdata import get_timeseries, get_ticker



#List of currencies supported by the system
DEFAULT_VALUATION_DATAPOINT='adjusted_close'
DEFAULT_CURRENCY='USD'
DEFAULT_INSTRUMENT_TYPE='Common Stock'
DEFAULT_MARKET_CODE='US'


class Portfolio:
    '''
    A portfolio is:
    . A collection of instruments
    . Quantities of these instruments
    '''
    def __init__(self, name:str="DEFAULT") -> None:
        self.positions:Positions = Positions()
        self.name = name

    def get_name(self)->str:
        return self.name

    def get_positions(self) -> Positions:
        '''
        Returns the list of positions of the portfolio in a dictionary keyed my ticker.
        '''
        return self.positions

    def _set_positions(self, positions:Positions) -> Positions:
        '''
        Returns the list of positions of the portfolio in a dictionary keyed my ticker.
        '''
        self.positions = positions
    
    def add(self, currency:str, quantity:number, tags:set=None):
        '''
        Adds a quantify of cash in the portfolio
        '''
        check_currency(currency)
        self._buy(PositionIdentifier(CASH, Currency(currency), tags), quantity)

    def buy(self, ticker_code:str, quantity:number, tags:set=None ):
        '''
        Adds an instrument in the portfolio
        '''  
        if(ticker_code.find(".") != -1):
            (ticker,exchange) = ticker_code.split('.')
            full_ticker = ticker+"."+exchange
        else:
            full_ticker = ticker_code+"." + DEFAULT_MARKET_CODE
        # Get meta data for the ticker
        try:
            ticker = get_ticker(full_ticker)
            self._buy(PositionIdentifier(EQUITY, ticker, tags), quantity)
        except Exception:
            raise PMException("Cannot find or process the instrument identified by ticker code " + ticker_code)
        
    def create(self, name, tags:set):
        positions:Positions = self.positions.get_tagged_positions(tags)
        toreturn= Portfolio(name)
        toreturn._set_positions(positions)
        return toreturn

    def _buy(self, ticker:PositionIdentifier, quantity:number):
        # Tagged positions are not aggregared with non-tagged positions. They are aggregated together 
        # if they have the same tickers and tags
        if(ticker in self.positions):
            self.positions[ticker] = self.positions[ticker] + quantity
        else:
            self.positions[ticker] = quantity

    def sell(self, ticker_code:str, quantity:number):
        '''
        Sells an equity from the portfolio
        '''
        if(ticker_code.find(".") != -1):
            (ticker,exchange) = ticker_code.split('.')
            full_ticker = ticker+"."+exchange
        else:
            full_ticker = ticker_code+"." + DEFAULT_MARKET_CODE
        # Get meta data for the ticker
        try:
            ticker = get_ticker(full_ticker)
            self._sell(PositionIdentifier(EQUITY, ticker), quantity)
        except Exception:
            raise PMException("Cannot find or process the instrument identified by ticker code " + ticker_code)


    def withdraw(self, currency:str, quantity:number):
        '''
        Withdraws some cash from the portfolio
        '''
        #TODO: Having segregated position can prevent withdrawing or selling enough stocks
        check_currency(currency)
        if((PositionIdentifier(CASH, Currency(currency)) in self.positions) and (self.positions[PositionIdentifier(CASH, Currency(currency))] >= quantity)):
            self.positions[PositionIdentifier(CASH, Currency(currency))] = self.positions[PositionIdentifier(CASH,Currency(currency))] - quantity
        else:
            raise PMException("Cannot sell {quantity} {currency}. The portfolio does not have this amount of cash in the denominated currency".format(quantity=quantity, currency=currency))

    def _sell(self, ticker:PositionIdentifier, quantity:number):
        if((ticker in self.positions) and (self.positions[ticker] >= quantity)):
            self.positions[ticker] = self.positions[ticker] - quantity
        else:
            raise PMException("Cannot sell {ticker_code}. Either the portfolio does not own the instrument or it does not have enough quantity of this instrument.".format(ticker_code=ticker))


    def get_shares(self, ticker_code:str , exchange:str='US', type:str =DEFAULT_INSTRUMENT_TYPE,  isin:str="", name:str="", country:str="USA",  currency:str="USD", tags:set=None )->number:
        return self._get_shares(PositionIdentifier(EQUITY, Ticker(ticker_code, exchange, type,isin,name, country, currency), tags))


    def get_position_amount(self, pi:PositionIdentifier)->number:
        return self.positions[pi]

    def get_cash(self, currency:str, tags:set=None)->number:
        check_currency(currency)
        return self.positions[PositionIdentifier(CASH,Currency(currency), tags)]

    def valuator(self):
        return PortfolioValuator(self)

    def _get_shares(self, ticker:PositionIdentifier)->number:
        return self.positions[ticker]

    def __repr__(self) -> str:
        return "Portfolio " + self.name +" \n" + str(self.positions)

class PortfolioGroup:
    def __init__(self, name:str="DEFAULT") -> None:
        self.__name = name
        self.__portfolios = {}

    def add(self, p:Portfolio, name:str='DEFAULT'):
        if name not in self.__portfolios:
            self.__portfolios[name] = list()
        self.__portfolios[name].append(p)

    def __len__(self):
        '''
        Returns the number of groups, not the number of portfolios
        '''
        return len(self.__portfolios.keys())

    def get(self, name:str)->list:
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
        for portfolio_set_name in self.__portfolios:
            portfolio_list = self.__portfolios[portfolio_set_name]
            for p in portfolio_list:
                toreturn.append(p)
        return toreturn

    def __repr__(self) -> str:
        toreturn = "Portfolio Group " + self.__name +" containing " + str(self.__len__())+" set(s) of portfolios: \n"
        for (i, portfolio_set_name) in enumerate(self.__portfolios):
            toreturn +="Set "+ portfolio_set_name+":\n"
            portfolio_list = self.__portfolios[portfolio_set_name]
            for (j, p) in enumerate(portfolio_list):
                toreturn += str(p)
                if((i != len(self.__portfolios)-1) or (j != len(portfolio_list) -1)):
                    toreturn += '\n'
        return toreturn
    
    def valuator(self):
        return PortfolioGroupValuator(self)

class InstrumentValuator:
    def __init__(self, portfolio:Portfolio, pi:PositionIdentifier, target_currency:Currency) -> None:
        self.target_currency = target_currency
        self.portfolio = portfolio
        self.pi = pi

    @abc.abstractmethod
    def get_valuation(self, valdate:date)->number:
        raise NotImplementedError("get_valuation should have an implementation in derived classes")

    def convert_to_target_currency(self, value:number, valdate:date, source_currency:Currency=DEFAULT_CURRENCY)->number:
        if(source_currency != self.target_currency):
            # Value the instrument to USD and then from USD to the target currency
            value_usd = value
            if(source_currency != Currency("USD")):
                value_usd = self.__convert_to_usd(value, source_currency, valdate)

            if(self.target_currency != Currency('USD')):
                return self.__convert_usd_to_target(value_usd, self.target_currency, valdate)
            return value_usd
        return value


    def __convert_usd_to_target(self, value:number, target_currency:Currency, valdate:date)->number:
        fx = get_fx(target_currency.get_identifier(), valdate)
        return value * fx

    def __convert_to_usd(self, value:number, source_currency:Currency, valdate:date)->number:
        # Get the FX rate
        fx = get_fx(source_currency.get_identifier(), valdate)
        return value/fx


    @staticmethod
    def valuator(portfolio:Portfolio, pi:PositionIdentifier, target_currency:Currency, **valuator_args):
        '''
        Returns the correct valuator for the right time of financial instrument.
        '''
        if(pi.type == CASH):
            return CashValuator(portfolio, pi, target_currency)
        if(pi.type == EQUITY):
            return EquityValuator(portfolio, pi, target_currency, **valuator_args)
        raise PMException("Could not create valuator for " + pi)
    

class EquityValuator(InstrumentValuator):
    def __init__(self, portfolio:Portfolio, pi:PositionIdentifier, target_currency:Currency, dpname=DEFAULT_VALUATION_DATAPOINT) -> None:
        InstrumentValuator.__init__(self, portfolio, pi, target_currency)
        self.valuation_data_point = dpname

    def get_valuation(self, valdate:date)->number:
        closing_price = get_timeseries(full_ticker=self.pi.id.get_full_ticker(), datapoint_name=self.valuation_data_point).get(valdate)
        return self.convert_to_target_currency(closing_price*self.portfolio.get_position_amount(self.pi), valdate, self.pi.id.get_currency())


class CashValuator(InstrumentValuator):
    def __init__(self, portfolio:Portfolio, pi:PositionIdentifier, target_currency:Currency) -> None:
        InstrumentValuator.__init__(self, portfolio,pi, target_currency)

    def get_valuation(self, valdate:date)->number:
        return self.convert_to_target_currency(self.portfolio.get_position_amount(self.pi), valdate, self.pi.id)

class IPorfolioValuator:
  
    @abc.abstractmethod
    def get_valuations(self, start_date:date=None, end_date:date=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
        raise NotImplementedError("get_valuations should have an implementation in derived classes")

    @abc.abstractmethod
    def get_valuation(self, valdate:date=None, dpname:str = DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->number:
        raise NotImplementedError("get_valuation should have an implementation in derived classes")

class PortfolioGroupValuator(IPorfolioValuator):
    def __init__(self, portfolio_group:PortfolioGroup) -> None:
        self.portfolio_group = portfolio_group

    def get_valuations(self, start_date:date=None, end_date:date=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
        #For each portfolio in the group, value it
        ts:TimeSeries|None = None
        for (i,portfolio) in enumerate(self.portfolio_group):
            pv = PortfolioValuator(portfolio)
            if(i==0):
                ts = pv.get_valuations(start_date, end_date, dp_name,ccy)
            else:
                ts += pv.get_valuations(start_date, end_date, dp_name,ccy)
        return ts

    def get_valuation(self, valdate:date=None, dpname:str = DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->number:
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

    def get_valuations(self, start_date:date=None, end_date:date=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
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
        
        period:pd.DatetimeIndex = pd.date_range(start_date, end_date, freq='D')
        toreturn:ndarray = numpy.zeros((end_date - start_date).days+1)
        for i, d in enumerate(period):
            toreturn[i]=self.get_valuation(start_date+timedelta(days=i), dpname=dp_name, ccy=ccy)
        return TimeSeries(toreturn, start_date=start_date, end_date=end_date)

    def get_valuation(self, valdate:date=None, dpname:str = DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->number:
        portfolio_valuation:number = 0.0
        for position_identifier in self.portfolio.get_positions():
            instrument_value:number = InstrumentValuator.valuator(self.portfolio, position_identifier, Currency(ccy), dpname=dpname).get_valuation(valdate)
            portfolio_valuation = portfolio_valuation + instrument_value
        return portfolio_valuation

    def get_start_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT):
        # Check the earliest start date of all instruments
        start_date:date|None = None
        for position_identifier in self.portfolio.get_positions():
            # Ignore cash positions to compute earliest start date of the portfolio
            if(position_identifier.type == CASH): continue
            sd = get_timeseries(full_ticker=position_identifier.id.get_full_ticker(), datapoint_name=dp_name).get_start_date()
            if((start_date == None) or (start_date < sd)):
                start_date = sd
        if(start_date == None):
            raise PMException("Could not determine the earliest start date of the portfolio. Please specify the start date explicitly.")
        return start_date


    def get_end_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT):
        end_date:date|None = None
        for position_identifier in self.portfolio.get_positions():
            # Ignore cash positions to compute earliest start date of the portfolio
            if(position_identifier.type == CASH): continue
            ed = get_timeseries(full_ticker=position_identifier.id.get_full_ticker(), datapoint_name=dp_name).get_end_date()
            if((end_date == None) or (end_date < ed)):
                end_date = ed
            if(end_date == None):
                raise PMException("Could not determine the latest end date of the portfolio. Please specify the end date explicitly.")
        return end_date


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
            toreturn[i]=toreturn[i-1] * self.get_valuation(self.base_date+timedelta(days=i), dpname=dp_name, ccy=ccy) / self.get_valuation(self.base_date+timedelta(days=i-1), dpname=dp_name, ccy=ccy)
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
        self.assertAlmostEqual((PortfolioValuator(portfolio=p).get_valuation(date.fromisoformat("2022-11-08"))), 60561, delta=1)


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
        pg.add(p, "EQUITIES")
        pg.add(p2, "CASH")
        self.assertTrue(len(pg), 2)
        p3:Portfolio = Portfolio("Cash in Europe")
        p3.add('EUR', 25000)
        pg.add(p3, "CASH")
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
#    @time_func
    def test_get_valuations(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_valuations(date.fromisoformat("2020-01-01"), date.fromisoformat('2020-12-31')).size(), (date.fromisoformat('2020-12-31') - date.fromisoformat("2020-01-01")).days+1)

#    @time_func
    def test_get_start_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_start_date(), datetime.strptime('1990-02-16', '%Y-%m-%d').date())

    
    def test_msci_valuation(self):
        p:Portfolio = Portfolio()
        p.buy('MSCI', 10)
        self.assertEqual(PortfolioValuator(p).get_valuations().get(date.fromisoformat("2022-09-01")),get_timeseries("MSCI.US", "adjusted_close").get(date(2022,9,1))*10)
        # This valuation should not change unless the historical time series is restated.
        self.assertAlmostEqual(PortfolioValuator(p).get_valuations().get(date(2022,9,1)),4556.9, delta=0.1) 

    def test_portfolio(self):
        my_portfolio:Portfolio = Portfolio()
        my_portfolio.buy('MSCI', 2578) #Performance shares
        my_portfolio.buy('MSCI', 3916) #Restricted shares
        my_portfolio.buy('MSCI', 3916) #Stock options
        my_portfolio.buy('MSCI', 807)  #Bradridge shares
        my_portfolio.add('USD', 1000000)
        PortfolioValuator(portfolio=my_portfolio).get_valuations().get(date.fromisoformat("2022-09-01"))


    def test_portfolio_group(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        pg = PortfolioGroup()
        pg.add(p)
        self.assertAlmostEqual((pg.valuator().get_valuation(date.fromisoformat("2022-09-01"))), 3495, delta=1)
        p2:Portfolio = Portfolio()
        p.buy('MSCI', 50)
        pg.add(p2)
        self.assertAlmostEqual((pg.valuator().get_valuation(date.fromisoformat("2022-09-01"))), 26278, delta = 1)

    def test_portfolio_group2(self):
        pg:PortfolioGroup = PortfolioGroup("My Investments")
        p:Portfolio = Portfolio("My cash")
        p.add('USD', 67000)
        p.add('CHF', 480000)
        pg.add(p, "CASH PORTFOLIO GROUP")
        self.assertAlmostEqual(pg.valuator().get_valuation(date.fromisoformat("2022-09-01")),557246, delta=1)
        p2:Portfolio = Portfolio()
        p2.buy('MSFT', 10)
        p2.buy('MSFT', 20)
        pg.add(p2)
        self.assertAlmostEqual(pg.valuator().get_valuation(date.fromisoformat("2022-09-01")), 565036, delta=1)

 #   @time_func
    def test_get_end_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertGreaterEqual(v.get_end_date(), datetime.strptime('2022-09-22', '%Y-%m-%d').date())

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
        value:number = v.get_valuation(valdate=date.fromisoformat("2022-09-01"))
        self.assertAlmostEqual(value, 455.69, delta=0.2)
        p.add('USD', 2000000)
        new_value:number = v.get_valuation(valdate=date.fromisoformat("2022-09-01"))
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
        value:number = v.get_valuation(valdate=date.fromisoformat("2022-09-01"))
        self.assertAlmostEqual(value, 4556.89, delta=1)
        value_chf:number = v.get_valuation(valdate=date.fromisoformat("2022-09-01"), ccy="CHF")
        self.assertAlmostEqual(value_chf, 4461, delta=1)

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
        with_cash = PortfolioValuator(portfolio=my_portfolio).get_valuation(date.fromisoformat("2022-09-01"))
        my_portfolio.add('ETH', 32.9123, tags={'CRYPTOS'})
        my_portfolio.add('BTC', 2.2347, tags={'CRYPTOS'})
        my_portfolio.add('DOT', 1214.4988, tags={'CRYPTOS'})
        with_cryptos = PortfolioValuator(portfolio=my_portfolio).get_valuation(date.fromisoformat("2022-09-01"))
        self.assertAlmostEqual(with_cryptos - with_cash, 105911, delta=1)

        my_portfolio.add('EUR', 1462.32, tags={'SWISSQUOTE'})
        my_portfolio.add('USD', 165928.14, tags={'SWISSQUOTE'})
        my_portfolio.buy('IPRP.SW', 235, tags={'SWISSQUOTE'})
        my_portfolio.buy('VUSA.SW', 800, tags={'SWISSQUOTE'})
        my_portfolio.buy('WSRUSA.SW', 489, tags={'SWISSQUOTE'})
        my_portfolio.buy('EFA', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('LCTU', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('STLA.PA', 2923, tags={'SWISSQUOTE'})

        with_swissquote = PortfolioValuator(portfolio=my_portfolio).get_valuation(date.fromisoformat("2022-09-01"))
#        print(with_swissquote- with_cryptos)
        swissquote = my_portfolio.create("swissquote", {'SWISSQUOTE'})
        self.assertEqual(len(swissquote.get_positions()), 8)
        sqvalue = PortfolioValuator(portfolio=swissquote).get_valuation(date(2022,9,1))
        self.assertAlmostEqual(with_swissquote - with_cryptos, sqvalue, delta=1)


if __name__ == '__main__':
    unittest.main()
