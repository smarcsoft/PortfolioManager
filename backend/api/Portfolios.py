import abc
from datetime import date, datetime, timedelta
import unittest
from numpy import ndarray, number
import numpy
import pandas as pd
from Ticker import Ticker
from PMExceptions import PMException
from PositionIdentifier import PositionIdentifier, Currency, CASH, EQUITY
from Positions import Positions
from TimeSeries import TimeSeries
from pmdata import get_timeseries



#List of currencies supported by the system
supported_currencies =("USD","EUR", "RUB", "GBP", "CNY", "JPY", "SGD", "INR", "CHF", "AUD", "CAD", "HKD", "MYR", "NOK", "NZD", "ZAR","SEK", "DKK", "BRL", "ZAC", "MXN", "TWD", "KRW", "CLP", "CZK", "HUF", "IDR", "ISK", "MXV", "PLN", "TRY", "UYU", "THB", "SAR", "ILS")
DEFAULT_VALUATION_DATAPOINT='adjusted_close'
DEFAULT_CURRENCY='USD'
DEFAULT_INSTRUMENT_TYPE='Common Stock'


def check_currency(currency:Currency):
        if currency not in supported_currencies:
            raise PMException("Invalid currency ({currency})".format(currency=currency))
        return True


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
    
    def add(self, currency:Currency, quantity:number):
        '''
        Adds a quantify of cash in the portfolio
        '''
        check_currency(currency)
        if(PositionIdentifier(CASH, currency) in self.positions):
            self.positions[PositionIdentifier(CASH, currency)] = self.positions[PositionIdentifier(CASH,currency)] + quantity
        else:
            self.positions[PositionIdentifier(CASH,currency)] = quantity

    def buy(self, ticker_code:str, quantity:number, exchange:str='US', type:str =DEFAULT_INSTRUMENT_TYPE,  isin:str="", name:str="", country:str="USA",  currency:str="USD" ):
        '''
        Adds an equity in the portfolio
        '''
        self._buy(PositionIdentifier(EQUITY, Ticker(ticker_code, exchange, type,isin,name, country, currency)), quantity)

    def _buy(self, ticker:PositionIdentifier, quantity:number):
        if(ticker in self.positions):
            self.positions[ticker] = self.positions[ticker] + quantity
        else:
            self.positions[ticker] = quantity

    def sell(self, ticker_code:str, quantity:number, exchange:str='US', type:str =DEFAULT_INSTRUMENT_TYPE,  isin:str="", name:str="", country:str="USA",  currency:str="USD" ):
        '''
        Sells an equity from the portfolio
        '''
        self._sell(PositionIdentifier(EQUITY, Ticker(ticker_code, exchange, type,isin,name, country, currency)), quantity)


    def withdraw(self, currency:Currency, quantity:number):
        '''
        Withdraws some cash from the portfolio
        '''
        check_currency(currency)
        if((PositionIdentifier(CASH, currency) in self.positions) and (self.positions[PositionIdentifier(CASH, currency)] >= quantity)):
            self.positions[PositionIdentifier(CASH, currency)] = self.positions[PositionIdentifier(CASH,currency)] - quantity
        else:
            raise PMException("Cannot sell {quantity} {currency}. The portfolio does not have this amount of cash in the denominated currency".format(quantity=quantity, currency=currency))

    def _sell(self, ticker:PositionIdentifier, quantity:number):
        if((ticker in self.positions) and (self.positions[ticker] >= quantity)):
            self.positions[ticker] = self.positions[ticker] - quantity
        else:
            raise PMException("Cannot sell {ticker_code}. Either the portfolio does not own the instrument or it does not have enough quantity of this instrument.".format(ticker_code=ticker))


    def get_shares(self, ticker_code:str , exchange:str='US', type:str =DEFAULT_INSTRUMENT_TYPE,  isin:str="", name:str="", country:str="USA",  currency:str="USD" )->number:
        return self._get_shares(PositionIdentifier(EQUITY, Ticker(ticker_code, exchange, type,isin,name, country, currency)))

    def get_cash(self, currency:Currency)->number:
        check_currency(currency)
        return self.positions[PositionIdentifier(CASH,currency)]

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
    def __init__(self, portfolio:Portfolio, target_currency:Currency) -> None:
        self.target_currency = target_currency
        self.portfolio = portfolio

    @abc.abstractmethod
    def get_valuation(self, valdate:date)->number:
        raise NotImplementedError("get_valuation should have an implementation in derived classes")

    def convert_target_currency(self, value:number, valdate:date, source_currency:Currency=DEFAULT_CURRENCY)->number:
        if(source_currency != self.target_currency):
            #TODO support currency conversion
            raise PMException("Currency conversions are not yet supported")
        return value

    @staticmethod
    def valuator(portfolio:Portfolio, pi:PositionIdentifier, target_currency:Currency, **valuator_args):
        if(pi.type == CASH):
            return CashValuator(portfolio, pi.id, target_currency)
        if(pi.type == EQUITY):
            return EquityValuator(portfolio, pi.id,target_currency, **valuator_args)
        raise PMException("Could not create valuator for " + pi)
    

class EquityValuator(InstrumentValuator):
    def __init__(self, portfolio:Portfolio, ticker:Ticker, target_currency:Currency, dpname=DEFAULT_VALUATION_DATAPOINT) -> None:
        InstrumentValuator.__init__(self, portfolio, target_currency)
        self.valuation_data_point = dpname
        self.ticker = ticker

    def get_valuation(self, valdate:date)->number:
        closing_price = get_timeseries(full_ticker=self.ticker.get_full_ticker(), datapoint_name=self.valuation_data_point).get(valdate)
        return self.convert_target_currency(closing_price*self.portfolio.get_shares(self.ticker.code, self.ticker.exchange), valdate, self.target_currency )


class CashValuator(InstrumentValuator):
    def __init__(self, portfolio:Portfolio, cash_currency:Currency, target_currency:Currency) -> None:
        InstrumentValuator.__init__(self, portfolio, target_currency)
        self.cash_currency = cash_currency

    def get_valuation(self, valdate:date)->number:
        return self.convert_target_currency(self.portfolio.get_cash(self.cash_currency), valdate, self.target_currency)

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
        ts:TimeSeries = None
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
            instrument_value:number = InstrumentValuator.valuator(self.portfolio, position_identifier, ccy, dpname=dpname).get_valuation(valdate)
            portfolio_valuation = portfolio_valuation + instrument_value
        return portfolio_valuation

    def get_start_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT):
        # Check the earliest start date of all instruments
        start_date:date = None
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
        end_date:date = None
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
        pg:PortfolioGroup = PortfolioGroup("My Investments")
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
        pg:PortfolioGroup = PortfolioGroup("My Investments")
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
        self.assertAlmostEqual((pg.valuator().get_valuation(date.fromisoformat("2022-09-01"))), 3509, delta=1)
        p2:Portfolio = Portfolio()
        p.buy('MSCI', 50)
        pg.add(p2)
        self.assertAlmostEqual((pg.valuator().get_valuation(date.fromisoformat("2022-09-01"))), 26355, delta = 1)

    def test_portfolio_group2(self):
        pg:PortfolioGroup = PortfolioGroup("My Investments")
        p:Portfolio = Portfolio("My cash")
        p.add('USD', 67000)
        p.add('CHF', 480000)
        pg.add(p, "CASH PORTFOLIO GROUP")
        self.assertEqual(pg.valuator().get_valuation(date.fromisoformat("2022-09-01")),547000)
        p2:Portfolio = Portfolio()
        p2.buy('MSFT', 10)
        p2.buy('MSFT', 20)
        pg.add(p2)
        self.assertAlmostEqual(pg.valuator().get_valuation(date.fromisoformat("2022-09-01")), 554811, delta=1)

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
        self.assertAlmostEqual(value, 456.9, delta=0.1)
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
        self.assertAlmostEqual(ts[len(ts)-1], 1574, delta=0.1)

if __name__ == '__main__':
    unittest.main()
