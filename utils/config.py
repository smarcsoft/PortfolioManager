import argparse
import logging
import logging.config
import os
import platform
from exceptions import PMException

DEFAULT_CONFIG_FILE="config/pm.conf"
DEFAULT_LOGGING_CONFIG_FILE="config/logging.conf"
__configfile = None
__logger = None
__config = {}

def __parse_line(line:str):
    keyval = line.split('=')
    return(keyval[0], keyval[1])


def __read_configuration(configfile:str):
    '''
    Returns a dictionary containing the entry of the configuration file specified in arguments
    '''
    # print(f"Reading configuration file {configfile}")
    config = {}
    if(__logger != None): __logger.info("Reading configuration file %s...", configfile)
    with open(configfile, "rt") as configfile:
        for line in configfile:
            if (len(line.strip())> 0) and (not line.strip().startswith('#')):
                (key,value) = __parse_line(line)
                if(__logger != None): __logger.debug("Found %s -> %s", key, value.strip())
                config[key.strip()] = value.strip()
    return config



def process_arguments():
    '''
    Process the command line arguments

    Returns a tuple of:
        . A list of exchanges to be processed. An empty list means all exchanges
        . The config file given as an argument
        . An update boolean flag corresponding to the update argument specified
    '''
    config_file = "config/pm.conf"
    parser = argparse.ArgumentParser(description="Feed the database of the portfolio manager")
    parser.add_argument('--debug', '--log', '-d', nargs='?', choices=['DEBUG', 'INFO','WARN', 'ERROR','CRITICAL'], help="Enable debugging with the specified level")
    parser.add_argument('--exchange', '-e', nargs='+', action="extend",type=str, help="Process the list of exchanges specified (by their codes)")
    parser.add_argument('--config', '-c', nargs='?', action="store",type=str, help="Use the configuration file specified.")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('--update', action="store_true", help="update only (does not process history)")
    args=parser.parse_args()
    debug_level = None
    if hasattr(args,"d"): debug_level = args.d 
    if hasattr(args,"debug"): debug_level = args.debug 
    if hasattr(args,"log"): debug_level = args.log 
    if (__logger !=None) and (debug_level != None):
        logging.getLogger(None).setLevel(debug_level.upper())
        __logger.info("Debug level set to %s", debug_level.upper())

    if hasattr(args,"config") and (args.config != None): 
        config_file = args.config 
    exchange_list=[]
    if hasattr(args,"e") and (args.e != None): exchange_list = args.e 
    if hasattr(args,"exchange") and (args.exchange != None): exchange_list = args.exchange 
    if (len(exchange_list) != 0) and (__logger != None):
        __logger.info("Processing exchanges:%s",exchange_list)
    update = False
    if args.update:
        update = True
    return (exchange_list, config_file, update)

def init_config(logger:str=None, configfile:str=DEFAULT_CONFIG_FILE):
    '''
    Initializes the configuration subsystem so that get_config() works.
    '''
    global __configfile, __logger
    # print(f"Calling init_config with {configfile}")
    # Check existence of the config file and throw an exception if it does not exist
    if not os.path.exists(configfile):
        # Revert back to the environment variable
        # print("Using PM_CONFIG_LOCATION")
        location_from_env = os.environ.get("PM_CONFIG_LOCATION")
        if(location_from_env == None): raise PMException(f"Cannot initialize configuration subsystem: {configfile} does not exists")
        configfile = location_from_env
    __configfile = configfile
    # print(f"Configuration file set to {__configfile}")
    if(logger == None): logger = "root"
    __logger = init_logging(logger)

def init_logging(loggername:str="root", configfile:str=DEFAULT_LOGGING_CONFIG_FILE)->logging.Logger:
    '''
    Initialized the logging infrastructure.
    Reads the logging configuration from the configuration file configfile and initializes the logging subsystem accordingly.
    Returns the initialized logger.
    '''
    # Logging configuration file can be overriden by the environment
    logging_from_env = os.environ.get("PM_LOGGING_LOCATION")
    if(logging_from_env == None):
        # Get the logging subsystem configuration 
        log_conf_file_loc = get_config("LOGGING_CONFIGURATION")
        if(len(log_conf_file_loc) == 0):
            #Fall back to detault
            log_conf_file_loc = configfile
        if(os.path.exists(log_conf_file_loc)):
            # print(f"Using logging configuration {log_conf_file_loc}")
            logging.config.fileConfig(log_conf_file_loc)
            return logging.getLogger(loggername)
        else:
            raise PMException(f"Cannot initialize logging subsystem with {log_conf_file_loc}: The file does not exist")
    else:
        if(os.path.exists(logging_from_env)):
            # print(f"Using logging configuration {logging_from_env}")
            logging.config.fileConfig(logging_from_env)
            return logging.getLogger(loggername)
        else:
            raise PMException(f"Cannot initialize logging subsystem with {logging_from_env}: The file does not exist")


def get_config(key:str)->str:
    '''
    Read the configuration file if needed and return the entry identified by key.

    Returns an empty string if the key is not found.

    Assumes the current directory is the parent on the config directory.
    '''

    try:
        global __config, __configfile
        # print(f"Calling get_config {key}")

        # Check if an environment variable is overriding the configuration file
        if(os.environ.get(key) != None):
            return os.environ.get(key)

        if __configfile == None:
            init_config()
        if __configfile in __config:
            # We are aware of the configuration file
            return __config[__configfile][key]
        __config[__configfile] = __read_configuration(__configfile)
        return __config[__configfile][key]
    except Exception as e:
        if __logger != None: __logger.error("Could not get configuration %s using configuration file %s -> %s", key, __configfile, str(e))
        return ""


def get_install_location()->str:
    # Windows or Unix ?
    # print("get_install_location called")
    toreturn=""
    if(platform.system() == "Windows"):
        toreturn = get_config("INSTALL_DIR_WIN")
        # print(f"INSTALL_DIR_WIN returned {toreturn}")
    else:
        toreturn = get_config("INSTALL_DIR_UNIX")
    return toreturn

if __name__ == '__main__':
    assert get_config("LOG_FILE_LOC") != ""
    assert get_install_location() != ""