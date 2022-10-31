import datetime
import unittest

from numpy import ndarray, number
import numpy
from Portfolio import Portfolio
from datetime import date, datetime, timedelta
from TimeSeries import TimeSeries
import pandas as pd
from Ticker import Ticker
from pmdata import get_timeseries

DEFAULT_VALUATION_DATAPOINT='adjusted_close'
DEFAULT_CURRENCY='USD'

class InstrumentValuator:
    def __init__(self, ticker:Ticker) -> None:
        self.ticker = ticker

    def get_valuation(self, valdate:date, quantity:number, dpname:str=DEFAULT_VALUATION_DATAPOINT)->number:
        closing_price = get_timeseries(full_ticker=self.ticker.get_full_ticker(), datapoint_name=dpname).get(valdate)
        return closing_price*quantity


class PortfolioValuator:
    def __init__(self, portfolio:Portfolio) -> None:
        self.portfolio = portfolio

    def get_valuations(self, start_date:date=None, end_date:date=None, dp_name=DEFAULT_VALUATION_DATAPOINT, ccy:str=DEFAULT_CURRENCY)->TimeSeries:
        '''
        Values the portfolio and returns a time series of valuations.
        Parameters are:
        start_date: Inclusive start date of the valuation period. If None, the portfolio will be valued from the earliest possible valuation date, which is the date from which we have prices for all positions of the portfolio.
        end_date: Inclusive end date of the valuation period. If None, the portfolio will be valued up to the latest possible valuation date, which is the date to which we have prices for all positions of the portfolio.
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
            instrument_value:number = InstrumentValuator(instrument).get_valuation(valdate, self.portfolio._get_quantity(instrument), dpname=dpname)
            portfolio_valuation = portfolio_valuation + instrument_value
        return portfolio_valuation

    def get_start_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT):
        # Check the earliest start date of all instruments
        start_date:date = None
        for ticker in self.portfolio.get_positions():
            sd = get_timeseries(full_ticker=ticker.get_full_ticker(), datapoint_name=dp_name).get_start_date()
            if((start_date == None) or (start_date < sd)):
                start_date = sd
        return start_date


    def get_end_date(self, dp_name:str=DEFAULT_VALUATION_DATAPOINT):
        end_date:date = None
        for ticker in self.portfolio.get_positions():
            ed = get_timeseries(full_ticker=ticker.get_full_ticker(), datapoint_name=dp_name).get_end_date()
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
    def test_get_valuations(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_valuations(date.fromisoformat("2020-01-01"), date.fromisoformat('2020-12-31')).size(), (date.fromisoformat('2020-12-31') - date.fromisoformat("2020-01-01")).days+1)

    def test_get_start_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertEqual(v.get_start_date(), datetime.strptime('1990-02-16', '%Y-%m-%d').date())


    def test_get_end_date(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        self.assertGreaterEqual(v.get_end_date(), datetime.strptime('2022-09-22', '%Y-%m-%d').date())

    def test_dp(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 1)
        v:PortfolioValuator = PortfolioValuator(portfolio=p)
        ts:TimeSeries = v.get_valuations(start_date=None, end_date=None, dp_name='close')
        tsa:TimeSeries = v.get_valuations(start_date=None, end_date=None, dp_name='adjusted_close')
        self.assertEqual(ts.size(), tsa.size())
        self.assertLessEqual(tsa.get_full_time_series()[0], ts.get_full_time_series()[0])

    def test_index_valuation(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        p.buy('MSCI', 30)
        v:IndexValuator = IndexValuator(portfolio=p, base_date=date.fromisoformat("2010-01-01"), base_value=100)
        print(v.get_index_valuations(end_date=date.fromisoformat("2021-12-31")).get_full_time_series())



if __name__ == '__main__':
    unittest.main()