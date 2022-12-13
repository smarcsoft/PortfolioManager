from datetime import date, datetime



def todatetime(date:date)->datetime:
    if isinstance(date, datetime): return date
    return datetime(date.year, date.month, date.day)

def strtodatetime(s:str)->datetime:
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')