from datetime import date, datetime



def todatetime(date:date)->datetime:
    return datetime(date.year, date.month, date.day)

def strtodatetime(s:str)->datetime:
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')