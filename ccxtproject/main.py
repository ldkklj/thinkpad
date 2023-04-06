
import ccxt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
import time

# from drawpic import *
# from analyse import *

df=pd.DataFrame()
#保存路径
path = 'C:\\'
def main():
    while True:
        records = _C(exchange.GetRecords)
        df_new = pd.DataFrame(records)
        df_new['Time'] = pd.to_datetime(df_new['Time'], unit='ms')
        df_new.index = df_new['Time']
        global df
        if df.empty or df_new['Time'].min() >= df['Time'].max():
             df=df.combine_first(df_new)
             temptm = df['Time'].max()
             print(df['Time'].max().strftime('%Y-%m-%d %H:%M:%S'))
        # if df_new['Time'].max() == pd.Timestamp('2020-06-30 22:22:00'):
        #      df=df.combine_first(df_new)
        #      df.to_csv(path+'records14.csv',index=False)
        #      break
        #休眠时间是选择周期
        time.sleep(1)
try:
    main()
except Exception as e:
    print(e)


