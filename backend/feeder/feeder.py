import argparse
from dataclasses import field
from urllib import request
from urllib.error import HTTPError
from urllib.parse import _NetlocResultMixinBytes
from eod import EodHistoricalData
import logging
import logging.config
import logging.handlers
import os
import json
import math
import datetime
import numpy as np
import pyodbc

__config = {}
logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('feeder')
__stats={}


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
    try:
        db_loc = get_config('DB_LOCATION')
        tocreate = os.path.join(db_loc, exchange['Code'])
        if not os.path.exists(tocreate):
            # Create the directory
            __logger.info("Creating exchange %s in the database", exchange['Code'])
            os.mkdir(tocreate)
            # Create id file
            with open(tocreate+'/id', 'wt') as id:
                id.write(str(exchange))
        __stats['Exchanges']['Processed'].append(exchange['Code'])
    except Exception as e:
        __logger.error("Could not process exchange %s -> %s", exchange['Code'], str(e))
        __stats['Exchanges']['Errors'].append(exchange['Code'])


def __updatedb_tickers(exchange):
    '''
    Update the database tree with the tickers for the exchange passed in argument
    
    Returns the list of tickers retrieved by the API
    '''
    # For each exchange, get the list of tickers
    __logger.info("Getting the ticker list for exchange %s", exchange['Code'])
    try:
        symbols = client.get_exchange_symbols(exchange=exchange['Code'])
        __logger.info("%d symbols retrieved for exchange %s", len(symbols), exchange['Code'])
        progress = 0
        steps = math.ceil(len(symbols)/10)
        for symbol in symbols:
            progress+=1
            __updatedb_ticker(exchange, symbol)
            if (steps != 0) and (progress % steps == 0):
                __logger.info("%d%% processed...", progress / steps * 10)
        return symbols
    except Exception as e:
        __logger.error("!!! Could not process exchange %s !!! -> %s", exchange['Code'], str(e))
        __stats['Exchanges']['Errors'].append(exchange['Code'])
        if exchange['Code'] in __stats['Exchanges']['Processed']: __stats['Exchanges']['Processed'].remove(exchange['Code']) 
        return []

def __update_stat_ticker_error(exchange:dict, symbol:dict, e:Exception):
    '''
    Update the __stats global dictionary to register the ticker in error with the message in exception e
    '''
    global __stats
    if exchange['Code'] not in __stats['Tickers']['Errors'].keys():
        __stats['Tickers']['Errors'][exchange['Code']] = []
    __stats['Tickers']['Errors'][exchange['Code']].append({'Code':symbol['Code'], 'Error':str(e)})

def __updatedb_ticker(exchange, symbol):
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
        __stats['Tickers']['Processed'].append(symbol['Code'])
    except Exception as e:
        __logger.error("Could not process ticker %s on exchange %s. Ignoring...", symbol['Code'], exchange['Code'])
        __update_stat_ticker_error(exchange, symbol, e)
        

def __reset_stats():
    #Each Exchange entry is {'Processed': [], 'Errors':[]}
    __stats['Exchanges'] = {'Processed':list(), 'Errors':list()}
    #Each Ticker entry is {'Processed': [(exchange, ticker_code)], 'Errors':{exchange:[{'Code':"", 'Error':""}]}}
    __stats['Tickers'] = {'Processed':list(), 'Errors':dict()}

def __display_stats_exchanges(stats, logger):
    exchange_success = len(stats['Exchanges']['Processed'])
    exchange_error = len(stats['Exchanges']['Errors'])
    logger.info("Number of exchanges successfully processed {success:d}/{total:d}".format(success = exchange_success, total = exchange_success + exchange_error))
    if(exchange_error != 0):
        logger.info("*** {failed:d} exchanges could not be processed:".format(failed = exchange_error))
        exchanges = ""
        for exchange_error in stats['Exchanges']['Errors']:
            exchanges = exchanges+exchange_error + ' - '
        logger.info(exchanges)

def __display_stats_tickers(stats, logger):
    tickers_success = len(stats['Tickers']['Processed'])
    #Calculate number of tickers failes
    tickers_failed = 0
    exchange_list = stats['Tickers']['Errors'].keys()
    for exchange in exchange_list:
        tickers_failed += len(stats['Tickers']['Errors'][exchange])
    
    total_tickers = tickers_success + tickers_failed
    percent_processed = 100.0
    if total_tickers != 0: percent_processed = tickers_success/(total_tickers)*100

    logger.info("Tickers processed {success:d}/{total:d} [{pct:.1f}%]".format(success = tickers_success, total = total_tickers, pct=percent_processed))
    #For each exchange where i have at least one ticker failed, display the issue
    for exchange in exchange_list:
        logger.info("Failure details for exchange {0}:".format(exchange))
        for ticker in stats['Tickers']['Errors'][exchange]:
            logger.info("{0:15} -> {1}".format(ticker['Code'],ticker['Error']))


def __create_meta_data_file(filename, data_point):
    s={}
    s['base_date'] = data_point['base_date']
    s['last_date'] = data_point['last_date']
    s['name'] = data_point['name']
    with open(filename,'w') as metafile:
        json.dump(s, metafile)


def __create_data_file(filename, data_point:np.ndarray):
    # Create the numpy array
    np.savez_compressed(filename, data_point)

def __feed_data_file(exchange, ticker, data_point):
    #Check if file exists
    db_loc = get_config('DB_LOCATION')
    exchange_loc = os.path.join(db_loc, exchange)
    ticker_loc = os.path.join(exchange_loc, ticker)
    meta_loc = os.path.join(ticker_loc,data_point['name']+".meta")
    data_loc = os.path.join(ticker_loc,data_point['name']+".npz")
    __create_meta_data_file(meta_loc,data_point)
    __create_data_file(data_loc,data_point['data'])

def __get_eod_field(prices:list, base_date:str, field_name:str, type:np.dtype)->np.ndarray:
    '''
    returns a ndarray containing the data point values.
    There is one element per date from the base date
    '''
    base_date = datetime.date.fromisoformat(base_date)
    to_date = datetime.date.fromisoformat(prices[len(prices)-1]['date'])
    number_of_elements = to_date - base_date 
    toreturn = np.zeros(number_of_elements.days+1, type)
    for price in prices:
        dp_date = datetime.date.fromisoformat(price['date'])
        index = (dp_date - base_date).days
        toreturn[index]= np.float32(price[field_name])
    return toreturn

def __pack_datapoint(dp:dict,fieldname:str,prices:list):
    '''
    Update the data point dictionary dp by adding the following keys:
    
    .base_date: The date of the oldest data point of the time series
    .last_date: The date of the most recent data point
    .name: The name of the field
    .data: a numpy array containing the data time series. Empty values are 0.0.

    Returns the dp dictionary containing the updated data point
    '''
    dp['base_date']=prices[0]['date']
    dp['last_date']=prices[len(prices)-1]['date']
    dp['name'] = fieldname
    dp['data'] = __get_eod_field(prices, dp['base_date'], fieldname, np.float32)
    return dp


def __feed_db_eodprices(client,exchange:dict, ticker:dict):
    '''
    Populate the database with end of day market data for the ticker belonging to this exchange 
    '''
    try:
        __logger.info("Fetching EOD prices for ticker %s from exchange %s", ticker['Code'], exchange['Code'])
        full_ticker= ticker['Code']+'.'+exchange['Code']
        prices = client.get_prices_eod(full_ticker)
        # Getting back [{date,open,high,low,close,adjusted_close,volume}]
        dp = {}
        if len(prices) >0 :
            dp=__pack_datapoint(dp,'open', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'close', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'high', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'low', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'adjusted_close', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'volume', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
    except Exception as e:
        __logger.error("Could not get eod data for ticker %s.%s->%s", ticker['Code'], exchange['Code'], str(e))
        __update_stat_ticker_error(exchange, ticker, e)


def display_stats(stats):
    logger = logging.getLogger("summary")
    logger.setLevel(logging.INFO)
    d = datetime.datetime.now()
    handler = logging.FileHandler(get_config("LOG_FILE_LOC")+"/feeder_run_{yyyy}-{mm:02d}-{dd:02d}_{hh:02d}_{mmm:02d}_{ss:02d}.log".format(yyyy=d.year, mm=d.month, dd=d.day, hh=d.hour, mmm=d.minute, ss=d.second))
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    __display_stats_exchanges(stats, logger)
    __display_stats_tickers(stats, logger)
    


def build_initial_db(client, exchange_list:list, sqlconnection):
    __reset_stats()
    exchanges=[]
    if len(exchange_list)==0:
        # Get the list of exchanges
        __logger.info("Getting the list of exchanges...")
        exchanges = client.get_exchanges()
        __logger.info("%d exchanges will be loaded in the database", len(exchanges))
    else:
        # Fetch each exchange details
        exchs = client.get_exchanges()
        for exchange_code in exchange_list:
            #Find the exchange code in the exchange list exchs
            es = [ex for ex in exchs if ex['Code']==exchange_code]
            if(len(es) != 0):
                exchanges.extend(es)

    for exchange in exchanges:
        __updatedb_exchange(exchange)
        tickers = __updatedb_tickers(exchange)
        for ticker in tickers:
            __feed_db_eodprices(client,exchange, ticker)
    # For each ticker, get the eod data
    # Create a subtree for each data point

def __process_arguments():
    '''
    Process the command line arguments

    Returns a list of exchanges to be processed.
    En empty list means all exchanges
    '''
    parser = argparse.ArgumentParser(description="Feed the database of the portfolio manager")
    parser.add_argument('--debug', '--log', '-d', nargs='?', choices=['DEBUG', 'INFO','WARN', 'ERROR','CRITICAL'], help="Enable debugging with the specified level")
    parser.add_argument('--exchanges', '-e', nargs='+', action="extend",type=str, help="Process the list of exchanges specified (by their codes)")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    args=parser.parse_args()
    debug_level = None
    if hasattr(args,"d"): debug_level = args.d 
    if hasattr(args,"debug"): debug_level = args.debug 
    if hasattr(args,"log"): debug_level = args.log 
    if debug_level != None:
        __logger.info("Debug level set to %s", debug_level.upper())
        __logger.setLevel(debug_level.upper())

    exchange_list=[]
    if hasattr(args,"e"): exchange_list = args.e 
    if hasattr(args,"exchanges"): exchange_list = args.exchanges 
    if len(exchange_list) != 0:
        __logger.info("Processing exchanges:%s",exchange_list)
    return exchange_list

def __connect_sql_db(): 
    '''
    Connects to SQL QB and return a connection or None if a connection cannot be established
    '''
    # Some other example server values are
    # server = 'localhost\sqlexpress' # for a named instance
    # server = 'myserver,port' # to specify an alternate port
    try:
        server = get_config("SQL_SERVER")
        database = get_config("SQL_DB")
        username = get_config("SQL_USER")
        password = get_config("SQL_PASSWORD") 
        connectionurl='DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password
        __logger.info("Connecting to database server with:%s", connectionurl)
        cnxn = pyodbc.connect(connectionurl)
        return cnxn
    except Exception as e:
        __logger.error("Cannot connect to SQL database:%s", str(e))
        return None

exchange_list = __process_arguments()
EOD_API_KEY = get_oed_apikey()
client = EodHistoricalData(EOD_API_KEY)
sqlconnection = __connect_sql_db()
#build_initial_db(client, exchange_list, sqlconnection)
#display_stats(__stats)