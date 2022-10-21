import unittest
from Exchange import Exchange

class Ticker:
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
    def __init__(self, code:str, exchange:Exchange=Exchange('NASDAQ','US'), type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD"):
        self._type= type
        self._code= code
        self._isin = isin
        self._name = name
        self._country = country
        self._exchange = exchange
        self._currency = currency

    def __eq__(self, another):
        return self.get_full_ticker()==another.get_full_ticker()

    def __hash__(self):
        return self.get_full_ticker().__hash__()
    
    def get_full_ticker(self):
        return self._code+'.'+self._exchange.code
    
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
        return "Ticker {code} for {name} with isin {isin}".format(code = self._code, name = self._name, isin = self._isin)


class UnitTestTicker(unittest.TestCase):
    def test_ticker(self):
        t:Ticker = Ticker('GT', Exchange('NASDAQ', 'US'), type='Common Stock', isin='US3825501014', name='Goodyear Tire & Rubber Co', country='USA', currency='USD')
        self.assertEqual(t.get_full_ticker(), "GT.US")

    def test_ticker_equal(self):
        t1=Ticker('MSFT')
        t2=Ticker('MSFT')
        self.assertEqual(t1,t2)



if __name__ == '__main__':
    unittest.main()