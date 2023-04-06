import ccxt
import traceback
import queue
import pandas as pd
import time
import logging
import log
import threading
import asyncio
from gloabalfunc import *
from analyse import *
#from queue import PriorityQueue
from queue import Queue
from ichat import *
import websocket
import math


biance = ccxt.binance()
#69y 1
biance.apiKey='vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y'
biance.secret='0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK'
biance.options['defaultType']='future'
biance.load_markets()
tradepairs=biance.markets
tradepairs.pop('ETHUSDT_210625')
tradepairs.pop('BTCSTUSDT')
tradepairs.pop('BTCUSDT_210625')

records = Vividict()
allTradeQueue = Vividict()
acount = Vividict()
BALANCE_RATIO = 0.5

# tickers = biance.fetch_tickers(symbols=tradepairs)
#dd = biance.fetch_orders( {'recvWindow': 10000000})
#order1 = biance.create_order('CHZ/USDT','STOP','buy',5,0.47,{'recvWindow': 10000000,'stopPrice':0.47})
#oporder = biance.create_order('CRV/USDT', 'TAKE_PROFIT', 'buy', 82, 0.076,{'recvWindow': 10000000, 'stopPrice': 0.076})
#orderbook = biance.fetch_order_book('BTC/USDT', 5, {'recvWindow': 10000000})
# balance = biance.fetch_balance({'recvWzxcindow': 100000 00})
# positions = balance['info']['positions']
# print(positions)
#curl "https://fapi.binance.com/fapi/v1/premiumIndex?"
#以下定义一些常量
MAXTRADENUM =5


def updatePrice():
    orderbook={}
    for key in tradepairs:
        orderbook=getOrderbook(biance,key)
        if orderbook is not None:
            if orderbook["asks"][0] is not None and orderbook["bids"][0] is not None:
                bidPrice = orderbook["bids"][0][0] * 0.618 + orderbook["asks"][0][0] * 0.382
                bidPrice *= 1.0001
                askPrice = orderbook["bids"][0][0] * 0.382 + orderbook["asks"][0][0] * 0.618
                askPrice *= 0.9999
                price = (orderbook["bids"][0][0] + orderbook["asks"][0][0]) * 0.35 +\
                        (orderbook["bids"][1][0] + orderbook["asks"][1][0]) * 0.1 +\
                        (orderbook["bids"][1][0] + orderbook["asks"][1][0]) * 0.05
                allTradeQueue[key]['askPrice'] = askPrice
                allTradeQueue[key]['bidPrice'] = bidPrice
                if len(allTradeQueue[key]['prices'])>10:
                    allTradeQueue[key]['prices'].pop(0)
                allTradeQueue[key]['prices'].append(price)
                allTradeQueue[key]['orderbook']=orderbook

def initAllTradesData():
    for key in tradepairs:
        data = Vividict()
        data['prices'] = []
        data['askPrice'] = 0.0
        data['bidPrice'] = 0.0
        data['vol'] = 0
        data['lastTradeStamp'] = 0
        data['orders'] = {}
        data['oporders'] = {}
        data['postions'] =[]
        data['orderbook'] = {}
        data['burstPrice'] = 0.002
        data['trend'] = ''
        data['uptick'] = 0
        data['downtick'] = 0
        allTradeQueue[key] = data

def updateRectTrades():
    for key in tradepairs:
        rcntTrades = getRecentTrades(biance,key,20)
        if rcntTrades is not None:
            _sumamount = 0
            for i in len(rcntTrades):
                if rcntTrades[i]['timestamp'] > allTradeQueue[key]['lastTradeStamp']:
                    _sumamount += rcntTrades['amount']
            allTradeQueue[key]['vol'] = _sumamount*0.7 + allTradeQueue[key]['vol']*0.3
            allTradeQueue[key]['lastTradeStamp'] = rcntTrades[0]['timestamp']

def predealPosition(position):
    position = list(filter(lambda x: abs(float(x['positionAmt']))>0.00001, position))
    if len(position) > 0:
        position.sort(key=lambda x:float(x['unrealizedProfit']))
        return position
    else:
        return None


def getsidebypos(priceEntry,priceNow,profit):
    side = None
    if priceEntry > priceNow:
        if profit < 0:
           side = 'buy'
        else:
            side ='sell'
    else:
        if profit > 0:
            side = 'buy'
        else:
            side = 'sell'
    return side

def reduceSomeOrder(position,ite):
    if position is None:
        return
    #减少一个个最亏钱的仓位
    if len(position) > 0:
        pos = position[ite]
        key = biance.markets_by_id[pos['symbol']]['symbol']
        side = getsidebypos(float(pos['entryPrice']), allTradeQueue[key]['prices'][-1], float(pos['unrealizedProfit']))
        opside = 'buy' if side == 'sell' else 'sell'
        type = 'TAKE_PROFIT' #if float(pos['unrealizedProfit']) > 0 else 'STOP'
        priprice = allTradeQueue[key]['orderbook']['asks'][0][0] if opside =='sell' else allTradeQueue[key]['orderbook']['bids'][0][0]
        price = priprice*1.002 if opside =='sell' else priprice*0.998
        task2 = loop.create_task(createStopOrderuntilEnd(key, type, opside,abs(float(pos['positionAmt'])), price, priprice))
        task2.add_done_callback(stopcallback)
        loop.run_until_complete(task2)


def stopcallback(task):
    order = task.result()
    if order is not None:
        key = order['symbol']
        allTradeQueue[key]['oporders'] = order
        # direct = 'buy' if order['side']=='sell' else 'sell'
        # amount = order['amount']
        # task1 = loop.create_task(createOrderuntilEnd(key, allTradeQueue[key]['orderbook']['asks'][0][0], direct, amount))
        # task1.add_done_callback(callback)
        # loop.run_until_complete(task1)


async def createStopOrderuntilEnd(key,type,side,amount,price,priprice):
    order = createStopOrder(biance, key, type, side, amount, price, priprice)
    if order:
        orderid = order['id']
        tick = 0
        while True:
            if tick > 10:
                return None
            await asyncio.sleep(30)
            tick+=1
            order0 = fetchOrder(biance, orderid, key)
            if order0:
                if order0['status'] == 'closed':
                    return order0
                else:
                    if side =='buy':
                        cancelorder = cancelOrder(biance, orderid, key)
                        await asyncio.sleep(2)
                        if cancelorder is not None:
                            price = price*1.001
                            priprice = price*1.001
                            order = createStopOrder(biance, key, type, side, amount, price, priprice)
                            if order is not None:
                                orderid = order['id']
                                continue
                            else:
                                return None
                        else:
                            continue
                    else:
                        cancelorder = cancelOrder(biance, orderid, key)
                        await asyncio.sleep(2)
                        if cancelorder is not None:
                            price = price*0.999
                            priprice = price*0.999
                            order = createStopOrder(biance, key, type, side, amount, price, priprice)
                            if order is not None:
                                orderid = order['id']
                                continue
                            else:
                                return None
                        else:
                            continue
        return None


def balanceCoinMoney():
    _account = getAccount(biance)
    if _account is None:
        sendMsg(3,'balance get error')
        return
    else:
        positions = predealPosition(_account['info']['positions'])
        if positions:
            exitsymbols = [item['symbol'] for item in positions]
            exitkeys = []
            for key in exitsymbols:
                key = biance.markets_by_id[key]['symbol']
                exitkeys.append(key)
            keys = allTradeQueue.keys()
            notexitkeys = keys - exitkeys
            for key in notexitkeys:
                allTradeQueue[key]['oporders'] = {}
            for pos in positions:
                idx = positions.index(pos)
                ratio = float(pos['unrealizedProfit'])/float(pos['initialMargin'])
                if ratio <-0.25:
                    reduceSomeOrder(positions, idx)
                elif ratio > 0.6:
                    reduceSomeOrder(positions, idx)

        acount['leftmoney'] = _account['USDT']['free']
        acount['usedmoney'] = _account['USDT']['used']
        acount['totalmoney'] = _account['USDT']['total']
        acount['profit'] = float(_account['info']['totalUnrealizedProfit'])
        acount['positions'] = positions
        # if acount['totalmoney'] <0.00001:
        #     sendMsg(3,'run out of money')
        #     return
        # else:
        #     _p = acount['profit']/acount['totalmoney']
        #     if _p > 0.03:
        #         reduceSomeOrder(positions,-1)


def poll():
    for key in allTradeQueue:
        data = allTradeQueue[key]
        if len(data['prices']) < 7:
            return
        maxprice  = max(data['prices'][-6:-1])
        maxprice1 = max(data['prices'][-6:-2])
        minprice  = min(data['prices'][-6:-1])
        minprice1 = min(data['prices'][-6:-2])
        price =0

        if data['prices'][-1] > data['prices'][-2]:
            if ((data['prices'][-1]- maxprice)/maxprice > data['burstPrice'] ) or ((data['prices'][-1] - maxprice1) / maxprice1 )> data['burstPrice']:
                data['trend'] = 'bull'
                price=data['orderbook']['bids'][4][0]
                direct = 'buy'
                amount = acount['leftmoney'] * 0.001 * 40 /data['prices'][-1]
                data['uptick']+=1
                if data['uptick'] > 2:
                    data['uptick'] = 0
                    if not data['orders']:
                        task = loop.create_task(createOrderuntilEnd(key, price, direct, amount))
                        task.add_done_callback(callback)
                        loop.run_until_complete(task)
        elif data['prices'][-1] < data['prices'][-2]:
            if ((data['prices'][-1]- minprice)/minprice < -data['burstPrice'] ) or ((data['prices'][-1] - minprice1) / minprice1 )<-data['burstPrice']:
                data['trend'] = 'bear'
                price = data['orderbook']['asks'][4][0]
                direct = 'sell'
                amount = acount['leftmoney'] * 0.001 * 40 /data['prices'][-1]
                data['downtick'] += 1
                if data['downtick'] > 2:
                    data['downtick'] = 0
                    if not data['orders']:
                        task = loop.create_task(createOrderuntilEnd(key, price, direct, amount))
                        task.add_done_callback(callback)
                        loop.run_until_complete(task)
            else:
                data['trend'] = 'mid'


def callback(task):
    order = task.result()
    if order is not None:
        key = order['symbol']
        allTradeQueue[key]['orders'] = order
    else:
        return


# def createOppositeOrder(order):
#     key = order['symbol']
#     direct = order[]

async def createOrderuntilEnd(key,price,direct,amount):
    if  acount['positions']:
        if len(acount['positions'])>MAXTRADENUM :
            return
    if float(amount)*float(price) < 5.0:
        amount = 6.0/float(price)
    tick = 0
    order = createOrder(biance, key, 'limit', direct, amount, price)
    if order:
        orderid = order['id']
        while True:
            if tick >100:
                cancelOrder(biance, orderid, key)
                return
            await asyncio.sleep(1)
            tick += 1
            order0 = fetchOrder(biance, orderid, key)
            if order0:
                if order0['status']=='closed':
                    return order0
                else:
                    if order0['remaining'] < order0['amount'] and  order0['remaining']>0:
                        cancelOrder(biance, orderid, key)
                        continue
            else:
                await asyncio.sleep(20)
                tick += 20
    else:
        return

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def main():
    initAllTradesData()
    while True:
        updatePrice()
        balanceCoinMoney()
        poll()
        time.sleep(3)
try:
     main()
except Exception as e:
    sendMsg(3,e)
    traceback.print_exc()