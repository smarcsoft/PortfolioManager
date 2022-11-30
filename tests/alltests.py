import unittest
from apitests import apitestsuite
from feedtests import feedtestsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(apitestsuite())
    runner.run(feedtestsuite())
    