import os

__database_location = None
__default_database_location = "backend/db"

def get_ticker_slice(symbols:list, exchange:dict):
    if exchange['Size'] == -1: return symbols
    #Filter for the subexchnage
    return symbols[exchange['Start']:exchange['Start']+exchange['Size']]


def get_equity_database()->str:
    '''
    Returns the database location
    '''
    if(__database_location != None): return __database_location
    if 'DB_LOCATION' in os.environ:
        return os.environ['DB_LOCATION']+"/EQUITIES"
    return __default_database_location+"/EQUITIES"

def get_fx_database()->str:
    '''
    Returns the database location
    '''
    if(__database_location != None): return __database_location
    if 'DB_LOCATION' in os.environ:
        return os.environ['DB_LOCATION']+"/FX"
    return __default_database_location+"/FX"

def set_database(location:str):
    __database_location = location