from datetime import date, datetime
from genericpath import exists
from glob import glob
import os
import unittest
import numpy as np
import json
from TimeSeries import fill, TimeSeries, PMException
from FundamentalData import FundamentalData
from PositionIdentifier import Ticker
from feedutils import get_equity_database, get_fx_database, set_database

__date_format = '%Y-%m-%d'

TimeSeriesCache = dict[str, TimeSeries] # FullyQualifiedTicker_DataPointName, timeseries
TickerCache = dict[str, dict[str, Ticker]] # Dictionary of (market, dictionary of (symbol name, Ticker)) for quick lookup by name

DEFAULT_CURRENCY_DATAPOINT="adjusted_close"

__cache = {}
__tickercache = {}

def init(database_location:str = None):
    if(database_location != None): set_database(database_location)
    location = get_equity_database()
    #check if the location is correct
    if not exists(location): raise PMException("Missing database at {location}".format(location=location))
    __init_ticker_cache()

def get_symbol_types():
    '''
    Browse the database to extract the distinct list of symbol types.
    Supported ticker types:
    ['ETF', 'Note', 'FUND', 'Common Stock', 'Mutual Fund', 'ETC', 'INDEX', 'Preferred Stock']
    '''
    tickers = __get_tickers_for_market()
    return list(set([ticker.type for ticker in tickers]))

def search(symbol_name:str, market:str='', type:str = "Common Stock")->list[Ticker]:
    '''
    Searches for the instrument containing symbol_name in its name for the market specified
    Arguments:
    symbol_name: the symbol, or part of the symbol name (not ticker) to look for
    market: '' for all markets (which is the default) or the exchange (such as 'US' or 'SW')
    type: the types of symbol to look for. See the results of get_symbol_types()
    '''
    if not __tickercache:
        __init_ticker_cache()
    tickers = __get_tickers_for_market(market)
    # Find the name in names
    matching_tickers = [ticker for ticker in tickers if (symbol_name.lower() in ticker.name.lower()) and (type.lower() in ticker.type.lower())]
    return matching_tickers

def search_isin(isin:str, market:str='')->list[Ticker]:
    '''
    Searches for the instrument containing symbol_name in its name for the market specified
    Arguments:
    symbol_name: the symbol, or part of the symbol name (not ticker) to look for
    market: '' for all markets (which is the default) or the exchange (such as 'US' or 'SW')
    type: the types of symbol to look for. See the results of get_symbol_types()
    '''
    if not __tickercache:
        __init_ticker_cache()
    tickers = __get_tickers_for_market(market)
    # Find the name in names
    matching_tickers = [ticker for ticker in tickers if (ticker.isin != None) and (isin.lower() in ticker.isin.lower())]
    return matching_tickers

def __get_tickers_for_market(market:str='')->list:
    if(len(market)!=0):
        return __tickercache[market].values()
    else:
        #union of all symbols for all markets
        toreturn = []
        for exchange in __tickercache.keys():
            toreturn.extend(__tickercache[exchange].values())
        return toreturn

            


def __init_ticker_cache():
    exchanges = __get_all_exchanges()
    for exchange in exchanges:
        if exchange not in __tickercache:
            __tickercache[exchange] = {}
        # Load the universe file
        path = os.path.join(get_equity_database(), exchange)
        tickers=[]
        with open(os.path.join(path, "universe.json")) as universefile:
            tickers=json.load(universefile)
        for ticker in tickers:
            __tickercache[exchange][ticker["Name"]] = Ticker(ticker["Code"], exchange, isin=ticker["Isin"], name=ticker["Name"], type=ticker["Type"])
       
def __get_all_exchanges():
    return [f.name for f in os.scandir(get_equity_database()) if f.is_dir()]

def get_fundamental_data(full_ticker:str)->FundamentalData:
    return FundamentalData.load(full_ticker)

def get_fx_timeseries(currency:str, datapoint_name:str=DEFAULT_CURRENCY_DATAPOINT ,fill_method=fill.FORWARDFILL, use_cache=True)->TimeSeries:
    try:
        if use_cache and (currency+"_"+datapoint_name in __cache):
            return __cache[currency+"_"+datapoint_name]
        # read it from the database
        path = os.path.join(get_fx_database(), currency, datapoint_name)
        a = np.load(path+'.npy')
        #Read start and end dates
        path = os.path.join(get_fx_database(),currency)
        with open(os.path.join(path, datapoint_name+".meta")) as metafile:
            meta = json.load(metafile)
            start_date = datetime.strptime(meta["base_date"], __date_format)
            end_date = datetime.strptime(meta["last_date"], __date_format)

        # Create the time series intance to return
        toreturn:TimeSeries =  TimeSeries(a, start_date.date(), end_date.date(), fill_method)
        if use_cache:
            __cache[currency+"_"+datapoint_name] = toreturn
        return toreturn

    except FileNotFoundError:
        raise PMException("Could not find time series for currency {currency}".format(currency = currency))

def get_fx(currency:str, fx_date:date, datapoint_name:str=DEFAULT_CURRENCY_DATAPOINT, fill_method=fill.FORWARDFILL, use_cache=True):
    return get_fx_timeseries(currency, datapoint_name, fill_method, use_cache).get(fx_date)
    

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
        path = os.path.join(get_equity_database(), exchange, ticker, name)
        a = np.load(path+'.npy')
        #Read start and end dates
        path = os.path.join(get_equity_database(), exchange, ticker)
        with open(os.path.join(path, datapoint_name+".meta")) as metafile:
            meta = json.load(metafile)
            start_date = datetime.strptime(meta["base_date"], __date_format)
            end_date = datetime.strptime(meta["last_date"], __date_format)

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
    idfile = os.path.join(get_equity_database(), exchange, ticker, "id")
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

    def test_msci_timeseries(self):
        ts:TimeSeries = get_timeseries("MSCI.US", "close")
        #Take the 1st of September value
        value = ts.get(date(2022,9,1))
        self.assertAlmostEqual(value, 456, delta=1)

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
        self.assertEqual(len(search("MICRO")), 44)
    
    def test_hot_search(self):
        self.assertEqual(len(search("MICROSOFT")), 1)

    def test_hot_search2(self):
        self.assertEqual(len(search("Property", "US")), 36)
        self.assertEqual(len(search("Property")), 39)

    def test_get_symbol_types(self):
        self.assertEqual(len(get_symbol_types()), 8)

    def test_currency(self):
        self.assertAlmostEqual(get_fx_timeseries("EUR")[0], 0.99, delta=0.01)
        self.assertAlmostEqual(get_fx_timeseries("EUR").get(date(2022,11,8)), 0.9981, delta = 0.001)

    def test_search_isin(self):
        self.assertEqual(len(search_isin("US55354G1004")), 1)

    def test_crypto(self):
        self.assertAlmostEqual(get_fx_timeseries("BTC").get(date(2022,11,9)), 6.2969199843932e-05, delta = 1e-05)
        self.assertAlmostEqual(get_fx_timeseries("ETH").get(date(2022,11,9)), 1/1100, delta = 0.001)

if __name__ == '__main__':
    init()
    unittest.main()
