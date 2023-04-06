import ccxt
import pandas as pd
from drawpic import *
from analyse import *
from gloabalfunc import *

biance = ccxt.binance()
biance.apiKey='vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y'
biance.secret='0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK'
biance.options['defaultType']='future'
biance.load_markets()
tradepairs=biance.markets

#order1 = biance.create_order('ZRX/USDT','limit','buy',1,'0.3988',{'recvWindow': 10000000})
# id = order1['id']

#order2 = biance.fetchOrders(symbol = undefined, since = undefined, limit = undefined, params = {'recvWindow': 10000000})
# biance.load_markets ()
# symbol = 'BTC/USDT'
# day = 24 * 60 * 60 * 1000
# start_time = biance.parse8601 ('2020-10-01T00:00:00')
# now = biance.milliseconds()
#
# all_trades = []
#
# while start_time < now:
#
#     print('------------------------------------------------------------------')
#     print('Fetching trades from', biance.iso8601(start_time))
#     end_time = start_time + day
#
#     trades = biance.fetch_my_trades (symbol, start_time, None, {
#         'endTime': end_time,'recvWindow': 10000000
#     })
#     if len(trades):
#         last_trade = trades[len(trades) - 1]
#         start_time = last_trade['timestamp'] + 1
#         all_trades = all_trades + trades
#     else:
#         start_time = end_time
#
# print('Fetched', len(all_trades), 'trades')
# for i in range(0, len(all_trades)):
#     trade = all_trades[i]
#     print (i, trade['id'], trade['datetime'], trade['amount'])

# price = getAccuratePrice(biance,'DOGE/USDT','sell')
# dd= price
#
#
# ohlc=biance.fetch_ohlcv('DOGE/USDT','15m',limit=50)
# #print(ohlc)
# df=pd.DataFrame(ohlc,columns=['time','open','high','low','close','0'],dtype='double')
# # print(df.columns)
# # print(df['time'])
# #df.set_index('0')
# # df.to_csv('records14.csv',index=False)
# # df = pd.read_csv('records14.csv', index_col='0')
# print(df.columns)
# dfbolling = dataAnalyseboll(df)
# add_plot = [mpf.make_addplot(dfbolling["BBANDS_upper"], color='y'),
#             mpf.make_addplot(dfbolling["BBANDS_middle"], color='r'),
#             mpf.make_addplot(dfbolling["BBANDS_lower"], color='b')]
# plotKLine(df, add_plot)


# balance = biance.fetch_balance({'recvWindow': 10000000})
# positions = balance['info']['positions']
# print(positions)
#
try:
    order1 = biance.create_order('SKL/USDT','market','buy',1,None,{'recvWindow': 10000000})
    #order1 = biance.fetch_order_book('SKL/USDT',5,{'recvWindow': 10000000})
except Exception as e:
    print(e)
dd=order1