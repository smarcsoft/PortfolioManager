import logging
import logging.config


logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('config')

__config = {}

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

if __name__ == '__main__':
    assert get_config("LOG_FILE_LOC") != ""