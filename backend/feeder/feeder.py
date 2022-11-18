from genericpath import exists
import glob
import os
import unittest
from eod import EodHistoricalData
import logging
import logging.config
import logging.handlers
import json
import math
import shutil
import datetime
from datetime import date
import numpy as np
from config import DEFAULT_CONFIG_FILE, DEFAULT_LOGGING_CONFIG_FILE, get_config, process_arguments, init_config
from exceptions import FeederException
from feedutils import get_ticker_slice


__logger = None
DATE_FORMAT = '%Y-%m-%d'

#Stats is a complex data structure grouping all statistics of the feeding process
# {"Exchanges", "Tickers"}
# Exchanges: {"Processed, Errors"}
# Exchanges{"Processed"} ->["Code-Part"]: Processed is a list of successfully processed exchange parts
# Exchanges{"Errors"} -> ["Code-Part"]: Errors is a list of errorneous exchange (part) loads

# Tickers: {"Processed, Errors"}
# Tickers  {"Processed"} ->["Code"]: Processed is a list of successfully processed fully qualified tickers
# Tickers{"Errors"} -> [{"code-part:[]"}]: Errors is a list of dict with exchangecode-part being the key and the list of {"Code" (fully qualified ticker code), "Error" (error strings)} as values
__stats={}

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

def get_oed_apikey() -> str:
    return get_config('EOD_API_KEY')

def __updatedb_exchange(exchange):
    '''
    Makes sure the directory structures are there in the file database for the exchange passed in argument
    '''
    #Check if the directory exists and if not create it
    try:
        db_loc = get_config('DB_LOCATION')
        tocreate = os.path.join(db_loc, "EQUITIES", exchange['Code'])
        os.makedirs( tocreate, exist_ok=True )
        if not os.path.exists(tocreate):
            # Create the directory
            __logger.info("Creating exchange %s in the database", exchange['Code'])
            os.makedirs(tocreate)
            # Create id file
            with open(tocreate+'/id', 'wt') as id:
                id.write(str(exchange))
        __stats['Exchanges']['Processed'].append(exchange['Code']+'-'+ str(exchange['Part']))
    except Exception as e:
        __logger.error("Could not process exchange %s part %d -> %s", exchange['Code'], exchange['Part'],str(e))
        __stats['Exchanges']['Errors'].append(exchange['Code']+'-'+str(exchange['Part']))




def __updatedb_tickers(exchange,client):
    '''
    Update the database tree with the tickers for the exchange passed in argument
    
    Returns the list of tickers retrieved by the API
    '''
    # For each exchange, get the list of tickers
    __logger.info("Getting the ticker list for exchange %s", exchange['Code'])
    try:
        symbols = client.get_exchange_symbols(exchange=exchange['Code'])
        symbols = get_ticker_slice(symbols, exchange)
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
        db_loc = get_config('DB_LOCATION')
        exchange_loc = os.path.join(db_loc, "EQUITIES", exchange['Code'])
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


def __update_meta_data_file(filename, data_point):
    '''
    Updates the meta data on the file database for the data point data_file

    Returns a tuple:
    The start date of the data point in the database before the update
    The end date of the data point in the database before the update
    The start date of the data point in the database after the update
    The end date of the data point in the database after the update
    or (None, None, start date after update, end date after update) if the file did not exists and was created by this function.

    '''
 
    new_datapoint_base_date = datetime.datetime.strptime(data_point['base_date'], DATE_FORMAT).date()
    new_datapoint_last_date = datetime.datetime.strptime(data_point['last_date'], DATE_FORMAT).date()
    s={}
    s['base_date'] = data_point['base_date']
    s['last_date'] = data_point['last_date']
    s['name'] = data_point['name']

    previous_datapoint_base_date = None
    previous_datapoint_last_date = None
    toupdate = s
    # Read the previous meta data file if it does exist
    if exists(filename):
        with open(filename,'r') as metafile:
            toupdate = json.loads(metafile.read())
            previous_datapoint_base_date = datetime.datetime.strptime(toupdate['base_date'], DATE_FORMAT).date()
            previous_datapoint_last_date = datetime.datetime.strptime(toupdate['last_date'], DATE_FORMAT).date()
            if new_datapoint_base_date < previous_datapoint_base_date: toupdate['base_date'] = s['base_date']
            if new_datapoint_last_date > previous_datapoint_last_date: toupdate['last_date'] = s['last_date']
    with open(filename,'w') as metafile:
        json.dump(toupdate, metafile)
    if previous_datapoint_base_date != None:
        return (previous_datapoint_base_date, previous_datapoint_last_date, min(new_datapoint_base_date, previous_datapoint_base_date), max(new_datapoint_last_date, previous_datapoint_last_date))
    else:
        return (None, None, new_datapoint_base_date, new_datapoint_last_date)

def __update_data_vector(before_datavec:np.ndarray, before_start_date, before_end_date, new_data_vec, new_start_date, new_end_date):
    #Check how many days prepend at the beginning of the data vector
    days_to_prepend = (before_start_date - new_start_date).days
    #Check how many days to append at the end of the data vector
    days_to_append = (new_end_date - before_end_date).days
    #sum them up and create a new vector of the new size
    newvec = np.zeros(before_datavec.size + max(0,days_to_prepend) + max(0,days_to_append))
    #Put the old data
    newvec[max(days_to_prepend,0):max(days_to_prepend,0) + before_datavec.size] = before_datavec
    #Override it with the new data
    if days_to_prepend > 0: 
        newvec[0:new_data_vec.size] = new_data_vec
    else:
        newvec[-days_to_prepend:-days_to_prepend+new_data_vec.size] = new_data_vec
    return newvec
    


def __update_data_file(filename, data_point:np.ndarray, before_start_date, before_end_date, new_start_date, new_end_date):
    #Check if file exists
    if os.path.exists(filename):
        #Update the file (read->add->store)
        before_datavec = np.load(file=filename)
        new_data_vec = __update_data_vector(before_datavec, before_start_date, before_end_date, data_point, new_start_date, new_end_date)
        #deletes the previous file to write the new one
        os.remove(filename)
        np.save(filename, new_data_vec)
    else:
        # Create the numpy array
        np.save(filename, data_point)



def __feed_data_file(exchange:str, ticker:str, data_point:dict):
    '''
    Creates (and creates only, does not support update) the data point file in the DB

    Arguments:
    . exchange: Exchange code
    . ticker: ticker code (not fully qualified with the exchange)
    . full_ticker: Fully qualified ticker 
    . data_point: dict containing the fields of the data points (name, data, base_date, last_date)
    '''
    #Check if file exists
    db_loc = get_config('DB_LOCATION')
    exchange_loc = os.path.join(db_loc, 'EQUITIES', exchange)
    ticker_loc = os.path.join(exchange_loc, ticker)
    meta_loc = os.path.join(ticker_loc,data_point['name']+".meta")
    data_loc = os.path.join(ticker_loc,data_point['name']+".npy")
    start_date = data_point['base_date']
    end_date = data_point['last_date']
    before_start_date, before_end_date, after_start_date, after_end_date = __update_meta_data_file(meta_loc,data_point)
    __update_data_file(data_loc,data_point['data'], before_start_date, before_end_date, datetime.datetime.strptime(start_date, DATE_FORMAT).date(), datetime.datetime.strptime(end_date, DATE_FORMAT).date())
    

def __get_eod_field(prices:list, base_date:str, field_name:str, type:np.dtype, as_of_date:date)->np.ndarray:
    '''
    returns a ndarray containing the data point values.
    There is one element per calendar date from the base date to the as_of_date
    '''
    base_date = datetime.date.fromisoformat(base_date)
    to_date = min(date.fromisoformat(prices[len(prices)-1]['date']), as_of_date)
    number_of_elements = to_date - base_date 
    toreturn = np.zeros(number_of_elements.days+1, type)
    for price in prices:
        dp_date = datetime.date.fromisoformat(price['date'])
        index = (dp_date - base_date).days
        if (index > number_of_elements.days): break
        toreturn[index]= np.float32(price[field_name])
    return toreturn

def __pack_datapoint(dp:dict,fieldname:str,prices:list, as_of_date:date):
    '''
    Update the data point dictionary dp by adding the following keys:
    
    .base_date: The date of the oldest data point of the time series
    .last_date: The date of the most recent data point
    .name: The name of the field
    .data: a numpy array containing the data time series. Empty values are 0.0.

    Returns the dp dictionary containing the updated data point
    '''
    dp['base_date']=prices[0]['date']
    dp['last_date']=date.strftime(min(date.fromisoformat(prices[len(prices)-1]['date']), as_of_date), DATE_FORMAT)
    dp['name'] = fieldname
    dp['data'] = __get_eod_field(prices, dp['base_date'], fieldname, np.float32, as_of_date)
    return dp

def get_last_date(full_ticker:str)->date:
    '''
    Return the last coverage date or None
    '''
    try:
        # Read the meta data files to extract the last date 
        # We retain the oldest last date of all meta files
        filenames = __getmetafilenames(full_ticker)
        start_date:date | None = None
        for filename in filenames:
            file_start_date = get_start_date(filename)
            if(start_date==None): 
                start_date = file_start_date
            else:
                start_date = min(start_date, file_start_date)
        return start_date

    except Exception as e:
        __logger.error("Failed to retrive the last coverage date for ticker %s: %s", full_ticker, str(e))

def get_start_date(filename:os.path)->date:
    with open(filename,'r') as metafile:
        meta = json.loads(metafile.read())
        return date.fromisoformat(meta["last_date"])

def __getmetafilenames(full_ticker:str)->list:
    db_loc = get_config('DB_LOCATION')
    full_ticker_list = full_ticker.split('.')
    ticker = full_ticker_list[0]
    exchange = full_ticker_list[1]
    exchange_loc = os.path.join(db_loc, "EQUITIES", exchange)
    ticker_loc = os.path.join(exchange_loc, ticker)
    #List all meta files
    return glob.glob(ticker_loc+"/*.meta")



def __feed_db_eodprices(client,exchange:dict, ticker:dict, update:bool, as_of_date:date):
    '''
    Populate the database with end of day market data for the ticker belonging to this exchange (or subexchange)
    '''
    try:
        __logger.info("Fetching EOD prices for ticker %s from exchange %s", ticker['Code'], exchange['Code'])
        full_ticker= ticker['Code']+'.'+exchange['Code']
        if not update:
            prices = client.get_prices_eod(full_ticker)
        else:
            from_date = get_last_date(full_ticker)
            if from_date == None:
                prices = client.get_prices_eod(full_ticker)
            else:
                from_date = from_date + datetime.timedelta(1)
                prices = client.get_prices_eod(full_ticker, period = 'd', order='a', from_=from_date)
        # Getting back [{date,open,high,low,close,adjusted_close,volume}]
        dp = {}
        if len(prices) >0 :
            dp=__pack_datapoint(dp,'open', prices, as_of_date)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'close', prices, as_of_date)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'high', prices, as_of_date)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'low', prices, as_of_date)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'adjusted_close', prices, as_of_date)
            __feed_data_file(exchange['Code'], ticker['Code'], dp)
            dp=__pack_datapoint(dp,'volume', prices, as_of_date)
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
    

def __populate_exchanges(client, exchanges:dict, update:bool, as_of_date:date):
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
        for ticker in tickers:
            __feed_db_eodprices(client,exchange, ticker, update, as_of_date)



def update_db(client, exchange_list:list, update, as_of_date:date=date.today()):
    '''
    Populate the file database
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

    . update: True if we just update the database up to today's data (we are not processing the full history)
    . as_of_date: as of date, which basically means run the loader as if we were on that date
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
            
            if(len(es)>1):
                raise FeederException("It seems the exchange {exchange} is specified more than once in the list of exchanges to process. Please check the configuration".format(exchange=es[0]['Code']))
            if(found == False):
                __logger.warning("Could not find exchange %s", exchange_code)

    __populate_exchanges(client, exchanges, update, as_of_date)



def __get_exchange_list(config:dict, batch_name:str)->list:
    exchange_list = []
    exchanges_in_batch = [batches['Exchanges'] for batches in config if batches['Batch_Name'] == batch_name]
    if len(exchanges_in_batch) != 1:
        raise FeederException("Could not find the batch {batch_name} in the configuration".format(batch_name=batch_name))
    for exchange in exchanges_in_batch[0]:
        exch = (exchange['Code'], exchange['Size'], exchange['Part'], exchange['Start'])
        exchange_list.append(exch)
    return exchange_list

def build_exchange_list(exchange_list:list):
    '''
    Take a list of exchanges and augment it with meta data
    '''
    to_return=[]
    for exchange in exchange_list:
        to_return.append((exchange, -1, 1, 0))
    return to_return

def run_feeder_batch(batch_name:str, configfile):
    '''
    Run the feeder for the list of exchanges in batch identified by batch_name
    '''
    init(None, configfile)
    __logger.info("Running batch feeder process %s", batch_name)
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    with open(configfile, "r") as config_file:
        config = json.load(config_file)
    exchange_list = __get_exchange_list(config, batch_name)
    update_db(client, exchange_list, False)
    display_stats(__stats)

def run_feeder(exchange_list, update:bool, as_of_date:date=date.today()):
    '''
    Run the feeder for the list of exchanges passed in argument
    Each element of the list is just a list of exchange codes
    '''
    init(None, configfile)
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    update_db(client, exchange_list, update, as_of_date)
    display_stats(__stats)


class UnitTestFeeder(unittest.TestCase):
    def setUp(self):
        init(None, "tests/config/pm.conf")
    
    def test__get_last_date(self):
        self.assertEqual(get_last_date("NESN.VX"), date(2022,11,10))

    def test__get_next_last_date(self):
        self.assertEqual(get_last_date("NESN.VX"), date(2022,11,11))

    def emptyvx(self):
        loc = get_config("DB_LOCATION")
        shutil.rmtree(os.path.join(loc, "EQUITIES/VX"))

    def test_full_load(self):
        self.emptyvx()
        exchange_list = build_exchange_list(['VX'])
        run_feeder(exchange_list, False,date(2022,11,10))
        self.assertTrue(True)

    def test_update_load(self):
        exchange_list = build_exchange_list(['VX'])
        run_feeder(exchange_list, True,date(2022,11,11))
        self.assertTrue(True)

if __name__ == '__main__':
    try:
        exchange_list,configfile,update = process_arguments()
        exchange_list = build_exchange_list(exchange_list)
        run_feeder(exchange_list, update)
    except Exception as e:
        print("Fatal error:", str(e))
        __logger.exception("Fatal error:%s", str(e))



