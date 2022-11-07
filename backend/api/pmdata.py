from datetime import date, datetime
from genericpath import exists
import os
import unittest
import numpy as np
import json
from TimeSeries import fill, TimeSeries, PMException
from FundamentalData import FundamentalData
from PositionIdentifier import Ticker
from feedutils import get_database, set_database


TimeSeriesCache = dict[str, TimeSeries] # FullyQualifiedTicker_DataPointName, timeseries
TickerCache = dict[str, dict[str, Ticker]] # Dictionary of (market, dictionary of (symbol name, Ticker)) for quick lookup by name

__cache = {}
__tickercache = {}

def init(database_location:str = None):
    if(database_location != None): set_database(database_location)
    location = get_database()
    #check if the location is correct
    if not exists(location): raise PMException("Missing database at {location}".format(location=location))
    __init_ticker_cache()


def search(symbol_name:str, market:str='US', type:str = "Common Stock")->list[Ticker]:
    if not __tickercache:
        __init_ticker_cache(market)
    if not __tickercache[market]:
        __init_ticker_cache(market)
    names = __tickercache[market].keys()
    # Find the name in names
    matching_names = [name for name in names if symbol_name.lower() in name.lower()]
    return [__tickercache[market][name] for name in matching_names if __tickercache[market][name].type.lower()==type.lower()]

def __init_ticker_cache(exchange:str='US'):
    if exchange not in __tickercache:
        __tickercache[exchange] = {}
    path = os.path.join(get_database(), exchange)
    # Read all directory entries as tickers
    for ticker in os.listdir(path=path):
        # Read symbol name
        with open(os.path.join(path, ticker, 'id')) as idfile:
            identity = json.load(idfile)
            __tickercache[exchange][identity["Name"]] = Ticker(ticker, exchange, isin=identity["Isin"], name=identity["Name"], type=identity["Type"])

def get_fundamental_data(full_ticker:str)->FundamentalData:
    return FundamentalData.load(full_ticker)


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
    try:
        if use_cache and (full_ticker+"_"+datapoint_name in __cache):
            return __cache[full_ticker+"_"+datapoint_name]
        # read it from the database
        (ticker, exchange) = full_ticker.split('.')
        name = datapoint_name
        path = os.path.join(get_database(), exchange, ticker, name)
        a = np.load(path+'.npy')
        #Read start and end dates
        path = os.path.join(get_database(), exchange, ticker)
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
    idfile = os.path.join(get_database(), exchange, ticker, "id")
    with open(idfile) as idf:
        td = json.load(idf)
    return Ticker(type=td['Type'], code=td['Code'], isin=td['Isin'], name=td['Name'], country=td['Country'], exchange=td['Exchange'], currency=td['Currency'])


class UnitTestData(unittest.TestCase):
    def test_get_timeseries(self):
        ts:TimeSeries = get_timeseries('GT.US', 'open')
        ts2:TimeSeries = get_timeseries('GT.US', 'open')
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

    def test_multiple_search(self):
        self.assertEqual(len(search("MICRO")), 43)
    
    def test_hot_search(self):
        self.assertEqual(len(search("MICROSOFT")), 1)

if __name__ == '__main__':
    init()
    unittest.main()
