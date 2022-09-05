from eod import EodHistoricalData
import logging
import logging.config

__config = {}
logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('feeder')


def __parse_line(line:str):
    keyval = line.split('=')
    return(keyval[0], keyval[1])

def __read_configuration():
    __logger.info("Reading configuration file config/pm.conf...")
    with open("config/pm.conf", "rt") as configfile:
        for line in configfile:
            (key,value) = __parse_line(line)
            __logger.debug("Found %s -> %s", key, value)
            __config[key] = value



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
        return __config([key])



def get_oed_apikey() -> str:
    return get_config('EOD_API_KEY')

EOD_API_KEY = get_oed_apikey()