from datetime import date, timedelta
import types
import numpy as np
import pandas as pd

fill = types.SimpleNamespace()
fill.FORWARDFILL = 1
fill.BACKFILL = 2

class PMException(Exception):
    pass

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

   