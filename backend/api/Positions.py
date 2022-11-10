import unittest
from numpy import number
from PositionIdentifier import PositionIdentifier
from PositionIdentifier import EQUITY, Ticker
from PositionIdentifier import Currency
from PositionIdentifier import CASH


class Positions:
    '''
    Containes the positions of a portfolio
    Positions are a set of PositionIdentifier and values (amount of money for currencies of number of shares)
    '''
    def __init__(self) -> None:
        self.__positions = {}

    def __getitem__(self, pi:PositionIdentifier)->number:
        return self.__positions[pi]

    def __iter__(self):
        return self.__positions.__iter__()

    def __next__(self):
        return self.__positions.__next__()

    def __repr__(self) -> str:
        toreturn:str=""
        number_of_positions = len(self.__positions)
        for i, positionidentifier in enumerate(self.__positions):
            toreturn = toreturn + str(self.__positions[positionidentifier]) + " " + str(positionidentifier)
            if(i != number_of_positions-1):
                toreturn = toreturn + '\n'
        return toreturn

    def __setitem__(self, id:PositionIdentifier, value:number):
        self.__positions[id] = value

    def __len__(self):
        return len(self.__positions)


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
