import sys
import os
from xmlrpc.client import boolean
sys.path.append(os.getcwd())
import argparse
from dataclasses import field
from decimal import Decimal
from urllib import request
from urllib.error import HTTPError
from urllib.parse import _NetlocResultMixinBytes
from eod import EodHistoricalData
import logging
import logging.config
import logging.handlers
import json
import math
import datetime
import numpy as np
import pyodbc
from config import get_config, process_arguments

class FeederException(Exception): pass

logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('feeder')

#Stats is a complex data structure grouping all statistics of the feeding process
# {"Exchanges", "Tickers"}
# Exchanges: {"Processed, Errors"}
# Exchanges{"Processed"} ->["Code-Part"]: Processed is a list of successfully processed exchange parts
# Exchanges{"Errors"} -> ["Code-Part"]: Errors is a list of errorneous exchange (part) loads

# Tickers: {"Processed, Errors"}
# Tickers  {"Processed"} ->["Code"]: Processed is a list of successfully processed fully qualified tickers
# Tickers{"Errors"} -> [{"code-part:[]"}]: Errors is a list of dict with exchangecode-part being the key and the list of {"Code" (fully qualified ticker code), "Error" (error strings)} as values
__stats={}

__config_file = "config/pm.conf"

def get_oed_apikey() -> str:
    return get_config('EOD_API_KEY', configfile=__config_file)

def __updatedb_exchange(exchange):
    #Check if the directory exists and if not create it
    try:
        db_loc = get_config('DB_LOCATION', configfile=__config_file)
        tocreate = os.path.join(db_loc, exchange['Code'])
        if not os.path.exists(tocreate):
            # Create the directory
            __logger.info("Creating exchange %s in the database", exchange['Code'])
            os.mkdir(tocreate)
            # Create id file
            with open(tocreate+'/id', 'wt') as id:
                id.write(str(exchange))
        __stats['Exchanges']['Processed'].append(exchange['Code']+'-'+ str(exchange['Part']))
    except Exception as e:
        __logger.error("Could not process exchange %s part %d -> %s", exchange['Code'], exchange['Part'],str(e))
        __stats['Exchanges']['Errors'].append(exchange['Code']+'-'+str(exchange['Part']))


def __get_tickers(symbols:list, exchange):
    if exchange['Size'] == -1: return symbols
    #Filter for the subexchnage
    return symbols[exchange['Start']:exchange['Start']+exchange['Size']]

def __updatedb_tickers(exchange,client):
    '''
    Update the database tree with the tickers for the exchange passed in argument
    
    Returns the list of tickers retrieved by the API
    '''
    # For each exchange, get the list of tickers
    __logger.info("Getting the ticker list for exchange %s", exchange['Code'])
    try:
        symbols = client.get_exchange_symbols(exchange=exchange['Code'])
        symbols = __get_tickers(symbols, exchange)
        __logger.info("%d symbols retrieved for exchange %s part %d", len(symbols), exchange['Code'],exchange['Part'] )
        progress = 0
        steps = math.ceil(len(symbols)/10)
        for symbol in symbols:
            progress+=1
            __updatedb_ticker(exchange, symbol)
            if (steps != 0) and (progress % steps == 0):
                __logger.info("%d%% processed...", progress / steps * 10)
        return symbols
    except Exception as e:
        __logger.error("!!! Could not process exchange %s part %d !!! -> %s", exchange['Code'], exchange['Part'], str(e))
        __stats['Exchanges']['Errors'].append(exchange['Code']+'-'+str(exchange['Part']))
        if exchange['Code']+'-'+str(exchange['Part']) in __stats['Exchanges']['Processed']: __stats['Exchanges']['Processed'].remove(exchange['Code']+'-'+str(exchange['Part'])) 
        return []

def __update_stat_ticker_error(exchange:dict, symbol:dict, e:Exception):
    '''
    Update the __stats global dictionary to register the ticker in error with the message in exception e
    '''
    global __stats
    if exchange['Code']+'-'+str(exchange['Part']) not in __stats['Tickers']['Errors'].keys():
        __stats['Tickers']['Errors'][exchange['Code']+'-'+str(exchange['Part'])] = []
    __stats['Tickers']['Errors'][exchange['Code']+'-'+str(exchange['Part'])].append({'Code':symbol['Code']+'.'+exchange['Code'], 'Error':str(e)})

def __updatedb_ticker(exchange, symbol):
    try:
        __logger.debug("Updating database for exchange %s and ticker %s", exchange['Code'], symbol['Code'])
        #__logger.debug(str(symbol))
        db_loc = get_config('DB_LOCATION', configfile=__config_file)
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
        __stats['Tickers']['Processed'].append(symbol['Code']+'.'+exchange['Code'])
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
    logger.info("Number of exchanges (or parts) successfully processed {success:d}/{total:d}".format(success = exchange_success, total = exchange_success + exchange_error))
    if(exchange_error != 0):
        logger.info("*** {failed:d} exchanges (or parts) could not be processed:".format(failed = exchange_error))
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

def __update_meta_date_in_sqldb(connection:pyodbc.Connection, load_id:Decimal, start_date:str, end_date:str, ticker:str, dp_name:str):
    try:
        with connection:
                cursor = connection.cursor()
                load_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                __logger.debug("Inserting ticker load meta data for %s.%s...", ticker, dp_name)
                cursor.execute("SET NOCOUNT ON;INSERT INTO TickerLoad (exchange_load_id, ticker_code, data_point_name, start_date, end_date, load_time) VALUES (?,?,?,?,?,?)",
                load_id, ticker, dp_name, start_date, end_date, load_time)
                #get the load_id back
                __logger.debug('...Successfully Inserted')
    except Exception as e:
        __logger.error("Failed: %s", str(e))


def __feed_data_file(exchange:str, ticker:str, data_point:dict, connection:pyodbc.Connection, load_id:Decimal):
    '''
    Creates (and creates only, does not support update) the data point file in the DB
    Updates the relational database PMFeeder with the meta data of the load (start and end dates...) if the connetion is not None
    '''
    #Check if file exists
    db_loc = get_config('DB_LOCATION', configfile=__config_file)
    exchange_loc = os.path.join(db_loc, exchange)
    ticker_loc = os.path.join(exchange_loc, ticker)
    meta_loc = os.path.join(ticker_loc,data_point['name']+".meta")
    data_loc = os.path.join(ticker_loc,data_point['name']+".npz")
    __create_meta_data_file(meta_loc,data_point)
    __create_data_file(data_loc,data_point['data'])
    start_date = data_point['base_date']
    end_date = data_point['last_date']
    if connection != None:
        __update_meta_date_in_sqldb(connection, load_id, start_date, end_date, ticker, data_point['name'])

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


def __feed_db_eodprices(client,exchange:dict, ticker:dict, connection, load_id:Decimal):
    '''
    Populate the database with end of day market data for the ticker belonging to this exchange (or subexchange)
    '''
    try:
        __logger.info("Fetching EOD prices for ticker %s from exchange %s", ticker['Code'], exchange['Code'])
        full_ticker= ticker['Code']+'.'+exchange['Code']
        prices = client.get_prices_eod(full_ticker)
        # Getting back [{date,open,high,low,close,adjusted_close,volume}]
        dp = {}
        if len(prices) >0 :
            dp=__pack_datapoint(dp,'open', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp, connection, load_id)
            dp=__pack_datapoint(dp,'close', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp, connection, load_id)
            dp=__pack_datapoint(dp,'high', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp, connection, load_id)
            dp=__pack_datapoint(dp,'low', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp, connection, load_id)
            dp=__pack_datapoint(dp,'adjusted_close', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp, connection, load_id)
            dp=__pack_datapoint(dp,'volume', prices)
            __feed_data_file(exchange['Code'], ticker['Code'], dp, connection, load_id)
    except Exception as e:
        __logger.error("Could not get eod data for ticker %s.%s->%s", ticker['Code'], exchange['Code'], str(e))
        __update_stat_ticker_error(exchange, ticker, e)


def display_stats(stats):
    logger = logging.getLogger("summary")
    logger.setLevel(logging.INFO)
    d = datetime.datetime.now()
    handler = logging.FileHandler(get_config("LOG_FILE_LOC", configfile=__config_file)+"/feeder_run_{yyyy}-{mm:02d}-{dd:02d}_{hh:02d}_{mmm:02d}_{ss:02d}.log".format(yyyy=d.year, mm=d.month, dd=d.day, hh=d.hour, mmm=d.minute, ss=d.second))
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    __display_stats_exchanges(stats, logger)
    __display_stats_tickers(stats, logger)
    
def __init_load(exchange:dict, sqlconnection:pyodbc.Connection)->Decimal:
    '''
    Insert a new load into ExchangeLoad
    Returns the newly inserted load id or -1 if error
    '''
    try:
        __logger.debug("Inserting load in database...")
        with sqlconnection:
            cursor = sqlconnection.cursor()
            cursor.execute("SET NOCOUNT ON;INSERT INTO ExchangeLoad (code, part, load_time) VALUES (?,?,?);SELECT @@IDENTITY as exchange_load_id;",exchange['Code'], exchange['Part'], datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            #get the load_id back
            rows = cursor.fetchall()
            exch_id= rows[0].exchange_load_id
            __logger.debug('...Successfully Inserted with new id %d', exch_id)
            return exch_id
    except Exception as e:
        __logger.error("Failed: %s", str(e))
        return -1        


def __populate_exchanges(client, sqlconnection, exchanges:dict):
    '''
    Feed the database(s) with the exchanges market data
    '''
    for exchange in exchanges:
        if exchange['Size'] == -1:
            __logger.info("Populating database for full exchange %s", exchange['Code'])
        else:
            __logger.info("Populating database for exchange %s part %d (%d tickers)", exchange['Code'], exchange['Part'], exchange['Size'])
        __updatedb_exchange(exchange)
        tickers = __updatedb_tickers(exchange,client)
        if (len(tickers) >0) and (sqlconnection != None):
            load_id = __init_load(exchange, sqlconnection)
        for ticker in tickers:
            __feed_db_eodprices(client,exchange, ticker, sqlconnection, load_id)


def build_initial_db(client, exchange_list:list, sqlconnection):
    '''
    Populate the file database and SQL server meta database
    Arguments are:
    . client: API client of the market data API
    . exchange_list: List of exchanges to populate
    Each element of the list is tuple (code, size, part, start) where:
        . code is the exchange code
        . size is the size of the exchange (or -1 if not available)
        . part the part (1-based) of the exchange universe to populate
        . start the starting index (0-based) of the first ticker of the part from the universe to populate

    Example for a full exchange universe to populate:
       ('IL',-1 ,1 ,0)
    Example for part 5 of an exchange to populate:
        ('US', 5247, 5,20988) which basically means populate the US exchange universe from ticker indexed at 20988 to ticker indexed at 20988+5247

    Note if exchange_list is an empty list, the function will populate the entire list of exchanges.

    . sql_connection: SQL connection of the meta database
    '''
    __reset_stats()
    exchanges=[]
    if len(exchange_list)==0:
        # Get the list of exchanges
        __logger.info("Getting the list of exchanges...")
        exchanges = client.get_exchanges()
        for e in exchanges:
            e['Size']=-1 #just means the full exchange
            e['Part']= 1
            e['Start']= 0
        __logger.info("%d exchanges will be loaded in the database", len(exchanges))
    else:
        # Fetch each exchange details
        exchs = client.get_exchanges()
        found=False
        for (exchange_code, exchange_size, exchange_part, exchange_start) in exchange_list:
            #Find the exchange code in the exchange list exchs
            es = [ex for ex in exchs if ex['Code']==exchange_code]
            if(len(es) != 0):
                found = True
                es[0]['Size']=exchange_size
                es[0]['Part']= exchange_part
                es[0]['Start']= exchange_start
                exchanges.extend(es)
            if(len(es)!=1):
                raise FeederException("It seems the exchange {exchange} is specified more than once in the list of exchanges to process. Please check the configuration".format(exchange=es[0]['Code']))
            if(found == False):
                __logger.warn("Could not find exchange %s", exchange_code)

    __populate_exchanges(client, sqlconnection, exchanges)

def __connect_sql_db()->pyodbc.Connection: 
    '''
    Connects to SQL QB and return a connection or None if a connection cannot be established
    '''
    # Some other example server values are
    # server = 'localhost\sqlexpress' # for a named instance
    # server = 'myserver,port' # to specify an alternate port
    try:
        server = get_config("SQL_SERVER", configfile=__config_file)
        database = get_config("SQL_DB", configfile=__config_file)
        username = get_config("SQL_USER", configfile=__config_file)
        password = get_config("SQL_PASSWORD", configfile=__config_file) 
        connectionurl='DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password
        __logger.debug("Connecting to database server with:%s", connectionurl)
        cnxn = pyodbc.connect(connectionurl)
        return cnxn
    except Exception as e:
        __logger.error("Cannot connect to SQL database:%s", str(e))
        return None


def __get_exchange_list(config:dict, batch_name:str)->list:
    exchange_list = []
    exchanges_in_batch = [batches['Exchanges'] for batches in config if batches['Batch_Name'] == batch_name]
    if len(exchanges_in_batch) != 1:
        raise FeederException("Could not find the batch {batch_name} in the configuration".format(batch_name=batch_name))
    for exchange in exchanges_in_batch[0]:
        exch = (exchange['Code'], exchange['Size'], exchange['Part'], exchange['Start'])
        exchange_list.append(exch)
    return exchange_list

def __build_exchange_list(exchange_list:list):
    '''
    Take a list of exchanges and augment it with meta data
    '''
    to_return=[]
    for exchange in exchange_list:
        to_return.append((exchange, -1, 1, 0))
    return to_return

def run_feeder_batch(batch_name:str):
    '''
    Run the feeder for the list of exchanges in batch identified by batch_name
    '''
    __logger.info("Running batch feeder process %s", batch_name)
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    sqlconnection = __connect_sql_db()
    with open("config/controller.json", "r") as config_file:
        config = json.load(config_file)
    exchange_list = __get_exchange_list(config, batch_name)
    build_initial_db(client, exchange_list, sqlconnection)

def run_feeder(exchange_list):
    '''
    Run the feeder for the list of exchanges passed in argument
    Each element of the list is just a list of exchange codes
    '''
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    sqlconnection = __connect_sql_db()
    build_initial_db(client, exchange_list, sqlconnection)

if __name__ == '__main__':
    try:
        exchange_list,configfile = process_arguments()
        exchange_list = __build_exchange_list(exchange_list)
        run_feeder(exchange_list)
        display_stats(__stats)
    except Exception as e:
        print("Fatal error:", str(e))
        __logger.fatal("Fatal error:%s", str(e), stack_info=True)