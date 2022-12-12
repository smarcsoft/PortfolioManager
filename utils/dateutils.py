from datetime import date, datetime



def todatetime(date:date)->datetime:
    return datetime(date.year, date.month, date.day)