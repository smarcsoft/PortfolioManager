from Ticker import Ticker

#List of instrument types supported by the system
CASH=1
EQUITY=2 #Can be stocks, mutual funds, ETFs

InstrumentType=int #One of the instrument types numbers above

Currency = str

class PositionIdentifier:
    '''
    Identifier of a position.

    Can be one of the following:
    For equities: ticker 
    For cash: currency
    '''
    def __init__(self, instrument_type: InstrumentType, identifier:Ticker | Currency):
       self._type = instrument_type
       self._id = identifier

    def __eq__(self, another):
        return (self._type == another._type) and self._id==another._id

    def __hash__(self):
        return self._id.__hash__()
    
    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    def __repr__(self):
        if(self._type == 1):
            return "Cash {currency}".format(currency=self._id)
        return "Equity {identifier}".format(identifier=self._id)

