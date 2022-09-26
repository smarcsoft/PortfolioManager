from datetime import date, datetime
from genericpath import exists
import os
import numpy as np
import json
from TimeSeries import fill, TimeSeries, PMException
from Ticker import Ticker

if 'DB_LOCATION' in os.environ:
    __default_dbbloc = os.environ['DB_LOCATION']
else:
    __default_dbbloc = "backend/db"
__dbloc = __default_dbbloc

def init(dbloc = __default_dbbloc):
    global __dbloc
    #check if the location is correct
    if not exists(dbloc): raise PMException("Missing database at {location}".format(location=dbloc))
    __dbloc = dbloc

def get_timeseries(full_ticker:str, datapoint_name:str, start_date:date=None, end_date:date=None, fill_method=fill.FORWARDFILL)->TimeSeries:
    global __dbloc

    try:
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
        return TimeSeries(a, start_date.date(), end_date.date(), fill_method)
    except FileNotFoundError:
        raise PMException("Could not find time series for ticker {full_ticker}".format(full_ticker = full_ticker))

def get_ticker(full_ticker:str)->Ticker:
    #read ticker details from datbase
    (ticker, exchange) = full_ticker.split('.')
    idfile = os.path.join(__dbloc, exchange, ticker, "id")
    with open(idfile) as idf:
        td = json.load(idf)
    return Ticker(type=td['Type'], code=td['Code'], isin=td['Isin'], name=td['Name'], country=td['Country'], exchange=td['Exchange'], currency=td['Currency'])

if __name__ == '__main__':
    init()
    ts = get_timeseries('GT.US', "open")
    print(ts)
    print("First 10 days of Jan 2020")
    ts1 = ts.cutndays(date(2020,1,1), 10)
    print(ts1)
    ts2 = ts.cut2dates(date(2020,1,1), date(2020,1,10))
    print(ts2)
    print(ts1==ts2)
    t = get_ticker('GT.US')
    print(t)