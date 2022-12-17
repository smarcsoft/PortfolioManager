from datetime import date, datetime, timedelta



def todatetime(date:date)->datetime:
    if isinstance(date, datetime): return date
    return datetime(date.year, date.month, date.day)

def strtodatetime(s:str)->datetime:
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def get_last_business_day(date:date)->date:
    '''
    From a given date, return the last business day
    '''
    if(date.weekday()<5): return date
    diff = 1
    if date.weekday() == 5: #Saturday
        diff = 1
    elif date.weekday() == 6: #Sunday
        diff = 2
    return date - timedelta(days=diff)