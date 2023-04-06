import logging
from ichat import *
import ccxt.async_support as ccxta  # noqa: E402
leftorders=[]


class SingleCoinPair(object):
    def __init__(self, coin, exchange1, exchange2):
        self.coin = coin
        self.exchange1 = exchange1
        self.exchange2 = exchange2

    def __hash__(self):
        return hash(self.coin + self.exchange1 + self.exchange2)

    def __eq__(self, other):
        ret1 = False
        ret2 = False
        if self.coin == other.coin and self.exchange1 == other.exchange1 and self.exchange2 == other.exchange2:
            #     ret1=True
            # if self.coin == other.coin and self.exchange1==other.exchange2 and self.exchange2==other.exchange1:
            #     ret2=True
            # if ret1 or ret2:
            return True
        else:
            return False


def getAccount(biance):
    try:
        accountinfo=biance.fetch_balance({'recvWindow': 10000000})
        return accountinfo
    except Exception as e:
        sendMsg(3,e)
        return None

class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

def upPrice(price):
    return price *1.001

def downPrice(price):
    return price*0.999



def getalltickers(biance,alltrades): #获取所有交易对行情
    try:
        tickers = biance.fetch_tickers(symbols=alltrades)
    except Exception as e:
        sendMsg(3, e)
        return None
    if tickers:
        return tickers

def getticker(biance,key):
    try:
        ticker = biance.fetch_ticker(key)
    except Exception as e:
        sendMsg(3, e)
        return None
    if ticker:
        return ticker

def createStopOrder(biance,symbol,type,side,amount,price,priprice):
    if type != 'TAKE_PROFIT' and type != 'STOP':
        sendMsg(1, 'create Stoporder error:type=' + str(type))
        return None
    try:
        order = biance.create_order(symbol, type, side, amount, price, {'recvWindow': 10000000, 'stopPrice': priprice})
    except Exception as e:
        sendMsg(1,'create Stoporder error:'+str(e))
        return None
    if order :
        sendMsg(1,'create order:'+str(order))
        return order

def createOrder(biance,symbol,type,side,amount,price):
    try:
        if type=='limit':
            order = biance.create_order(symbol,type, side, amount, price,{'recvWindow': 10000000})
        elif type=='market':
            order = biance.create_order(symbol, type, side, amount, {'recvWindow': 10000000})
    except Exception as e:
        sendMsg(3,'create order error:'+str(e))
        return None
    if order :
        sendMsg(1, 'create order :' + str(order))
        return order

async def asycreteOrder(exchange,symbol,type,side,amount,price,params):
    print(exchange.id + ' ' + symbol + ' ' + type + ' ' + side + ' ' + str(amount) + ' ' + str(price))
    try:
        if params:
            order = await exchange.create_order(symbol, type, side, amount, price,params)
        else:
            order = await exchange.create_order(symbol, type, side, amount, price)
        return order
    except ccxta.InsufficientFunds as e:
        sendMsg(3,'create_order() failed – not enough funds')
        sendMsg(3,e)
    except Exception as e:
        sendMsg(3,'create_order() failed')
        sendMsg(3,e)
    await exchange.close()



def fetchOrder(biance,id,symbol):
    sendMsg(1,'fetchorder:'+str(id))
    try:
        trade0 = biance.fetch_order(id, symbol, {'recvWindow': 10000000})
    except Exception as e:
        str1='fetch order error:'+str(id)+'@'+str(symbol)+str(e)
        sendMsg(3,str1)
        return None
    if trade0:
        return trade0

async def asyfetchOrder(exchange,id,symbol):
    try:
        trade0 = await exchange.fetch_order(id, symbol)
    except Exception as e:
        str1 = 'fetch order error:' + str(id) + '@' + str(symbol) + str(e)
        sendMsg(3, str1)
        return None
    if trade0:
        return trade0


def cancelOrder(biance,id,symbol):
    try:
        trade0 = biance.cancel_order(id,symbol,{'recvWindow': 10000000})
    except Exception as e:
        sendMsg(3,'failed to cancel order')
        sendMsg(3,e)
        return None
    if trade0:
        sendMsg(3,'ordercanceld:'+str(id)+trade0['id'])
        sendMsg(3,trade0)
        return trade0

async def asycancelOrder(exchange,id,symbol):
    try:
        trade0 = await exchange.cancel_order(id,symbol,{'recvWindow': 10000000})
    except Exception as e:
        sendMsg(3,'failed to cancel order')
        sendMsg(3,e)
        return None
    if trade0:
        sendMsg(3,'ordercanceld:'+str(id))
        sendMsg(3,trade0)
        return trade0

def getOrderStatus(biance,id,symbol):
    try:
        trade0 = biance.fetch_order(id, symbol, {'recvWindow': 10000000})
    except Exception as e:
        sendMsg(3,e)
        sendMsg(3,trade0)
        return None
    if trade0:
        return trade0['status']


def getDirectbyPrice(initPrice,lastPrice,profit):
    if profit > 0.00000001:
        if lastPrice > initPrice:
            return 'buy'
        else:
            return 'sell'
    else:
        if lastPrice > lastPrice:
            return 'sell'
        else:
            return 'buy'

def recaculateDistPrice(biance,key,lowprice,highprice,direct,multi):
    currentprice = getAccuratePrice(biance,key,direct)
    if currentprice:
        if direct=='sell':
            distprice=max(currentprice,highprice)-abs(max(currentprice,highprice)-lowprice)*0.618*(1-multi*0.08)
            distprice=upPrice(distprice)
            return distprice
        elif direct =='buy':
            distprice = min(currentprice,lowprice) + abs(highprice - min(currentprice,lowprice))*0.618*(1-multi*0.08)
            distprice = downPrice(distprice)
            return distprice
        else:
            return None

def getOrderbook(biance,key):
    orderbook=None
    try:
        orderbook = biance.fetch_order_book(key, 5, {'recvWindow': 10000000})
    except Exception as e:
        print(e)
    if orderbook:
        if orderbook["asks"][0] is not None and orderbook["bids"][0] is not None:
            return orderbook
        else:
            return None
    else:
        return None

def getRecentTrades(biance,key,num):
    rcntTrades = None
    try:
        rcntTrades = biance.fetch_trades(key, None, num, {'recvWindow': 10000000})
    except Exception as e:
        print(e)
    if rcntTrades:
        if rcntTrades[0] is not None:
            return rcntTrades
        else:
            return None
    else:
        return None






def getAccuratePrice(biance,key,direct):
    price = None
    orderbook = getOrderbook(biance, key)
    if orderbook is not None:
        if direct=='sell':
            if orderbook["asks"][0] is not None:
                price = orderbook["asks"][0][0]
        elif direct=='buy':
            if orderbook["bids"][0] is not None:
                price = orderbook["bids"][0][0]
    return price

def getOpsiteSide(side):
    if side=='sell':
        return 'buy'
    elif side == 'buy':
        return 'sell'
