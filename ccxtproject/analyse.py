import pandas as pd
import talib as talib
import numpy as np

pd.set_option('display.precision', 10)
def dataAnalyseboll(data):
    try:
        dftemp = pd.DataFrame()
        dftemp["BBANDS_upper"], dftemp["BBANDS_middle"], dftemp["BBANDS_lower"] = talib.BBANDS(np.array(data['close']), timeperiod=21)
    except Exception as e:
        print(e)
        return None
    return dftemp