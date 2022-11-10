
import json
import os
import sys
import unittest
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(),'utils'))
sys.path.append(os.path.join(os.getcwd(),'../../..','utils'))
from feedutils import get_equity_database
from PMExceptions import PMException

class FundamentalData:
    def __init__(self, fd:dict) -> None:
        self._full = fd
        self._general = fd["General"]
        self._highlights = fd["Highlights"]
        self._valuation = fd["Valuation"]
        self._shares_stats = fd["SharesStats"]
        self._technicals = fd["Technicals"]
        self._splits_dividends = fd["SplitsDividends"]
        self._holders = fd["Holders"]
        self._insider_transactions = fd["InsiderTransactions"]
        self._outstanding_shares = fd["outstandingShares"]
        self._earnings = fd["Earnings"]
        self._financials = fd["Financials"]

    @staticmethod
    def load(full_ticker:str):
        '''
        from the ticker, read the database and return a new FundamentalData object
        '''
        db_loc = get_equity_database()
        (ticker, exchange) = full_ticker.split('.')
        file_loc = os.path.join(db_loc, exchange, ticker)+"/fd.json"
        if(os.path.exists(file_loc) == False):
            raise PMException("Could not find fundamental data for ticker " + full_ticker)
        with open(file_loc, 'rt') as fd:
            fd_content = fd.read()
            d = json.loads(fd_content)
            return FundamentalData(d)

    def __repr__(self) -> str:
        return str(self._full)

    def general(self)->dict:
        return self._general

    def highlights(self)->dict:
        return self._highlights

    def valuation(self)->dict:
        return self._valuation 

    def shares_stats(self)->dict:
        return self._shares_stats

    def splits_dividends(self)->dict:
        return self._splits_dividends

    def technicals(self)->dict:
        return self._technicals

    def holders(self)->dict:
        return self._holders

    def insider_transactions(self)->dict:
        return self._insider_transactions

    def outstanding_shares(self)->dict:
        return self._outstanding_shares

    def earnings(self)->dict:
        return self._earnings

    def financials(self)->dict:
        return self._financials   

class UnitTestFundamentalData(unittest.TestCase):
    def test_load(self):
        fd:FundamentalData = FundamentalData.load("WNC.US")
        self.assertEqual(len(fd.general()),34) 
        self.assertEqual(len(fd.highlights()),25) 
        self.assertEqual(len(fd.valuation()),7) 
        self.assertEqual(len(fd.shares_stats()),9) 
        self.assertEqual(len(fd.splits_dividends()),8) 
        self.assertEqual(len(fd.technicals()),9) 
        self.assertEqual(len(fd.holders()),2) 
        self.assertEqual(len(fd.insider_transactions()),20) 
        self.assertEqual(len(fd.outstanding_shares()),2) 
        self.assertEqual(len(fd.earnings()),3) 
        self.assertEqual(len(fd.financials()),3) 

    def test_missing(self):
        try:
            fd:FundamentalData = FundamentalData.load("ZINPAX.US")
            self.assertTrue(False)
        except PMException:
            self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
