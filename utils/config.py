import argparse
import logging
import logging.config


logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('config')

__config = {}

def __parse_line(line:str):
    keyval = line.split('=')
    return(keyval[0], keyval[1])


def __read_configuration(configfile:str):
    '''
    Returns a dictionary containing the entry of the configuration file specified in arguments
    '''
    config = {}
    __logger.info("Reading configuration file %s...", configfile)
    with open(configfile, "rt") as configfile:
        for line in configfile:
            if (len(line.strip())> 0) and (not line.strip().startswith('#')):
                (key,value) = __parse_line(line)
                __logger.debug("Found %s -> %s", key, value.strip())
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
    if debug_level != None:
        logging.getLogger(None).setLevel(debug_level.upper())
        __logger.info("Debug level set to %s", debug_level.upper())

    if hasattr(args,"config") and (args.config != None): 
        config_file = args.config 
    exchange_list=[]
    if hasattr(args,"e") and (args.e != None): exchange_list = args.e 
    if hasattr(args,"exchange") and (args.exchange != None): exchange_list = args.exchange 
    if len(exchange_list) != 0:
        __logger.info("Processing exchanges:%s",exchange_list)
    update = False
    if args.update:
        update = True
    return (exchange_list, config_file, update)

def get_config(key:str, *, configfile="config/pm.conf")->str:
    '''
    Read the configuration file is needed and return the entry identified by key.

    Returns an empty string if the key is not found.

    Assumes the current directory is the parent on the config directory.
    '''

    try:
        global __config
        if configfile in __config:
            # We are aware of the configuration file
            return __config[configfile][key]
        __config[configfile] = __read_configuration(configfile)
        return __config[configfile][key]
    except Exception as e:
        __logger.error("Could not get configuration %s using configuration file %s -> %s", key, configfile, str(e))
        return ""

if __name__ == '__main__':
    assert get_config("LOG_FILE_LOC") != ""