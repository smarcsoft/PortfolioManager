import datetime
from numpy import number
from PositionIdentifier import PositionIdentifier 

BUY=0
SELL=1

class Transaction:

    def __init__(self, type:int, pi: PositionIdentifier, quantity:number, date:datetime):
        '''
        Defines a new transaction
        type is either BUY or SELL
        '''
        self.__type = type
        self.__positionidentifier = pi
        self.__quantity = quantity
        self.__date = date

    def get_quantity(self)->number:
        return self.__quantity

    def get_transaction_type(self)->int:
        return self.__type

    def get_position_identifier(self)->PositionIdentifier:
        return self.__positionidentifier
    
    def get_date(self)->datetime:
        return self.__date
    
    

    
