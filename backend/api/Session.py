from datetime import date, datetime
import json
import os
import pickle
import re
from shutil import rmtree
from typing import TypedDict
import unittest
 
from Portfolios import Portfolio
from PositionIdentifier import CASH, EQUITY
from exceptions import PMException
from config import get_config, init_logging
from os.path import exists

class User(TypedDict):
    first_name:str
    last_name:str
    email:str

    

class Session:
    def __init__(self, login_time:datetime, user:User):
        self.login_time = login_time
        self.activity:list=[]
        self.user = user

    def get_login_time(self):
        return self.login_time

    def save_portfolio(self,portfolio:Portfolio):
        p:dict = portfolio.state()
        db_loc = get_config("DB_LOCATION")
        user_dir = os.path.join(db_loc,"USERS", self.user["email"])
        user_portfolio_dir = os.path.join(user_dir,"PORTFOLIOS")
        if(not exists(user_portfolio_dir)):
            # Create the directory
            os.mkdir(user_portfolio_dir)
        portfolio_file = os.path.join(user_portfolio_dir, portfolio.get_name()+".json")
        with open(portfolio_file, "wt") as pf:
            json.dump(p, pf)

    def load_portfolio(self, name:str)->Portfolio:
        db_loc = get_config("DB_LOCATION")
        user_dir = os.path.join(db_loc,"USERS", self.user["email"])
        user_portfolio_dir = os.path.join(user_dir,"PORTFOLIOS")
        portfolio_file = os.path.join(user_portfolio_dir, name+".json")
        if(not os.path.exists(portfolio_file)):
            raise PMException(f"Could not find portfolio {name} in database")
        with open(portfolio_file, "rt") as pf:
            portfolio_state = json.load(pf)
        return self._unmarshall_portfolio(portfolio_state)
        
    def _unmarshall_portfolio(self, state:dict)->Portfolio:
        # Recreate the portfolio from its state
        toreturn:Portfolio=Portfolio(state['name'])
        positions = state['positions']
        for position in positions:
            position_identifier = position['identifier']
            position_amount = position['amount']
            if(position_identifier['type'] == EQUITY): 
                toreturn.buy(position_identifier['id']['code']+'.'+position_identifier['id']['virtual_exchange'], position_amount, set(position_identifier['tags']))
            if(position_identifier['type'] == CASH): 
                toreturn.add(position['identifier']['id']['currency'], position_amount, set(position_identifier['tags']))
        return toreturn


class SessionEncoder(json.JSONEncoder):

    def default(self, object):
        if isinstance(object, Session):
            return object.__dict__
        else:
            return json.JSONEncoder.default(self, object)

def _session_decoder(session:dict):
    toreturn = Session(datetime.strptime(session['login_time'], "%Y-%m-%d-%H-%M-%S"),session['user'] )
    toreturn.activity = session['activity']
    return toreturn

def get_last_login(u:User)->datetime:
    '''
    Get the last time the user logged in
    '''
    session:Session = get_last_session(u)
    return session.get_login_time()

def get_last_session(user:User)->Session:
    '''
    Get the last session created for the user
    '''
    db_loc = get_config("DB_LOCATION")
    user_dir = os.path.join(db_loc,"USERS", user["email"])
    user_session_dir = os.path.join(user_dir,"SESSIONS")
    session_file = os.path.join(user_session_dir,"last_session.json")
    with open(session_file, "rt") as l:
        session_dict = json.load(l)
    return Session(datetime.strptime(session_dict['login_time'], "%Y-%m-%d-%H-%M-%S"), user)

def create_user(first_name:str, last_name:str, email:str, overwrite:bool=False)->User:
    '''
    Creates or update a user in the database.
    Returns the newly created user with first_name, last_name and email as fields in the dictionary 
    '''
    if(not check_email(email)):
        raise PMException("Invalid email address {email}".format(email=email))
    db_loc = get_config("DB_LOCATION")
    users = os.path.join(db_loc,"USERS")
    if(not exists(users)):
        # Create the directory
        os.mkdir(users)
    # Check if user already exists
    user_dir = os.path.join(users, email)
    if(not exists(user_dir)):
        # Create the directory
        os.mkdir(user_dir)
    
    u:User={"first_name":first_name, "last_name":last_name, "email":email}
    user_file = os.path.join(user_dir, "user.json")
    if(exists(user_file) and (not overwrite)):
        raise PMException("User {user} already exists.".format(user=email))
    with open(user_file, "wt") as f:
        json.dump(u,f)
    return u

def check_email(email:str)->bool:
    '''
    Checks the format of the email address provided
    '''
    pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.match(pat,email):
        return True
    else:
        return False

def get_user(email:str)->User:
    '''
    Get the user from the database
    '''
    if(not check_email(email)):
        raise PMException("Invalid email address {email}".format(email=email))
    db_loc = get_config("DB_LOCATION")
    user_dir = os.path.join(db_loc,"USERS", email)
    if(not exists(user_dir)):
        raise PMException(f"User {email} does not exist")
    with open(os.path.join(user_dir,"user.json"), "rt") as f:
        return json.load(f)

def delete_user(user:User):
    '''
    Delete a user from the database
    '''
    db_loc = get_config("DB_LOCATION")
    user_dir = os.path.join(db_loc,"USERS", user["email"])
    if(not exists(user_dir)):
        raise PMException("User {email} does not exist".format(email=User["email"]))
    rmtree(user_dir)


def create_session(user:User)->Session:
    '''
    Creates a new session for the user
    '''
    db_loc = get_config("DB_LOCATION")
    user_dir = os.path.join(db_loc,"USERS", user["email"])
    user_session_dir = os.path.join(user_dir,"SESSIONS")
    if(not exists(user_session_dir)):
        os.mkdir(user_session_dir)
    login_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    session_file = os.path.join(user_session_dir,"session_" + login_time +".json")
    session:Session = Session(login_time, user)
    with open(session_file, "wt") as f:
        json.dump(session, f, cls=SessionEncoder)
    # Save the last session in a specific file for easier access
    session_file = os.path.join(user_session_dir,"last_session.json")
    with open(session_file, "wt") as l:
        json.dump(session, l, cls=SessionEncoder)
    return session



class UnitTestSession(unittest.TestCase):

    def test_a_new_user(self):
        # Should succeed
        create_user("Sebastien", "Test", "sebTest@yahoo.com")
        try:
            create_user("Sebastien", "Test", "sebTest@yahoo.com")
            self.fail("Should not have been able to create the user as it already exists")
        except PMException:
            self.assertTrue(True)

    def test_b_get_user(self):
        user = get_user("sebTest@yahoo.com")
        self.assertTrue(user["first_name"] == "Sebastien")
        try:
            get_user("another@yahoo.com")
        except PMException:
            self.assertFalse(False)
            return
        self.fail("Should not have been there")

    def test_f_delete_user(self):
        user = get_user("sebTest@yahoo.com")
        delete_user(user)

    def test_c_new_session(self):
        user = get_user("sebTest@yahoo.com")
        create_session(user)
    
    def test_d_last_login(self):
        user = get_user("sebTest@yahoo.com")
        self.assertTrue((datetime.today() - get_last_login(user)).days == 0)

    def test_e_portfolio_save_and_load(self):
        user = get_user(email="sebTest@yahoo.com")
        session:Session =  create_session(user)
        # Create my portfolio
        my_portfolio:Portfolio = Portfolio()
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
        my_portfolio.add('EUR', 1462.32, tags={'SWISSQUOTE'})
        my_portfolio.add('USD', 165928.14, tags={'SWISSQUOTE'})
        my_portfolio.buy('IPRP.SW', 235, tags={'SWISSQUOTE'})
        my_portfolio.buy('VUSA.SW', 800, tags={'SWISSQUOTE'})
        my_portfolio.buy('WSRUSA.SW', 489, tags={'SWISSQUOTE'})
        my_portfolio.buy('EFA', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('LCTU', 428, tags={'SWISSQUOTE'})
        my_portfolio.buy('BCHN.LSE', 460, tags={'SWISSQUOTE'})
        my_portfolio.buy('STLA.PA', 2923, tags={'SWISSQUOTE'})
        my_portfolio.buy('C40.PA', 320, tags={'SWISSQUOTE'})
        my_portfolio.add('EUR', 162045, tags={'LIFE INSURANCE'})
        my_portfolio.add('EUR', 75532, tags={'LIFE INSURANCE'})
        my_portfolio.add('CHF', 28724, tags={'LIFE INSURANCE'})
        my_portfolio.add('CHF', 8916, tags={'LIFE INSURANCE'})
        my_portfolio.buy('ACWI.PA', 76, tags={'FRANCE'})
        session.save_portfolio(my_portfolio)
        # Load the portfolio back
        loaded_portfolio = session.load_portfolio("DEFAULT")
        # Value the 2 portfolios and check if the valuations are identical
        val1 = loaded_portfolio.valuator().get_valuation(date(2022,11,27))
        val2 = my_portfolio.valuator().get_valuation(date(2022,11,27))
        self.assertEqual(val1, val2)

if __name__ == '__main__':
    init_logging()
    unittest.main()
