import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def get_labels_from_identifiers(identifiers:list):
    to_return =[]
    for pi in identifiers:
        if(pi['type'] == 1): to_return.append(pi['id']['currency'])
        if(pi['type'] == 2): to_return.append(pi['id']['code'])
    return to_return

def profit_and_losses_chart(serie:pd.Series, date:datetime.date, currency:str):
    plt.style.use('seaborn-notebook')
    fig,ax = plt.subplots()
    y_pos = np.arange(len(serie.index))
    ax.barh(y_pos, serie.values)
    ax.set_yticks(y_pos, labels=serie.index)
    ax.set_title(f"Portfolio profit and loss by position in {currency} on {date}")
    ax.set_xlabel("USD")

def position_values_chart(serie:pd.Series, date:datetime.date, currency:str):
    plt.style.use('seaborn-notebook')
    fig,ax = plt.subplots()
    ax.pie(serie, labels = serie.index, labeldistance=None, wedgeprops=dict(width=0.3, edgecolor='w'))
    ax.legend(serie.index)
