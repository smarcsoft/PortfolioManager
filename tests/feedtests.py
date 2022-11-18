import unittest
from fdfeed import UnitTestFDFeeder

from feeder import UnitTestFeeder
from fxfeed import UnitTestFXFeeder


def feedtestsuite():
    suite = unittest.TestSuite()
    suite.addTest(UnitTestFeeder('test_full_load'))
    suite.addTest(UnitTestFeeder('test__get_last_date'))
    suite.addTest(UnitTestFeeder('test_update_load'))
    suite.addTest(UnitTestFeeder('test__get_next_last_date'))
    suite.addTest(UnitTestFXFeeder('test_fx_load'))
    suite.addTest(UnitTestFDFeeder('test_fd_load'))
    suite.addTest(UnitTestFDFeeder('check_fd_load'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(feedtestsuite())