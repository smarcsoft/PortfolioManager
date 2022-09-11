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

def run_control(config:list):
    #run each batch on the current machine
    #TODO
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
    with open("config/controller.json", "r") as config_file:
        config = json.load(config_file)
    run_control(config)
