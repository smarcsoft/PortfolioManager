import datetime
import json
import sys
import os
import unittest
import numpy as np
from exceptions import FeederException
from eod import EodHistoricalData
import logging
import logging.config
import logging.handlers
from config import DEFAULT_CONFIG_FILE, DEFAULT_LOGGING_CONFIG_FILE, get_config, init_config, process_arguments

DATE_FORMAT = '%Y-%m-%d'

__stats=[]
number_of_currencies_to_process=0

def get_oed_apikey() -> str:
    return get_config('EOD_API_KEY')

def __reset_stats():
    __stats=[]

def __display_stats(logger):
    logger.info("Number of currencies processed:{ccy_number}/{total_ccy_number}".format(ccy_number = len(__stats), total_ccy_number = number_of_currencies_to_process))

def __store_fx_data(currency:str,  fx_data:list, fiat:bool):
    '''
    Stores the fundamental data of the ticker passed in arguments.

    Arguments:
    . exchange: Exchange code
    . ticker: ticker code (not fully qualified with the exchange)
    . fundamental_data: dictionary to store

    '''
    #Check if file exists
    db_loc = get_config('DB_LOCATION')
    file_loc = os.path.join(db_loc, "FX", currency.split('-')[0])
    #create directories if missing
    os.makedirs(file_loc, exist_ok=True) 

    # Create the meta file for each datapoint
    # Then create each numpy arrays
    (first, last, open, high, low, close, adjusted_close) = __create_arrays(fx_data, fiat)
    __store(file_loc, open, first, last, "open")
    __store(file_loc,high, first, last, "high")
    __store(file_loc,low, first, last, "low")
    __store(file_loc,close, first, last, "close")
    __store(file_loc,adjusted_close, first, last, "adjusted_close")


def __store(file_loc:str, v:np.ndarray, first:datetime.date, last:datetime.date, field:str):
    __store_meta(file_loc+"/"+field+'.meta',first, last, field)
    __store_data(v, file_loc+"/"+field+".npy")

def __store_data(v:np.ndarray, filename:str):
    if os.path.exists(filename):
        os.remove(filename)
    np.save(filename, v)


def __store_meta(filename:str, first:datetime.date, last:datetime.date, field:str):
    with open(filename, 'wt') as fd:
        towrite = dict()
        towrite["base_date"]=first.strftime(DATE_FORMAT)
        towrite["last_date"]=last.strftime(DATE_FORMAT)
        towrite["name"]=field
        fd.write(json.dumps(towrite))

def __create_arrays(fx_data:list, fiat:bool):
    start_date = datetime.datetime.strptime(fx_data[0]['date'], DATE_FORMAT).date()
    end_date = datetime.datetime.strptime(fx_data[len(fx_data) - 1]['date'], DATE_FORMAT).date()
    opening = np.zeros((end_date - start_date).days + 1)
    high = np.zeros((end_date - start_date).days + 1)
    low = np.zeros((end_date - start_date).days + 1)
    close = np.zeros((end_date - start_date).days + 1)
    adjusted_close = np.zeros((end_date - start_date).days + 1)
    (opening, high, low, close, adjusted_close) = __fill_array(fx_data, start_date, opening, high, low, close, adjusted_close, fiat)
    return (start_date, end_date, opening, high, low, close, adjusted_close)

def __fill_array(fx_data:list, start_date:datetime.date, open:np.ndarray, high:np.ndarray, low:np.ndarray, close:np.ndarray, adjusted_close:np.ndarray, fiat:bool):
    for fx in fx_data:
        date = datetime.datetime.strptime(fx['date'], DATE_FORMAT).date()
        #Get the index in the array
        index = (date - start_date).days
        if(fiat):
            open[index]=fx["open"]
            high[index]=fx["high"]
            low[index]=fx["low"]
            close[index]=fx["close"]
            adjusted_close[index]=fx["adjusted_close"]
        else:
            open[index]=1/fx["open"]
            high[index]=1/fx["high"]
            low[index]=1/fx["low"]
            close[index]=1/fx["close"]
            adjusted_close[index]=1/fx["adjusted_close"]
    return (open, high, low, close, adjusted_close)

def update(fx:dict, v:np.ndarray, field:str, index):
    v[index]=fx[field]


def display_stats():
    logger = logging.getLogger("summary")
    logger.setLevel(logging.INFO)
    d = datetime.datetime.now()
    handler = logging.FileHandler(get_config("LOG_FILE_LOC")+"/fxfeeder_run_{yyyy}-{mm:02d}-{dd:02d}_{hh:02d}_{mmm:02d}_{ss:02d}.log".format(yyyy=d.year, mm=d.month, dd=d.day, hh=d.hour, mmm=d.minute, ss=d.second))
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    __display_stats(logger)
    
    
def update_stats(ccy:str):
    __stats.append(ccy)

def process_currency(client, ccy:str):
    __logger.info("Processing currency " + ccy)
    ts = client.get_prices_eod(ccy.upper()+".FOREX")
    __store_fx_data(ccy, ts, True)
    update_stats(ccy)

def process_crypto_currency(client, ccy:str):
    ts = client.get_prices_eod(ccy.upper()+".CC")
    __store_fx_data(ccy, ts, False)
    update_stats(ccy)


def update_db(client, currencies:str):
    '''
    Populate the file database with FX data
    Arguments are:
    . client: API client of the market data API
    '''
    global number_of_currencies_to_process

    __reset_stats()
    #Get the list of currencies
    ccys = currencies.split(',')
    number_of_currencies_to_process = len(ccys)
    for ccy in ccys:
        try:
            process_currency(client, ccy)
        except Exception as e:
            __logger.error("Could not process currency {currency}:{message}".format(currency=ccy, message=str(e)))

def update_db_cryptos(client, currencies:str):
    '''
    Populate the file database with crypto data
    Arguments are:
    . client: API client of the market data API
    . comma separated list of currencies to process
    '''
    global number_of_currencies_to_process

    __reset_stats()
    #Get the list of currencies
    ccys = currencies.split(',')
    number_of_currencies_to_process += len(ccys)
    for ccy in ccys:
        try:
            process_crypto_currency(client, ccy)
        except Exception as e:
            __logger.error("Could not process currency {currency}:{message}".format(currency=ccy, message=str(e)))

def run_forex_data_feeder():
    '''
    Run the feeder for the list of exchanges passed in argument
    Each element of the list is just a list of exchange codes
    '''
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    update_db(client, get_config("CURRENCIES"))
    update_db_cryptos(client, get_config("CRYPTO_CURRENCIES"))
    display_stats()

def init(logger = None, configfile:str=DEFAULT_CONFIG_FILE):
    global __logger
    if(logger != None):
        __logger = logger
    else:
        init_config(None, configfile)
        # Get the logging subsystem configuration 
        log_conf_file_loc = get_config("LOGGING_CONFIGURATION")
        if(len(log_conf_file_loc) == 0):
            #Fall back to detault
            log_conf_file_loc = DEFAULT_LOGGING_CONFIG_FILE
        if(os.path.exists(log_conf_file_loc)):
            logging.config.fileConfig(log_conf_file_loc)
            __logger = logging.getLogger('feeder')
        else:
            raise FeederException("Cannot initialize logging subsystem with " + log_conf_file_loc+": The file does not exist")

class UnitTestFXFeeder(unittest.TestCase):
    def setUp(self):
        init(None, "tests/config/pm.conf")
    
    def test_fx_load(self):
        run_forex_data_feeder()
        self.assertTrue(True)


if __name__ == '__main__':
    try:
        exchange_list,configfile,update = process_arguments()
        init(None, configfile)
        run_forex_data_feeder()
    except Exception as e:
        print("Fatal error:", str(e))
        __logger.exception("Fatal error:%s", str(e))