class Ticker:
    def __init__(self, type:str, code:str, isin:str, name:str, country:str, exchange:str, currency:str):
        self._type= type
        self._code= code
        self._isin = isin
        self._name = name
        self._country = country
        self._exchange = exchange
        self._currency = currency
    
    
    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def country(self):
        return self._country

    @property
    def exchange(self):
        return self._exchange

    @property
    def currency(self):
        return self._currency

    @property
    def type(self):
        return self._type

    @property
    def isin(self):
        return self._isin


    def __repr__(self):
        return "Ticker {code} for {name} with isin={isin}".format(code = self._code, name = self._name, isin = self._isin)