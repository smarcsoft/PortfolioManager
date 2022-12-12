import unittest
from numpy import number
from PositionIdentifier import PositionIdentifier
from PositionIdentifier import EQUITY, Ticker
from PositionIdentifier import Currency
from PositionIdentifier import CASH
from copy import deepcopy

from Transaction import Transaction, BUY, SELL
from exceptions import PMException


class Positions:
    '''
    Contains the positions of a portfolio
    Positions are a set of PositionIdentifier and values (amount of money for currencies or number of shares)
    '''
    def __init__(self) -> None:
        self.__positions = {}

    @staticmethod
    def _create_from(positions:dict):
        toreturn = Positions()
        toreturn.__positions = positions
        return toreturn

    def apply_transaction(self, transaction: Transaction):
        quantity = transaction.get_quantity()
        pi = transaction.get_position_identifier()
        if(transaction.get_transaction_type() == BUY):
            if(pi in self):
                self[pi] = self[pi] + quantity
            else:
                self[pi] = quantity
            return
            
        if(transaction.get_transaction_type() == SELL):
            if((pi in self) and (self[pi] >= quantity)):
                self[pi] = self[pi] - quantity
            else:
                raise PMException(f"Cannot sell {quantity} {pi.pretty_print()}. Either the portfolio does not own the instrument or it does not have enough quantity of this instrument.")


    def state(self)->list:
        '''
        Returns a serializable state containing all the positions
        '''
        toreturn = []
        for positionidentifier in self.__positions.keys():
            element = {}
            element['identifier'] = positionidentifier.state()
            element['amount']=self.__positions[positionidentifier]
            toreturn.append(element)
        return toreturn

    def __getitem__(self, pi:PositionIdentifier)->number:
        return self.__positions[pi]

    def __iter__(self):
        return self.__positions.__iter__()

    def __next__(self):
        return self.__positions.__next__()

    def pretty_print(self) -> str:
        toreturn:str=""
        number_of_positions = len(self.__positions)
        for i, positionidentifier in enumerate(self.__positions):
            toreturn = toreturn + str(self.__positions[positionidentifier]) + " " + positionidentifier.pretty_print()
            if(i != number_of_positions-1):
                toreturn = toreturn + '\n'
        return toreturn

    def __setitem__(self, id:PositionIdentifier, value:number):
        self.__positions[id] = value

    def __len__(self):
        return len(self.__positions)

    def copy(self):
        '''
        Performs a deep copy of the positions
        '''
        return Positions._create_from(deepcopy(self.__positions))

    def get_tagged_positions(self,tags:set):
        toreturn:Positions = Positions()
        for positionidentifier in self.__positions:
            if positionidentifier.has_one_tag(tags):
                toreturn[positionidentifier] = self.__positions[positionidentifier]
        return toreturn

    
class UnitTestPositions(unittest.TestCase):
    def test_positions_tags(self):
        p:Positions = Positions()
        t1=Ticker('MSFT')
        pi1:PositionIdentifier = PositionIdentifier(EQUITY, t1)
        p[pi1] = 10
        self.assertEqual(p[pi1], 10)
        pi2:PositionIdentifier = PositionIdentifier(EQUITY, t1, tags={'EQUITY'})
        p[pi2] = 20
        self.assertEqual(p[pi2], 20)
        c1=Currency('USD')
        pi3:PositionIdentifier = PositionIdentifier(CASH, c1)
        p[pi3] = 1500
        self.assertEqual(p[pi3], 1500)
        pi4:PositionIdentifier = PositionIdentifier(CASH, c1, tags={'MY CASH'})
        p[pi4] = 2500
        self.assertEqual(p[pi4], 2500)
    


if __name__ == '__main__':
    unittest.main()
