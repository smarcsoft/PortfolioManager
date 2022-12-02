import os
import unittest
from apitests import apitestsuite
from feedtests import feedtestsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(apitestsuite())
    # Change dir for feeders
    os.chdir("..")
    runner.run(feedtestsuite())
    