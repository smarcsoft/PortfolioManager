import unittest
from numpy import number
from Ticker import Ticker
from PMExceptions import PMException
from PositionIdentifier import PositionIdentifier, Currency, CASH, EQUITY

Positions = dict[PositionIdentifier, number]

#List of currencies supported by the system
supported_currencies =("USD","EUR", "RUB", "GBP", "CNY", "JPY", "SGD", "INR", "CHF", "AUD", "CAD", "HKD", "MYR", "NOK", "NZD", "ZAR","SEK", "DKK", "BRL", "ZAC", "MXN", "TWD", "KRW", "CLP", "CZK", "HUF", "IDR", "ISK", "MXV", "PLN", "TRY", "UYU", "THB", "SAR", "ILS")


def check_currency(currency:Currency):
        if currency not in supported_currencies:
            raise PMException("Invalid currency")
        return True


class Portfolio:
    '''
    A portfolio is:
    . A collection of instruments
    . Quantities of these instruments
    '''
    def __init__(self) -> None:
        self.positions:Positions = {}

    def get_positions(self) -> Positions:
        '''
        Returns the list of positions of the portfolio in a dictionary keyed my ticker.
        '''
        return self.positions
    
    def add(self, currency:Currency, quantity:number):
        '''
        Adds a quantify of cash in the portfolio
        '''
        check_currency(currency)
        if(PositionIdentifier(CASH, currency) in self.positions):
            self.positions[PositionIdentifier(CASH, currency)] = self.positions[(CASH,currency)] + quantity
        else:
            self.positions[PositionIdentifier(CASH,currency)] = quantity

    def buy(self, ticker_code:str, quantity:number, exchange:str='US', type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD" ):
        '''
        Adds an equity in the portfolio
        '''
        self._buy(PositionIdentifier(EQUITY, Ticker(ticker_code, exchange, type,isin,name, country, currency)), quantity)

    def _buy(self, ticker:PositionIdentifier, quantity:number):
        if(ticker in self.positions):
            self.positions[ticker] = self.positions[ticker] + quantity
        else:
            self.positions[ticker] = quantity

    def sell(self, ticker_code:str, quantity:number, exchange:str='US', type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD" ):
        '''
        Sells an equity from the portfolio
        '''
        self._sell(PositionIdentifier(EQUITY, Ticker(ticker_code, exchange, type,isin,name, country, currency)), quantity)


    def withdraw(self, currency:Currency, quantity:number):
        '''
        Withdraws some cash from the portfolio
        '''
        check_currency(currency)
        if((PositionIdentifier(CASH, currency) in self.positions) and (self.positions[PositionIdentifier(CASH, currency)] >= quantity)):
            self.positions[PositionIdentifier(CASH, currency)] = self.positions[PositionIdentifier(CASH,currency)] - quantity
        else:
            raise PMException("Cannot sell {quantity} {currency}. The portfolio does not have this amount of cash in the denominated currency".format(quantity=quantity, currency=currency))

    def _sell(self, ticker:PositionIdentifier, quantity:number):
        if((ticker in self.positions) and (self.positions[ticker] >= quantity)):
            self.positions[ticker] = self.positions[ticker] - quantity
        else:
            raise PMException("Cannot sell {ticker_code}. Either the portfolio does not own the instrument or it does not have enough quantity of this instrument.".format(ticker_code=ticker))


    def get_shares(self, ticker_code:str , exchange:str='US', type:str ='Common Stock',  isin:str="", name:str="", country:str="USA",  currency:str="USD" )->number:
        return self._get_shares(PositionIdentifier(EQUITY, Ticker(ticker_code, exchange, type,isin,name, country, currency)))

    def get_cash(self, currency:Currency)->number:
        check_currency(currency)
        return self.positions[PositionIdentifier(CASH,currency)]

    def _get_shares(self, ticker:PositionIdentifier)->number:
        return self.positions[ticker]

class UnitTestPortfolio(unittest.TestCase):
    def test_buy(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        p.buy('MSFT', 30)
        self.assertEqual(p.get_shares('MSFT'), 40)
        self.assertEqual(p.get_shares('CSCO'), 20)

    def test_positions(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 10)
        p.buy('CSCO', 20)
        p.buy('MSFT', 30)
        self.assertEqual(len(p.get_positions()),2)

    def test_sell_short(self):
        p:Portfolio = Portfolio()
        p.buy('MSFT', 40)
        p.buy('CSCO', 20)
        p.sell('MSFT', 40)
        self.assertEqual(p.get_shares('MSFT'), 0)
        try:
            p.sell('MSFT', 1)
            self.assertFalse(True) # Fail the test since exception should have been raised
        except PMException:
            self.assertTrue(True)

    def test_cash(self):
        p:Portfolio = Portfolio()
        p.add("USD", 10000)
        p.add("CHF", 50000)
        p.withdraw("USD", 4000)
        p.buy('MSFT', 40)
        self.assertEqual(p.get_cash('USD'), 6000)
        self.assertEqual(p.get_cash('CHF'), 50000)
        p.withdraw("USD", 1000)
        self.assertEqual(p.get_cash('USD'), 5000)
        self.assertEqual(p.get_cash('CHF'), 50000)
        p.withdraw("CHF", 20000)
        self.assertEqual(p.get_cash('USD'), 5000)
        self.assertEqual(p.get_cash('CHF'), 30000)
        self.assertEqual(p.get_shares('MSFT'), 40)
        

    def test_cash_short(self):
        p:Portfolio = Portfolio()
        p.add("USD", 10000)
        try:
            p.withdraw("USD", 10000) #Should be fine
        except PMException:
            #Should not be raised
            self.assertTrue(False)
        try:
            p.withdraw("USD", 1) #Not enough money
            self.assertTrue(False) #Should never be reached
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
