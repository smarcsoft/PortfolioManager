import argparse
import json
import logging
import logging.config
from multiprocessing import Process
from feeder.feeder import run_feeder_batch

logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('controller')

def run_batch(config:dict)->Process:
    '''
    Spawns a batch process and return the process spawned
    '''
    __logger.info("Running batch %s", config['Batch_Name'])
    __logger.info("Exchanges covered:%s", [exchange['Code'] for exchange in config['Exchanges']])
    #spawn the feeder with the list of exchanges
    p = Process(target=run_feeder_batch, args=(config['Batch_Name'],))
    p.start()
    return p


def process_arguments():
    '''
    Return the configuration file to use
    '''
    parser = argparse.ArgumentParser(description="Feed the database of the portfolio manager using multiple loader instances")
    parser.add_argument('--debug', '--log', '-d', nargs='?', choices=['DEBUG', 'INFO','WARN', 'ERROR','CRITICAL'], help="Enable debugging with the specified level")
    parser.add_argument('--config', '-c', nargs='?', action="store",type=str, help="Use the configuration file specified.")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    args=parser.parse_args()
    debug_level = None
    if hasattr(args,"d"): debug_level = args.d 
    if hasattr(args,"debug"): debug_level = args.debug 
    if hasattr(args,"log"): debug_level = args.log 
    if debug_level != None:
        logging.getLogger(None).setLevel(debug_level.upper())
        __logger.info("Debug level set to %s", debug_level.upper())

    config_file = "config/controller.json"
    if hasattr(args,"config") and (args.config != None): 
        config_file = args.config 
    return config_file

def run_control(config:list):
    #run each batch on the current machine
    processes=[]
    for configuration in config:
        __logger.info("Spawning batch process...")
        p = run_batch(configuration)
        __logger.info("Batch process spawn %s", str(p))
        processes.append(p)

    #wait for each process to terminate
    for process in processes:
        process.join()
        __logger.info("Process %s terminated with exit code %d", str(process),process.exitcode)

if __name__ == '__main__':
    #read json config file
    with open(process_arguments(), "r") as config_file:
        config = json.load(config_file)
    run_control(config)
