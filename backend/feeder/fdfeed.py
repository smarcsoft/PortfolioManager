import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(),'..','utils'))
from eod import EodHistoricalData
import logging
import logging.config
import logging.handlers
import json
import datetime
from config import get_config, process_arguments
from exceptions import FeederException
from feedutils import get_ticker_slice


Error=str
Ticker = str
TickerError = tuple[Ticker, Error] 
SuccessFail = dict[str, list[TickerError]] #{"Success":("MSFT", ""), ("CSCO","")..., "Failed":("MSCI","Error while***"), ("GYTR", "Error while***")...}
Exchange = str
Statistics = dict[Exchange, SuccessFail]

logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('fdfeeder')

__stats:Statistics={}

__config_file = "config/pm.conf"

def get_oed_apikey() -> str:
    return get_config('EOD_API_KEY', configfile=__config_file)


def __update_stat_ticker_error(exchange:dict, symbol:str, e:Exception):
    '''
    Update the __stats global dictionary to register the ticker in error 
    '''
    global __stats
    if exchange not in __stats:
        __stats[exchange] = {"Success":list(), "Failed":list()}
    __stats[exchange]["Failed"].append((symbol, str(e)))
   
def __update_stat_ticker_success(exchange:str, symbol:str):
    '''
    Update the __stats global dictionary to register the ticker in error 
    '''
    global __stats
    if exchange not in __stats:
        __stats[exchange] = {"Success":list(), "Failed":list()}
    __stats[exchange]["Success"].append(symbol)

def __reset_stats():
    __stats={}


def __display_stats(logger):
    logger.info("Number of exchanges processed:{exchange_number}".format(exchange_number = len(__stats.keys())))
    for exchange in __stats.keys():
        logger.info("Exchange {exchange_name} summary:".format(exchange_name=exchange))
        logger.info("Success rate:{success_rate}%".format(success_rate=len(__stats[exchange]['Success'])/(len(__stats[exchange]['Success'])+len(__stats[exchange]['Failed']))*100))
        if(len(__stats[exchange]['Failed']) > 0):
            logger.info("Failure reporting:")
            for failed in __stats[exchange]['Failed']:
                logger.info("{ticker} -> {error_message}".format(ticker=failed[0], error_message=failed[1]))
            

def __store_fundamental_data(exchange:str, ticker:str, fundamental_data:dict):
    '''
    Stores the fundamental data of the ticker passed in arguments.

    Arguments:
    . exchange: Exchange code
    . ticker: ticker code (not fully qualified with the exchange)
    . fundamental_data: dictionary to store

    '''
    #Check if file exists
    db_loc = get_config('DB_LOCATION', configfile=__config_file)
    file_loc = os.path.join(db_loc, exchange, ticker)
    with open(file_loc+'/fd.json', 'wt') as fd:
        fd.write(json.dumps(fundamental_data))

    
def __feed_db_fundamental_data(client, exchange:str, ticker:str, index:int, total:int):
    '''
    Populate the database with fundamental data for the ticker belonging to this exchange (or subexchange)
    '''
    try:
        __logger.info("Fetching fundamental data for ticker %s (%d / %d) from exchange %s", ticker, index, total, exchange)
        full_ticker= ticker+'.'+exchange
        
        fundamental_data = client.get_fundamental_equity(full_ticker)
        if fundamental_data:
            __store_fundamental_data(exchange, ticker, fundamental_data)
            __update_stat_ticker_success(exchange, ticker)
        else:
            __update_stat_ticker_error(exchange, ticker, "No fundamental data retrieved for ticker " + ticker)
    except Exception as e:
        __logger.error("Could not get fundamental data for ticker %s.%s->%s", ticker, exchange, str(e))
        __update_stat_ticker_error(exchange, ticker, e)


def display_stats():
    logger = logging.getLogger("summary")
    logger.setLevel(logging.INFO)
    d = datetime.datetime.now()
    handler = logging.FileHandler(get_config("LOG_FILE_LOC", configfile=__config_file)+"/fdfeeder_run_{yyyy}-{mm:02d}-{dd:02d}_{hh:02d}_{mmm:02d}_{ss:02d}.log".format(yyyy=d.year, mm=d.month, dd=d.day, hh=d.hour, mmm=d.minute, ss=d.second))
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    __display_stats(logger)
    
    
def get_tickers_from_db(exchange:dict)->list[str]:
    '''
    Returns the list of tickers known to the database as string.
    Warning: These are not fully qualified tickers
    '''
    try:
        db_loc = get_config('DB_LOCATION', configfile=__config_file)
        toread = os.path.join(db_loc, exchange)
        tickers = os.listdir(toread)
        return tickers
    except Exception as e:
        __logger.error("Could not get tickers for exchange {exchange}:{exception_message}".format(exchange=exchange['Code'], exception_message=str(e)))
        raise e


def __populate_exchanges(client, exchanges:dict):
    '''
    Feed the database(s) with the exchanges market data
    '''
    for exchange in exchanges:
        if exchange['Size'] == -1:
            __logger.info("Populating database for full exchange %s", exchange['Code'])
        else:
            __logger.info("Populating database for exchange %s part %d (%d tickers)", exchange['Code'], exchange['Part'], exchange['Size'])

        tickers = client.get_exchange_symbols(exchange=exchange['Code'])
        tickers = get_ticker_slice(tickers, exchange)

        total = len(tickers)
        if (total >0):
            __logger.info("Processing {ticker_number} tickers...".format(ticker_number=total))
            i = 1
            for ticker in tickers:
                __feed_db_fundamental_data(client,exchange['Code'], ticker['Code'], i,total)
                i+=1



def update_db(client, exchange_list:list):
    '''
    Populate the file database with fundamental data
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

    __populate_exchanges(client, exchanges)



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

def run_feeder_batch(batch_name:str, configfile):
    '''
    Run the feeder for the list of exchanges in batch identified by batch_name
    '''
    __logger.info("Running batch feeder process %s", batch_name)
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    with open(configfile, "r") as config_file:
        config = json.load(config_file)
    exchange_list = __get_exchange_list(config, batch_name)
    update_db(client, exchange_list)
    display_stats()

def run_fundamental_data_feeder_batch(batch_name:str, configfile, debug_level):
    '''
    Run the fundamental data feeder for the list of exchanges in batch identified by batch_name
    '''
    if(debug_level != None):
        __logger.setLevel(debug_level)
    __logger.info("Running fundamental data batch feeder process %s", batch_name)
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    with open(configfile, "r") as config_file:
        config = json.load(config_file)
    exchange_list = __get_exchange_list(config, batch_name)
    update_db(client, exchange_list)
    display_stats()

def run_fundamental_data_feeder(exchange_list):
    '''
    Run the feeder for the list of exchanges passed in argument
    Each element of the list is just a list of exchange codes
    '''
    api_key = get_oed_apikey()
    client = EodHistoricalData(api_key)
    update_db(client, exchange_list)
    display_stats()

if __name__ == '__main__':
    try:
        exchange_list,configfile,update = process_arguments()
        exchange_list = __build_exchange_list(exchange_list)
        run_fundamental_data_feeder(exchange_list)
    except Exception as e:
        print("Fatal error:", str(e))
        __logger.exception("Fatal error:%s", str(e))