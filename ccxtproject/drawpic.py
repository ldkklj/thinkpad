import mplfinance as mpf
import pandas as pd
def plotKLine(data,add_plot):
    data['Time'] = pd.to_datetime(data['Time'], unit='ms')
    data.index=data['Time']
   # data.rename(columns={'open':'Open', 'close':'Close', 'high':'High','low':'Low','Time':'Date'}, inplace = True)
    data.rename(columns={'1': 'Open', '2': 'Close', '3': 'High', '4': 'Low', '0': 'Date'}, inplace=True)
   # mpf.plot(data, type='candle',style='yahoo',figratio=(2,1), figsize=(20,11),mav=(2, 5, 10))
    mpf.plot(data, type='candle', style='yahoo', addplot=add_plot,figratio=(2, 1), figsize=(20, 11))
    print(mpf.available_styles())




# import numpy as np
# import matplotlib.pyplot as plt
# import math
# x = np.arange(0.0002, 0.02, 0.001)
# y = []
# for t in x:
#     y_1 = math.pow(t, -0.4)*5
#     y.append(y_1)
#
#
# plt.plot(x,y,label="sin")
#
# plt.title('sin & cos')
# plt.legend()   #打上标签
# plt.show()
