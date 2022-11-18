import unittest
from FundamentalData import UnitTestFundamentalData
from Portfolios import UnitTestPortfolio, UnitTestValuations
from PositionIdentifier import UnitTestTicker
from Positions import UnitTestPositions
from TimeSeries import UnitTestTimeSeries
from pmdata import UnitTestData
from apitests import apitestsuite
from feedtests import feedtestsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(apitestsuite())
    runner.run(feedtestsuite())