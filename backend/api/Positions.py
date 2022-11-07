from numpy import number
from PositionIdentifier import PositionIdentifier


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