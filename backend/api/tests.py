import unittest

from FundamentalData import UnitTestFundamentalData
from Portfolios import UnitTestPortfolio, UnitTestValuations
from PositionIdentifier import UnitTestTicker
from Positions import UnitTestPositions
from TimeSeries import UnitTestTimeSeries
from pmdata import UnitTestData


def suite():
    suite = unittest.TestSuite()
    suite.addTest(UnitTestFundamentalData('test_load'))
    suite.addTest(UnitTestFundamentalData('test_missing'))
    suite.addTest(UnitTestData('test_get_timeseries'))
    suite.addTest(UnitTestData('test_get_ticker'))
    suite.addTest(UnitTestData('test_multiple_search'))
    suite.addTest(UnitTestData('test_hot_search'))
    suite.addTest(UnitTestPortfolio('test_buy'))
    suite.addTest(UnitTestPortfolio('test_positions'))
    suite.addTest(UnitTestPortfolio('test_sell_short'))
    suite.addTest(UnitTestPortfolio('test_cash'))
    suite.addTest(UnitTestPortfolio('test_cash_short'))
    suite.addTest(UnitTestPortfolio('test_sell_what_you_do_not_have'))
    suite.addTest(UnitTestPortfolio('test_portfolio_group1'))
    suite.addTest(UnitTestPortfolio('test_portfolio_group2'))
    suite.addTest(UnitTestPortfolio('test_portfolio_tags'))
    suite.addTest(UnitTestValuations('test_get_valuations'))
    suite.addTest(UnitTestValuations('test_get_start_date'))
    suite.addTest(UnitTestValuations('test_portfolio'))
    suite.addTest(UnitTestValuations('test_portfolio_group'))
    suite.addTest(UnitTestValuations('test_portfolio_group2'))
    suite.addTest(UnitTestValuations('test_get_end_date'))
    suite.addTest(UnitTestValuations('test_dp'))
    suite.addTest(UnitTestValuations('test_cash'))
    suite.addTest(UnitTestValuations('test_index_valuation'))
    suite.addTest(UnitTestTicker('test_ticker'))
    suite.addTest(UnitTestTicker('test_ticker_equal'))
    suite.addTest(UnitTestTicker('test_position_identifier_hash'))
    suite.addTest(UnitTestTicker('test_currency'))
    suite.addTest(UnitTestTicker('test_positionIdentifier'))
    suite.addTest(UnitTestPositions('test_positions_tags'))
    suite.addTest(UnitTestTimeSeries('test_iadd'))
    suite.addTest(UnitTestTimeSeries('test_add'))
    suite.addTest(UnitTestTimeSeries('test_isub'))
    suite.addTest(UnitTestTimeSeries('test_sub'))
    suite.addTest(UnitTestTimeSeries('test_mul'))
    suite.addTest(UnitTestTimeSeries('test_div'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())