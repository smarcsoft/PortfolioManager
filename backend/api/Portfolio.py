import unittest
from numpy import number
from Ticker import Ticker
from Exchange import Exchange
from PMExceptions import PMException

Positions = dict[Ticker, number]

class Portfolio:
    '''
    A portfolio is:
    . A collection of instruments
    . Quantities of these instruments
    '''
    def __init__(self) -> None:
        self.positions:Positions = {}
    
    def buy(self, ticker_code:str, quantity:number, exchange:Exchange=Exchange('NASDAQ','US'), type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD" ):
        self._buy(Ticker(ticker_code, exchange, type,isin,name, country, currency), quantity)

    def _buy(self, ticker:Ticker, quantity:number):
        if(ticker in self.positions):
            self.positions[ticker] = self.positions[ticker] + quantity
        else:
            self.positions[ticker] = quantity

    def sell(self, ticker_code:str, quantity:number, exchange:Exchange=Exchange('NASDAQ','US'), type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD" ):
        self._sell(Ticker(ticker_code, exchange, type,isin,name, country, currency), quantity)

    def _sell(self, ticker:Ticker, quantity:number):
        if((ticker in self.positions) and self.positions[ticker]) >= quantity:
            self.positions[ticker] = self.positions[ticker] - quantity
        else:
            raise PMException("Cannot sell {ticker_code}. Either the portfolio does not own the instrument or it does not have enough quantity of this instrument.".format(ticker_code=ticker))

    def get_quantity(self, ticker_code:str, exchange:Exchange=Exchange('NASDAQ','US'), type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD" ):
        return self._get_quantity(Ticker(ticker_code, exchange, type,isin,name, country, currency))

    def _get_quantity(self, ticker:Ticker)->number:
        return self.positions[ticker]

class UnitTestPortfolio(unittest.TestCase):
    def test_buy(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        p.buy('MSFT', 30)
        self.assertEqual(p.get_quantity('MSFT'), 40)
        self.assertEqual(p.get_quantity('CSCO'), 20)

    def test_sell_short(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 40)
        p.buy('CSCO', 20)
        p.sell('MSFT', 40)
        self.assertEqual(p.get_quantity('MSFT'), 0)
        try:
            p.sell('MSFT', 1)
            self.assertFalse(True) # Fail the test since exception should have been raised
        except PMException:
            self.assertTrue(True)

    def test_sell_what_you_do_not_have(self):
        p:Portfolio = Portfolio()
        try:
            p.sell('MSFT', 40)
            self.assertFalse(True) # Fail the test since exception should have been raised
        except PMException:
            self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
