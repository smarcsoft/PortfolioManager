import datetime
import json
import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(),'..','utils'))
from eod import EodHistoricalData
import logging
import logging.config
import logging.handlers
from config import get_config, process_arguments


logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('fdfeeder')

__stats=[]
number_of_currencies_to_process=0

__config_file = "config/pm.conf"

def get_oed_apikey(config:str=__config_file) -> str:
    return get_config('EOD_API_KEY', configfile=config)


def __reset_stats():
    __stats=[]


def __display_stats(logger):
    logger.info("Number of currencies processed:{ccy_number}/{total_ccy_number}".format(ccy_number = len(__stats), total_ccy_number = number_of_currencies_to_process))

def __store_fx_data(currency:str,  fx_data:dict):
    '''
    Stores the fundamental data of the ticker passed in arguments.

    Arguments:
    . exchange: Exchange code
    . ticker: ticker code (not fully qualified with the exchange)
    . fundamental_data: dictionary to store

    '''
    #Check if file exists
    db_loc = get_config('DB_LOCATION', configfile=__config_file)
    file_loc = os.path.join(db_loc, currency)
    #create directories if missing
    os.makedirs(file_loc, exist_ok=True) 
    with open(file_loc+"/"+currency+'.json', 'wt') as fd:
        fd.write(json.dumps(fx_data))


def display_stats():
    logger = logging.getLogger("summary")
    logger.setLevel(logging.INFO)
    d = datetime.datetime.now()
    handler = logging.FileHandler(get_config("LOG_FILE_LOC", configfile=__config_file)+"/fxfeeder_run_{yyyy}-{mm:02d}-{dd:02d}_{hh:02d}_{mmm:02d}_{ss:02d}.log".format(yyyy=d.year, mm=d.month, dd=d.day, hh=d.hour, mmm=d.minute, ss=d.second))
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    __display_stats(logger)
    
    
def update_stats(ccy:str):
    __stats.append(ccy)

def process_currency(client, ccy:str):
    ts = client.get_prices_eod(ccy.upper()+".FOREX")
    __store_fx_data(ccy, ts)
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

def run_forex_data_feeder(configfile:str):
    '''
    Run the feeder for the list of exchanges passed in argument
    Each element of the list is just a list of exchange codes
    '''
    api_key = get_oed_apikey(configfile)
    client = EodHistoricalData(api_key)
    update_db(client, get_config("CURRENCIES"))
    display_stats()

if __name__ == '__main__':
    try:
        exchange_list,configfile,update = process_arguments()
        run_forex_data_feeder(configfile)
    except Exception as e:
        print("Fatal error:", str(e))
        __logger.exception("Fatal error:%s", str(e))