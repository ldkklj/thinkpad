import pandas as pd
from drawpic import *
from analyse import *


df = pd.read_csv('records15.csv')
dfbolling = dataAnalyse(df)
add_plot = [mpf.make_addplot(dfbolling["BBANDS_upper"], color='y'),
            mpf.make_addplot(dfbolling["BBANDS_middle"], color='r'),
            mpf.make_addplot(dfbolling["BBANDS_lower"], color='b')]
df['Time']=pd.to_datetime(df['0'],unit='ms')
plotKLine(df, add_plot)