import abc
import unittest
from exceptions import PMException


#List of instrument types supported by the system
CASH=1
EQUITY=2 #Can be stocks, mutual funds, ETFs
InstrumentType=int #One of the instrument types numbers above

supported_currencies =("USD","EUR", "RUB", "GBP", "CNY", "JPY", "SGD", "INR", "CHF", "AUD", "CAD", "HKD", "MYR", "NOK", "NZD", "ZAR","SEK", "DKK", "BRL", "ZAC", "MXN", "TWD", "KRW", "CLP", "CZK", "HUF", "IDR", "ISK", "MXV", "PLN", "TRY", "UYU", "THB", "SAR", "ILS")
supported_crypto_currencies = ("ADA","BCH","BTC","ETH","DOT","USDT","BNB","USDC","XRP","SOL","DOGE")

def check_currency(currency:str)->bool:
    '''
    Returns True if FIAT currency
    Returns False if cryto currency
    Returns an exception is unsupported.
    '''
    if (currency in supported_currencies): 
        return True

    if (currency in supported_crypto_currencies): 
        return False
    
    raise PMException("Invalid currency ({currency})".format(currency=currency))

class IInstrumentIdentifier:

    @abc.abstractmethod
    def get_identifier(self)->str:
        raise NotImplementedError("get_identifier should be implemented!")

class Currency(IInstrumentIdentifier):
    def __init__(self, currency:str="USD"):
        self._fiat = check_currency(currency)
        self._currency = currency

    def is_fiat(self)->bool:
        return self._fiat

    def is_cryto(self)->bool:
        return not self.is_fiat()

    def get_identifier(self)->str:
        return self._currency

    def __eq__(self, another):
        return self.get_identifier()==another.get_identifier()

    def __ne__(self, another):
        return not self.__eq__(another)

    def __hash__(self):
        return self.get_identifier().__hash__()

    def __repr__(self):
        return self.get_identifier()

class Ticker(IInstrumentIdentifier):
    '''
    Create a new ticker with:
    code: example GT
    country: example USA
    currency: example USD
    exchange: example NASDAQ
    isin: example US3825501014
    name: example 'Goodyear Tire & Rubber Co'
    type: example 'Common Stock'
    '''
    def __init__(self, code:str, exchange:str='US', type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD"):
        self._type= type
        self._code= code
        self._isin = isin
        self._name = name
        self._country = country
        self._exchange = exchange
        self._currency = currency

    def __eq__(self, another):
        return self.get_full_ticker()==another.get_full_ticker()

    def __ne__(self, another):
        return not self.__eq__(another)

    def __hash__(self):
        return self.get_full_ticker().__hash__()
    
    def get_full_ticker(self):
        return self._code+'.'+self._exchange

    def get_identifier(self)->str:
        return self.get_full_ticker()

    def get_currency(self)->Currency:
        if(self.exchange == 'US'):
            return Currency("USD")
        raise PMException("Undefined currency for ticker {ticker}", ticker = self.get_full_ticker())
        
    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def country(self):
        return self._country

    @property
    def exchange(self):
        return self._exchange

    @property
    def currency(self):
        return self._currency

    @property
    def type(self):
        return self._type

    @property
    def isin(self):
        return self._isin

    def __repr__(self):
        return "Ticker {code} for company {name} with isin {isin}".format(code = self._code, name = self._name if len(self._name) != 0 else "UNKNOWN", isin = self._isin if (self._isin != None) and (len(self._isin) != 0) else "UNKNOWN")


class PositionIdentifier:
    '''
    Identifier of a position in a portfolio.
    Unlike an instrument identifier, a position identifier can be tagged

    Can be one of the following:
    For equities: ticker 
    For cash: currency
    '''
    def __init__(self, instrument_type: InstrumentType, identifier:Ticker | Currency, tags:set=None):
        self._type = instrument_type
        self._id = identifier
        if(tags == None):
            self._tags = set()
        else:
            self._tags = tags

    def __eq__(self, another):
        return (self._type == another._type) and (self._id==another._id) and (self.tags == another.tags)

    def __hash__(self):
        return self._id.__hash__()
    
    @property
    def id(self):
        return self._id

    def _get_full_id_with_tags(self)->str:
        tagids=""
        if(len(self._tags)>0):
            tagids= self.__construct_tag_id()
            return self.id.get_identifier()+"/"+tagids
        else:
            return self.get_identifier()

    @property
    def type(self):
        return self._type

    def __repr__(self):
        if(self._type == 1):
            return "Cash {currency}".format(currency=self._id)
        return "Equity {identifier}".format(identifier=self._id)


    def __construct_tag_id(self)->str:
        toreturn=""
        for (i,tag) in enumerate(self._tags):
            toreturn+=tag
            if(i != len(self._tags)-1):
                toreturn+="/"
        return toreturn

    @property
    def tags(self):
        return self._tags


class UnitTestTicker(unittest.TestCase):
    def test_ticker(self):
        t:Ticker = Ticker('GT', 'US', type='Common Stock', isin='US3825501014', name='Goodyear Tire & Rubber Co', country='USA', currency='USD')
        self.assertEqual(t.get_full_ticker(), "GT.US")

    def test_ticker_equal(self):
        t1=Ticker('MSFT')
        t2=Ticker('MSFT')
        self.assertEqual(t1,t2)

    def test_position_identifier_hash(self):
        t1=Ticker('MSFT')
        t2=Ticker('MSFT')
        self.assertEqual(t1.__hash__(),t2.__hash__())
        pi1:PositionIdentifier = PositionIdentifier(EQUITY, t1)
        pi2:PositionIdentifier = PositionIdentifier(EQUITY, t2)
        self.assertEqual(pi1.__hash__(),pi2.__hash__())
        pi1:PositionIdentifier = PositionIdentifier(EQUITY, t1, tags={'INITIAL'})
        pi2:PositionIdentifier = PositionIdentifier(EQUITY, t2, tags={'INITIAL'})
        self.assertEqual(pi1.__hash__(),pi2.__hash__())

    def test_currency(self):
        c1 = Currency("USD")
        c2 = Currency("USD")
        self.assertEqual(c1, c2)

    def test_positionIdentifier(self):
        pi1 = PositionIdentifier(EQUITY, Ticker("MSCI"), tags={"EQUITY", "BONUS", "YEAR2020"})
        self.assertTrue(pi1._get_full_id_with_tags().index("YEAR2020")!=0)
        self.assertTrue(pi1._get_full_id_with_tags().index("EQUITY")!=0)
        self.assertTrue(pi1._get_full_id_with_tags().index("BONUS")!=0)




if __name__ == '__main__':
    unittest.main()