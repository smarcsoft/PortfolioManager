from datetime import date, timedelta
import types
import unittest
import numpy as np
from numpy import ndarray, number
import pandas as pd
from PMExceptions import PMException

fill = types.SimpleNamespace()
fill.FORWARDFILL = 1
fill.BACKFILL = 2



class TimeSeries:

    '''
    Encapsulate a time series which is basically:
    a start date
    an end date
    elements of data between the start date and the end date
    '''
    def __init__(self, ts:np.ndarray, start_date:date=None, end_date:date=None, fill_method=None):
        self.time_series = ts
        self.start_date = start_date
        self.end_date = end_date
        if((start_date != None) and (end_date != None)):
            # A few consistency checks:
            # 1. We cannot have start_date > end_date
            # 2. We must have at least end-date - start-date elements in the array
            self.days = (end_date - start_date).days + 1
            if self.days > ts.size: raise PMException("Cannot instanciate time series with array of size {size}, start date {start_date} and end_date {end_date}".format(size = ts.size, start_date=start_date, end_date = end_date))
        # Clean the time series
        if(fill_method != None):
            self.missing(fill_method)
    
    def get_start_date(self)->date:
        return self.start_date
        
    def get_end_date(self)->date:
        return self.end_date
        
    def get_full_time_series(self)->np.ndarray:
        return self.time_series

    def __getitem__(self,i):
        return self.time_series[i]

    def __setitem__(self,i,v):
        self.time_series[i]=v

    def __iadd__(self, other):
        self.time_series+=other.time_series
        return self

    def __isub__(self, other):
        self.time_series-=other.time_series
        return self
    
    def __add__(self, other):
        return TimeSeries(self.time_series+other.time_series)

    def __sub__(self, other):
        return TimeSeries(self.time_series-other.time_series)

    def __mul__(self, other):
        return TimeSeries(self.time_series*other.time_series)

    def __truediv__(self, other):
        return TimeSeries(self.time_series/other.time_series)
    

    def get(self,date:date)->np.float32:
        return self.time_series[(date - self.start_date).days]
    
    def size(self)->int:
        return self.time_series.size

    def days(self)->int:
        return self.days

    def cut2dates(self, start_date:date, end_date:date):
        return TimeSeries(self.time_series[(start_date -self.start_date).days:(end_date-self.end_date).days], start_date, end_date)

    def cutndays(self, start_date:date, days:int):
        return TimeSeries(self.time_series[(start_date -self.start_date).days:(start_date -self.start_date).days + days], start_date, start_date + timedelta(days=days-1))

    def rebase(self, base_date:date=None, base_value:number=100):
        '''
        Rebase the time series. 
        We are rebasing a time series from a base date and a base value by computing the returns of the 
        original time series from that date. 
        '''
        if(base_date == None):
            base_date = self.start_date
        period:pd.DatetimeIndex = pd.date_range(base_date, self.end_date, freq='D')
        toreturn:ndarray = np.zeros((self.end_date - base_date).days+1)
        toreturn[0]=base_value
        for i, d in enumerate(period):
            if(i==0): continue #Skip the first date since it is valued as base_value
            toreturn[i]=toreturn[i-1] * self.get(base_date+timedelta(days=i))/ self.get(base_date+timedelta(days=i-1))
        return TimeSeries(toreturn, base_date, end_date=self.end_date)

    
    def missing(self, method=fill.FORWARDFILL):
        match method:
            case fill.FORWARDFILL:
                self.__forwardfill()
            case fill.BACKFILL:
                self.__backfill()
            case _:
                raise PMException("Incorrect method {method}".format(method=method))


    def __forwardfill(self):
        df = pd.DataFrame(self.time_series)
        df.replace(0.0, method='ffill', inplace=True)
        self.time_series = df.to_numpy().flatten()

    def __backfill(self):
        df = pd.DataFrame(self.time_series)
        df.replace(0.0, method='bfill', inplace=True)
        self.time_series = df.to_numpy().flatten()


    def __repr__(self):
        return "Time Series from {start_date:%m-%d-%Y} to {end_date:%m-%d-%Y} of {size} days with {ts}".format(start_date = self.start_date, end_date = self.end_date, size = self.time_series.size, ts=self.time_series)

    def __eq__(self, other):
        return (self.time_series == other.time_series).all() and (self.start_date == other.start_date) and (self.end_date == other.end_date)

    def __ne__(self, other):
        return not self.eq(other)

class UnitTestTimeSeries(unittest.TestCase):
    def test_iadd(self):
        ts1=TimeSeries(np.array([5,6,7,8]))
        ts2=TimeSeries(np.array([1,2,3,4]))
        ts1+=ts2
        self.assertEqual(ts1[0], 6)
        self.assertEqual(ts1[3], 12)

    def test_add(self):
        ts1=TimeSeries(np.array([5,6,7,8]))
        ts2=TimeSeries(np.array([1,2,3,4]))
        ts3 = ts1+ts2
        self.assertEqual(ts3[0], 6)
        self.assertEqual(ts3[3], 12)

    def test_isub(self):
        ts1=TimeSeries(np.array([5,6,7,8]))
        ts2=TimeSeries(np.array([1,2,3,4]))
        ts1-=ts2
        self.assertEqual(ts1[0], 4)
        self.assertEqual(ts1[3], 4)

    def test_sub(self):
        ts1=TimeSeries(np.array([5,6,7,8]))
        ts2=TimeSeries(np.array([1,2,3,4]))
        ts3 = ts1-ts2
        self.assertEqual(ts3[0], 4)
        self.assertEqual(ts3[3], 4)

    def test_mul(self):
        ts1=TimeSeries(np.array([5,6,7,8]))
        ts2=TimeSeries(np.array([1,2,3,4]))
        ts3 = ts1*ts2
        self.assertEqual(ts3[0], 5)
        self.assertEqual(ts3[3], 32)

    def test_div(self):
        ts1=TimeSeries(np.array([5,6,7,8]))
        ts2=TimeSeries(np.array([1,2,3,4]))
        ts3 = ts1/ts2
        self.assertEqual(ts3[0], 5)
        self.assertEqual(ts3[3], 2)

if __name__ == '__main__':
    unittest.main()