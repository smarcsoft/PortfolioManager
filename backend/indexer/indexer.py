import json
import logging
import os
from config import  get_config, get_install_location,  init_logging, process_arguments
from exceptions import PMException


__logger = None

def walk_exchange(basedir, exchange_dir)->list:
    universe=[]
    for ticker in os.listdir(os.path.join(basedir,exchange_dir)):
        #Find the ID file
        idfiledir = os.path.join(basedir, exchange_dir, ticker)
        if(os.path.isdir(idfiledir)):
            with open(os.path.join(idfiledir, 'id'), 'rt') as id:
                universe.append(json.load(id))
    update_universe(os.path.join(basedir, exchange_dir), exchange_dir, universe)
    return universe

def walk(databasename:str)->list:
    '''
    Returns a list of objects. Each object is an id file structure.
    '''
    install = get_install_location()
    db_location = get_config("DB_LOCATION")
    basedir = os.path.join(install, "backend", db_location,databasename)
    universe = []
    for exchange in os.listdir(basedir):
        if(os.path.isdir(os.path.join(basedir, exchange))):
            universe.extend(walk_exchange(basedir, exchange))
    update_universe(basedir, "ALL", universe)
    return universe

def update_universe(directory, exchange, universe:list):
    __logger.info("Creating universe file for " + exchange)
    with open(os.path.join(directory, 'universe.json'), 'wt') as u:
        json.dump(universe, u)


if __name__ == '__main__':
    try:
        (exchange_list, config_file, update) = process_arguments()
        __logger = init_logging('indexer', config_file)
        __logger.info("Running indexer...")
        universe = walk('EQUITIES')
        __logger.info(str(len(universe)) +" tickers are being indexed")
    except Exception as e:
        print("Fatal error:", str(e))
        __logger.exception("Fatal error:%s", str(e))



