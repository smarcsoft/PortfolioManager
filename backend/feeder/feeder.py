from urllib import request
from urllib.error import HTTPError
from eod import EodHistoricalData
import logging
import logging.config
import os
import json
import math

__config = {}
logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('feeder')


def __parse_line(line:str):
    keyval = line.split('=')
    return(keyval[0], keyval[1])

def __read_configuration():
    config = {}
    __logger.info("Reading configuration file config/pm.conf...")
    with open("config/pm.conf", "rt") as configfile:
        for line in configfile:
            if not line.strip().startswith('#'):
                (key,value) = __parse_line(line)
                __logger.debug("Found %s -> %s", key, value)
                config[key.strip()] = value.strip()
    return config



def get_config(key:str)->str:
    '''
    Read the configuration file is needed and return the entry identified by key.

    Returns an empty string if the key is not found.

    Assumes the current directory is the parent on the config directory.
    '''
    global __config
    if __config: 
        return __config[key]
    else:
        __config = __read_configuration()
        if not __config: return ""
        return __config[key]



def get_oed_apikey() -> str:
    return get_config('EOD_API_KEY')

def __updatedb_exchange(exchange):
    #Check if the directory exists and if not create it
    db_loc = get_config('DB_LOCATION')
    tocreate = os.path.join(db_loc, exchange['Code'])
    if not os.path.exists(tocreate):
        # Create the directory
        __logger.info("Creating exchange %s in the database", exchange['Code'])
        os.mkdir(tocreate)
        # Create id file
        with open(tocreate+'/id', 'wt') as id:
            id.write(str(exchange))

def __updatedb_tickers(exchange, symbol):
    try:
        __logger.debug("Updating database for exchange %s and ticker %s", exchange['Code'], symbol['Code'])
        #__logger.debug(str(symbol))
        db_loc = get_config('DB_LOCATION')
        exchange_loc = os.path.join(db_loc, exchange['Code'])
        ticker_loc = os.path.join(exchange_loc, symbol['Code'])
        if not os.path.exists(ticker_loc):
            #Create the ticker directory
            __logger.debug("Creating ticker %s in the database for exchange %s", symbol['Code'], exchange['Code'])
            os.mkdir(ticker_loc)
            # Create id file
            with open(ticker_loc+'/id', 'wb') as id:
                towrite = json.dumps(symbol, ensure_ascii=False)
                id.write(towrite.encode('utf-8'))
    except OSError:
        __logger.error("Could not process ticker %s on exchange %s. Ignoring...", symbol['Code'], exchange['Code'])

def build_initial_db(client):
    # Get the list of exchanges
    __logger.info("Getting the list of exchanges...")
    exchanges = client.get_exchanges()
    __logger.info("%d exchanges retrieved", len(exchanges))
    for exchange in exchanges:
        __updatedb_exchange(exchange)
        # For each exchange, get the list of tickers
        __logger.info("Getting the ticker list for exchange %s", exchange['Code'])
        try:
            symbols = client.get_exchange_symbols(exchange=exchange['Code'])
            __logger.info("%d symbols retrieved for exchange %s", len(symbols), exchange['Code'])
            progress = 0
            steps = math.ceil(len(symbols)/10)
            for symbol in symbols:
                progress+=1
                __updatedb_tickers(exchange, symbol)
                if (steps != 0) and (progress % steps == 0):
                    __logger.info("%d%% processed...", progress / steps * 10)
        except Exception as e:
            __logger.error("!!! Could not process exchange %s !!! -> %s", exchange['Code'], str(e))
    # Build the directory tree
    # For each ticker, get the eod data
    # Create a subtree for each data point

EOD_API_KEY = get_oed_apikey()
client = EodHistoricalData(EOD_API_KEY)
build_initial_db(client)