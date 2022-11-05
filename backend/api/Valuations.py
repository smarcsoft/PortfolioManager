import abc
import datetime
import unittest

from numpy import ndarray, number
import numpy
from Portfolio import Portfolio
from datetime import date, datetime, timedelta
from TimeSeries import TimeSeries
import pandas as pd
from Ticker import Ticker
from PMExceptions import PMException
from Portfolio import Currency
from Portfolio import CASH, EQUITY
from Portfolio import PositionIdentifier
from pmdata import get_timeseries
from timing import time_func

DEFAULT_VALUATION_DATAPOINT='adjusted_close'
DEFAULT_CURRENCY='USD'

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

class PortfolioValuator:
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
        for instrument in self.portfolio.get_positions():
            instrument_value:number = InstrumentValuator.valuator(self.portfolio, instrument, ccy, dpname=dpname).get_valuation(valdate)
            portfolio_valuation = portfolio_valuation + instrument_value
        return portfolio_valuation

    def get_start_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT):
        # Check the earliest start date of all instruments
        start_date:date = None
        for ticker in self.portfolio.get_positions():
            sd = get_timeseries(full_ticker=ticker.id.get_full_ticker(), datapoint_name=dp_name).get_start_date()
            if((start_date == None) or (start_date < sd)):
                start_date = sd
        return start_date


    def get_end_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT):
        end_date:date = None
        for ticker in self.portfolio.get_positions():
            ed = get_timeseries(full_ticker=ticker.id.get_full_ticker(), datapoint_name=dp_name).get_end_date()
            if((end_date == None) or (end_date < ed)):
                end_date = ed
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
    @time_func
    def test_get_valuations(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_valuations(date.fromisoformat("2020-01-01"), date.fromisoformat('2020-12-31')).size(), (date.fromisoformat('2020-12-31') - date.fromisoformat("2020-01-01")).days+1)

    @time_func
    def test_get_start_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_start_date(), datetime.strptime('1990-02-16', '%Y-%m-%d').date())

    @time_func
    def test_get_end_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertGreaterEqual(v.get_end_date(), datetime.strptime('2022-09-22', '%Y-%m-%d').date())

    @time_func
    def test_dp(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 1)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        ts:TimeSeries = v.get_valuations(start_date=None, end_date=None, dp_name='close')
        tsa:TimeSeries = v.get_valuations(start_date=None, end_date=None, dp_name='adjusted_close')
        self.assertEqual(ts.size(), tsa.size())
        self.assertLessEqual(tsa.get_full_time_series()[0], ts.get_full_time_series()[0])

    @time_func
    def test_cash(self):
        p:Portfolio = Portfolio()
        p.buy('MSCI', 1)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        value:number = v.get_valuation(valdate=date.fromisoformat("2022-09-01"))
        self.assertAlmostEqual(value, 456.9, delta=0.1)
        p.add('USD', 2000000)
        new_value:number = v.get_valuation(valdate=date.fromisoformat("2022-09-01"))
        self.assertEqual(new_value-value, 2000000)

    @time_func
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