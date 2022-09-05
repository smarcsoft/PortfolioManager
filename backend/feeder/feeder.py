from eod import EodHistoricalData
import logging
import logging.config
import os

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

def __update_exchange(exchange):
    #Check if the directory exists and if not create it
    db_loc = get_config('DB_LOCATION')
    if not os.path.exists('/'+exchange['Code']):
        # Create the directory
        __logger.info("Creating exchange %s in the database", exchange['Code'])
        tocreate = os.path.join(db_loc, exchange['Code'])
        os.mkdir(tocreate)
        # Create id file
        with open(tocreate+'/id', 'wt') as id:
            id.write(str(exchange))


def __update_db(value:str,type:str="price"):
    if type=='exchange':
        __update_exchange(value)

def build_initial_db(client):
    # Get the list of exchanges
    __logger.info("Getting the list of exchanges...")
    exchanges = client.get_exchanges()
    __logger.info("%d exchanges retrieved", len(exchanges))
    for exchange in exchanges:
        __update_db(exchange, type="exchange")
    # For each exchange, get the list of tickers
    # Build the directory tree
    # For each ticker, get the eod data
    # Create a subtree for each data point

EOD_API_KEY = get_oed_apikey()
client = EodHistoricalData(EOD_API_KEY)
build_initial_db(client)