from datetime import date, datetime
from genericpath import exists
import os
import unittest
import numpy as np
import json
from TimeSeries import fill, TimeSeries, PMException
from Ticker import Ticker

TimeSeriesCache = dict[str, TimeSeries] #fully qualifiedticker (as string), timeseries

if 'DB_LOCATION' in os.environ:
    __default_dbbloc = os.environ['DB_LOCATION']
else:
    __default_dbbloc = "backend/db"
__dbloc = __default_dbbloc
__cache = {}

def init(dbloc = __default_dbbloc):
    global __dbloc
    #check if the location is correct
    if not exists(dbloc): raise PMException("Missing database at {location}".format(location=dbloc))
    __dbloc = dbloc

def get_timeseries(full_ticker:str, datapoint_name:str, fill_method=fill.FORWARDFILL, use_cache=True)->TimeSeries:
    '''
    Return the time series of a data point. 
    Parameters:
    full_ticker: concatenation of the ticker and country code
    datapoint_name: Supported data points are:
        . adjusted_close
        . close
        . high
        . low
        . open
        . volume
    Raises an exception if the time series cannot be loaded. Cannot return None.
    '''
    global __dbloc

    try:
        if use_cache and (full_ticker+"_"+datapoint_name in __cache):
            return __cache[full_ticker+"_"+datapoint_name]
        # read it from the database
        (ticker, exchange) = full_ticker.split('.')
        name = datapoint_name
        path = os.path.join(__dbloc, exchange, ticker, name)
        a = np.load(path+'.npy')
        #Read start and end dates
        path = os.path.join(__dbloc, exchange, ticker)
        with open(os.path.join(path, datapoint_name+".meta")) as metafile:
            meta = json.load(metafile)
            start_date = datetime.strptime(meta["base_date"], '%Y-%m-%d')
            end_date = datetime.strptime(meta["last_date"], '%Y-%m-%d')

        # Create the time series intance to return
        toreturn:TimeSeries =  TimeSeries(a, start_date.date(), end_date.date(), fill_method)
        if use_cache:
            __cache[full_ticker+"_"+datapoint_name] = toreturn
        return toreturn

    except FileNotFoundError:
        raise PMException("Could not find time series for ticker {full_ticker}".format(full_ticker = full_ticker))

def get_ticker(full_ticker:str)->Ticker:
    #read ticker details from datbase
    (ticker, exchange) = full_ticker.split('.')
    idfile = os.path.join(__dbloc, exchange, ticker, "id")
    with open(idfile) as idf:
        td = json.load(idf)
    return Ticker(type=td['Type'], code=td['Code'], isin=td['Isin'], name=td['Name'], country=td['Country'], exchange=td['Exchange'], currency=td['Currency'])


class UnitTestData(unittest.TestCase):
    def test_get_timeseries(self):
        ts:TimeSeries = get_timeseries('GT.US', 'open')
        print(ts)
        ts2:TimeSeries = get_timeseries('GT.US', 'open')
        print(ts2)
        self.assertEqual(ts, ts2)
        ts3:TimeSeries = ts.cutndays(date(2020,1,1), 10)
        ts4:TimeSeries = ts.cut2dates(date(2020,1,1), date(2020,1,10))
        self.assertEqual(ts3, ts4)

    def test_get_ticker(self):
        t:Ticker = get_ticker('GT.US')
        self.assertEqual(t.code, 'GT')
        self.assertEqual(t.country, 'USA')
        self.assertEqual(t.currency, 'USD')
        self.assertEqual(t.exchange,'NASDAQ')
        self.assertEqual(t.isin, 'US3825501014')
        self.assertEqual(t.name, 'Goodyear Tire & Rubber Co')
        self.assertEqual(t.type, 'Common Stock')

if __name__ == '__main__':
    init()
    unittest.main()
