from datetime import datetime, timedelta
import unittest
from Positions import Positions
from dateutils import todatetime 
from Portfolios import Portfolio
from PositionIdentifier import PositionIdentifier
from exceptions import PMException
import numpy as np
import pandas as pd

def profit_and_losses(portfolio:Portfolio, date1:datetime, date2:datetime, target_ccy:str)->dict:
    '''
    Returns the profit and losses of the portfolio and each of its constituents between 2 dates 
    The returns data structure is a dict
    dict['positions'] is a data frame containing the P&LS of each position in the portfolio
    dict['portfolio'] is a dict containing the P&Ls of the portfolio
    '''
    date1 = todatetime(date1)
    date2 = todatetime(date2)
    if(date1>date2): date1, date2 = date2, date1

    # Check of the portfolio can be valued at date1
    if(portfolio.get_start_date()>date1):
        raise PMException(f"Cannot compute profit and losses between {date1} and {date2} because {date1} is after the start date of the portfolio {portfolio.get_start_date()}")
    # Value each position at the 2 dates and compute differences and percentage gain or loss
    positions:Positions = portfolio.get_positions(date2)
    number_of_positions = len(positions)
    pandls = np.zeros(number_of_positions, dtype=np.float64)
    pandlspct = np.zeros(number_of_positions, dtype=np.float64)
    identifiers = []
    for i, pi in enumerate(positions):
        identifiers.append(pi.state())
        # Value the position at the 2 dates
        vd2 = portfolio.value_position(pi, date2, None, target_ccy)
        #Check if the position can be valued at date1
        earliestval = portfolio.get_earliest_valuation(pi)
        if (earliestval != None) and (earliestval > date1.date()): #The position exists at d2 but does not exists at d1
            vd1 = 0
        else:
            vd1 = portfolio.value_position(pi, date1, None, target_ccy)
        if(vd1 != 0):
            pandls[i] = vd2 - vd1
            pandlspct[i] = (vd2/vd1-1.0)*100
        else:
            pandls[i] = vd2
            pandlspct[i] = 0 
    # Create pandas dataframe from the underlying numpy arrays
    spandls = pd.Series(pandls, index = identifiers)
    spandlspct = pd.Series(pandlspct, index = identifiers)
    pandldf = pd.DataFrame({"pandls":spandls, "pandlspct":spandlspct}, columns=["pandls", "pandlspct"])
    #Evaluate the portfolio itself
    pv1=portfolio.valuator().get_valuation(date1)
    pv2=portfolio.valuator().get_valuation(date2)
    to_return={}
    to_return["positions"] = pandldf
    to_return["portfolio"]={"pandl_absolute":pv2-pv1, "pandl_pct":(pv2/pv1-1.0)*100}
    return to_return
        

class UnitTestAnalytics(unittest.TestCase):
    def test_prodit_and_losses(self):
        my_portfolio:Portfolio = Portfolio("DEFAULT", datetime(2021,1,18))
        my_portfolio.buy('MSCI', 2578, tags={'PERFORMANCE SHARES'}) #Performance shares
        my_portfolio.buy('MSCI', 3916, tags={'RESTRICTED SHARES'}) #Restricted shares
        my_portfolio.buy('MSCI', 1110, tags={'STOCK OPTIONS'}) #Stock options
        my_portfolio.buy('MSCI', 807, tags={'BROADRIDGE SHARES'})  #Bradridge shares
        my_portfolio.buy('MSCI', 3000, tags={'MORGAN STANLEY SHARES'})  #Bradridge shares
        my_portfolio.add('CHF', 14845)  # BCGE
        my_portfolio.add('EUR', 2000)   # N26
        my_portfolio.add('EUR', 1169)   # Boursorama
        my_portfolio.add('CHF', 387798) # UBS
        my_portfolio.add('CHF', 42233)  # Liechsteinstein
        my_portfolio.add('ETH', 32.9123, tags={'CRYPTOS'})
        my_portfolio.add('BTC', 2.2347, tags={'CRYPTOS'})
        my_portfolio.add('DOT', 1214.4988, tags={'CRYPTOS'})
        my_portfolio.add('CHF', 50000)
        my_portfolio.add('EUR', 1462.32, tags={'SWISSQUOTE'})
        my_portfolio.add('USD', 165928.14, tags={'SWISSQUOTE'})
        my_portfolio.buy('IPRP.SW', 235, tags={'SWISSQUOTE'})
        my_portfolio.buy('VUSA.SW', 800, tags={'SWISSQUOTE'})
        my_portfolio.buy('WSRUSA.SW', 489, tags={'SWISSQUOTE'})
        my_portfolio.buy('EFA', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('LCTU', 428, datetime(2021,4,8), tags={'SWISSQUOTE'})
        my_portfolio.buy('BCHN.LSE', 460, tags={'SWISSQUOTE'})
        my_portfolio.buy('STLA.PA', 2923, datetime(2021,1,18), tags={'SWISSQUOTE'})
        my_portfolio.buy('C40.PA', 320, tags={'SWISSQUOTE'})
        my_portfolio.add('EUR', 162045, tags={'LIFE INSURANCE'})
        my_portfolio.add('EUR', 75532, tags={'LIFE INSURANCE'})
        my_portfolio.add('CHF', 28724, tags={'LIFE INSURANCE'})
        my_portfolio.add('CHF', 8916, tags={'LIFE INSURANCE'})
        eval_date:datetime = datetime(2022,11,25)
        #Compute the P&L of the portfolio consituents between the last 2 days
        previous_day = eval_date - timedelta(days=1)
        pandls = profit_and_losses(my_portfolio, previous_day, eval_date, "USD")
        self.assertAlmostEqual(pandls['portfolio']['pandl_pct'], 0.52, delta=0.01)
        df:pd.DataFrame = pandls['positions']['pandls']
        df.plot()
        



if __name__ == '__main__':
    unittest.main()