from TimeSeries import TimeSeries
import pandas as pd
import matplotlib.pyplot as plt 

def graph_time_series(ts:TimeSeries):
    # We are getting access to the underlying Numpy array in order to graph it
    tsv = ts.get_full_time_series()
    # We are getting access to the dates in order to display them on the horizontal axis
    dates = pd.date_range(ts.get_start_date(), ts.get_end_date(), freq='D')
    # And we graph the data with style
    plt.style.use('bmh')
    fig, ax = plt.subplots()
    ax.set_title("Portfolio valuation example")
    ax.set_ylabel("USD")
    adjusted_close_line, = ax.plot(dates, tsv, linewidth=1)
    fig.legend((adjusted_close_line,), ('Adjusted close valuation',), loc='lower left')
    plt.show()

