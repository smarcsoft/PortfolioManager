import json
from config import process_arguments
from config import get_config
import logging
import logging.config
from eod import EodHistoricalData

logging.config.fileConfig("config/logging.conf")
__logger = logging.getLogger('controller')

class ExchangeNotAssigned(Exception): pass
class AllocationError(Exception): pass

'''
Creates the json configuration file of the controlFeed

Without any argument, the configuration file created will be based on the entire today's universe.
The biggest exchanges will be split according to the configuration file 

We can provide the -e or --exchanges argument to restrict the universe to the list of exchanges provided.

'''

def generate_exchange_list(client):
    exchanges = client.get_exchanges()
    #print list of exchanges as a comma separated string
    #exchangelist = [exchange['Code'] for exchange in exchanges]
    #print(exchangelist)
    return exchanges


def __fillbucket(bucket_number:int, exchanges_remaining:list, buckets, buckets_size):
    '''
    Fills in the bucket identified with bucket_number (0-based) with one exchang
    The exchange chosen will be the biggest fitting in the bucket
    If the smallest exchange is bigger when the bucket remaining size, an exeption will be thrown since it would mean the bucket is too small

    Parameters:
    bucket_number: Identifies the bucket to be filled by one exchange
    exchanges_remaining: List of remaining exchanges waiting to be assigned a bucket. This is an output parameter since the algorithm will remove the exchange allocated to a bucket from the list.
    buckets: List of dictionaries containing:
        . Remaining_size: size remaining in the bucket
        . Exchanges: List of exchanges. 
    This is an output parameter since the list of bucket will be modified with the exchange allocated into a bucket.
    
    buckets_batch_size: The initial size of each bucket
    '''
    #get the current list of exchanges of the bucket
    if buckets[bucket_number] == None: 
        buckets[bucket_number]={}
        buckets[bucket_number]['Batch_Name'] = 'Batch_{n:02d}'.format(n=bucket_number+1)
        buckets[bucket_number]['Remaining_size'] = buckets_size
        buckets[bucket_number]['Exchanges'] = []
    exchanges_in_bucket = buckets[bucket_number]
        
    #get the remaining size of the bucket
    remaining_size = buckets[bucket_number]['Remaining_size']
    #Find the biggest exchange smaller than remaining_size
    found = False
    for exchange in exchanges_remaining:
        if exchange['Size'] <= remaining_size:
            found = True
            #Assign the exchange to the bucket
            exchanges_in_bucket['Exchanges'].append(exchange)
            exchanges_in_bucket['Remaining_size']-=exchange['Size']
            #Remove the exchange from the list of remaining exchanges to be assigned
            exchanges_remaining.remove(exchange)
            __logger.debug("Exchange %s (%d tickers) assigned to bucket %d", exchange['Code'],exchange['Size'], bucket_number)
            __logger.debug("%d exchanges remain to be assigned", len(exchanges_remaining))
            break
    if not found:
        #We could not assign an exchange to the bucket
        raise ExchangeNotAssigned("Bucket {bucket_index} could not be given an exchange to process. Its remaining size is {remaining_size} and the smallest exchange size is {smallest_exchange_size} -,> {smallest_exchange} exchange"
        .format(bucket_index=bucket_number, remaining_size=remaining_size, smallest_exchange_size=exchanges_remaining[len(exchanges_remaining)-1]['Size'], smallest_exchange=exchanges_remaining[len(exchanges_remaining)-1]['Code']))

        


def __split_exchanges(batch_number:int, exchange_stats:list):
    '''
    Algorithm splitting the ticker universes into batch_number batches
    Returns a list of batch_number elements with each element being dictionary with:
    .Batch_Name being the name of the batch
    .Remaining_Size number of tickers remaining to add in the element until it is full 
    .Exchanges being the list of echanges in that batch
    '''
    universe_size = sum([stat['Size'] for stat in exchange_stats])
    __logger.debug("Total universe size:%d", universe_size)
    batch_size = universe_size / batch_number * 1.25 #25% buffer
    buckets = [None]*batch_number
    buckets_size = int(batch_size)
    exchanges = exchange_stats.copy()
    # Sort the exchanges from the biggest to the smallest because we want to allocate the biggest first
    exchanges.sort(key=lambda e: e['Size'], reverse=True)
    bucket_number = -1
    while len(exchanges) >0:
        #Try to fill the bucket with an exchange.
        #If not possible, try the next bucket
        try:
            bucket_number+=1
            __fillbucket(bucket_number%batch_number, exchanges, buckets, buckets_size)
            nextb = 0
        except ExchangeNotAssigned as ena:
            nextb +=1
            if(nextb >=batch_number):
                #We could not allocate the remaining exchanges
                raise AllocationError("Could not allocate the following exchanges:" + str(exchanges)+". Underlying cause:"+str(ena))
    #All buckets allocated
    __logger.info("All %d exchanges have been allocated within %d buckets", len(exchange_stats), batch_number)
    return buckets

def __split_one_exchange(ex, parts):
    '''
    split exchange ex into parts parts and return the list of exchanges resulting
    '''
    org_size = ex['Size']
    __logger.debug("Splitting exchange %s of size %d into %d parts", ex['Code'], org_size, parts)
    new_size = int(org_size/parts)
    toreturn = []
    for i in range(parts):
        split_ex = {}
        split_ex['Code']=ex["Code"]
        split_ex['Part']=i+1
        #Starting point in the exchange universe (index of the first tiker of the bacth)
        split_ex['Start'] = i*new_size
        if i != parts - 1:
            split_ex['Size']= new_size
        else:
            split_ex['Size']= org_size-new_size*(parts-1)
        __logger.debug("Exchange %s of size %d", split_ex['Code'], split_ex['Size'])
        toreturn.append(split_ex)
    return toreturn


def __split_exchange(exchange_stats:list, exchange_code_to_split:str, parts:int):
    for e in exchange_stats:
        if e['Code'] == exchange_code_to_split:
            exchange_stats.remove(e)
            es = __split_one_exchange(e, parts)
            exchange_stats.extend(es)
            return
    __logger.warn("Could not find exchange %s in the list of exchanges to split", exchange_code_to_split)


exchanges,configfile = process_arguments()
API_KEY = get_config("EOD_API_KEY", configfile=configfile)
client = EodHistoricalData(API_KEY)
#To generate the list of exchanges, invoke generate_exchange_list(client)
#exchanges = ['US', 'LSE', 'NEO', 'TO', 'BE', 'F', 'STU', 'HA', 'XETRA', 'HM', 'MU', 'DU', 'MI', 'VI', 'LU', 'PA', 'BR', 'AS', 'LS', 'VX', 'SW', 'MC', 'IR', 'ST', 'OL', 'CO', 'HE', 'IC', 'PR', 'TA', 'HK', 'KQ', 'KO', 'WAR', 'BUD', 'PSE', 'SG', 'BSE', 'KAR', 'SR', 'TSE', 'SN', 'BK', 'JSE', 'SHG', 'NSE', 'AT', 'SHE', 'AU', 'JK', 'CM', 'VN', 'KLSE', 'RO', 'SA', 'BA', 'MX', 'IL', 'ZSE', 'BOND', 'TWO', 'EUBOND', 'LIM', 'GBOND', 'MONEY', 'EUFUND', 'MCX', 'FOREX', 'TW', 'IS', 'INDX', 'CC', 'COMM']
# For each exchange, get the size of the universe

if len(exchanges) == 0:
    exchanges = [e['Code'] for e in generate_exchange_list(client)]
exchange_stats=[]
for exchange in exchanges:
    # Get the size of the universe
    try:
        symbols = client.get_exchange_symbols(exchange)
        __logger.info("%d symbols retrieved for exchange %s", len(symbols), exchange)
        exchange_stat = {}
        exchange_stat['Code']= exchange
        exchange_stat['Part']=1 #not plit by default
        exchange_stat['Start']=0
        exchange_stat['Size'] = len(symbols)
        exchange_stats.append(exchange_stat)
    except Exception as e:
        __logger.error("Error for %s -> %s", exchange, str(e))

#Check if we have to split exchanges further
exchanges_to_split = get_config("SPLIT_EXCHANGES", configfile=configfile)
exchanges_codes_to_split = exchanges_to_split.split(',')
for exchange_code_to_split in exchanges_codes_to_split:
    #How many parts ?
    parts = get_config("SPLIT_" + exchange_code_to_split.strip(), configfile=configfile)
    __split_exchange(exchange_stats, exchange_code_to_split, int(parts))

bs = __split_exchanges(int(get_config("SPLIT_BATCHES", configfile=configfile)), exchange_stats)
with open("config/controller.json","w") as config_file:
    json.dump(bs, config_file)
