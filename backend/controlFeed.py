import argparse
import json
import logging
import logging.config
from multiprocessing import Process
from feeder import run_feeder_batch
from fdfeed import run_fundamental_data_feeder_batch

logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('controller')

def run_batch(config:dict, configfile, batch_definition_file, load_type, debug_level)->Process:
    '''
    Spawns a batch process and return the process spawned
    '''
    __logger.info("Running batch %s", config['Batch_Name'])
    __logger.info("Exchanges covered:%s", [exchange['Code'] for exchange in config['Exchanges']])
    #spawn the feeder with the list of exchanges
    if(load_type == "price"):
        p = Process(target=run_feeder_batch, args=(config['Batch_Name'],configfile, batch_definition_file))
    if(load_type == "fundamental_data"):
        p = Process(target=run_fundamental_data_feeder_batch, args=(config['Batch_Name'],configfile, batch_definition_file, debug_level))
    p.start()
    return p


def process_arguments():
    '''
    Return the configuration file to use
    '''
    parser = argparse.ArgumentParser(description="Feed the database of the portfolio manager using multiple loader instances")
    parser.add_argument('--debug', '--log', '-d', nargs='?', choices=['DEBUG', 'INFO','WARN', 'ERROR','CRITICAL'], help="Enable debugging with the specified level")
    parser.add_argument('--config', '-c', nargs='?', action="store",type=str, help="Use the controller configuration file specified.")
    parser.add_argument('--feederconfig', '-f', nargs='?', action="store",type=str, help="Use the feeder configuration file specified when spawning the feeders.")
    parser.add_argument('--load', '-l', nargs='?', action="store",type=str, help="Load type. Type can be price|fundamental_data. Default is price")
    parser.add_argument('--batch', '-b', nargs='?', action="store",type=str, help="Loads the batch specified.")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    args=parser.parse_args()
    debug_level = None
    batch = None
    if hasattr(args,"d"): debug_level = args.d 
    if hasattr(args,"debug"): debug_level = args.debug 
    if hasattr(args,"log"): debug_level = args.log 
    if debug_level != None:
        logging.getLogger(None).setLevel(debug_level.upper())
        __logger.info("Debug level set to %s", debug_level.upper())

    config_file = "config/controller.json"
    if hasattr(args,"config") and (args.config != None): 
        config_file = args.config 

    feeder_config_file = "config/pm.conf"
    if hasattr(args,"feederconfig") and (args.feederconfig != None): 
        feeder_config_file = args.feederconfig 

    load_type = "price"
    if hasattr(args,"load") and (args.load != None): 
        load_type = args.load 
    if hasattr(args,"batch") and (args.batch != None): 
        batch = args.batch 
    return config_file,feeder_config_file, load_type,debug_level, batch

def run_control(config:list, configfile, batch_definition_file, load_type, debug_level):
    #run each batch on the current machine
    processes=[]
    for configuration in config:
        __logger.info("Spawning batch process...")
        p = run_batch(configuration, configfile, batch_definition_file, load_type, debug_level)
        __logger.info("Batch process spawn %s", str(p))
        processes.append(p)

    #wait for each process to terminate
    for process in processes:
        process.join()
        __logger.info("Process %s terminated with exit code %d", str(process),process.exitcode)

if __name__ == '__main__':
    #read json config file
    conf,feeder_conf, load_type,debug_level,batch = process_arguments()
    with open(conf, "r") as config_file:
        config = json.load(config_file)
    if(batch != None):
        # Just retain the batch to process, not the set of batches specified in the configuration file
        config = [conf for conf in config if conf["Batch_Name"] == batch]
    run_control(config, feeder_conf, conf, load_type, debug_level)
