# -*- coding: utf-8 -*-

import asyncio
import ccxt
import ccxt.async_support as ccxta  # noqa: E402
import time
import os
import sys
import threading
import numpy as np
import copy
from gloabalfunc import *
from  ichat import *
import math

import json
from collections import OrderedDict
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

my_wallet ={}
openorderoffset= 0.005
closeoffset =0.002

huobi = ccxta.huobi({
    'apiKey': '146d5676-ur2fg6h2gf-5f6cff3b-50178',
    'secret': '40f5fa81-aee281b4-ae61fea3-fdea0',
})

binance = ccxta.binance({
    'apiKey': 'vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y',
    'secret': '0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK',
})

okex = ccxta.okex({
    'apiKey': '53edb788-6d50-45be-a44f-ebc2f448f8ef',
    'secret': '5EEE95F9706CD887CEB0982F49EDF338',
    'password': 'fevath12QW@',
})


mexc = ccxta.mexc({
    'apiKey': 'mx0WY9l3iaNYWXpvo8',
    'secret': '518ba4e088d4472a81fa55707090007b',
})
mexcn = ccxt.mexc({
    'apiKey': 'mx0WY9l3iaNYWXpvo8',
    'secret': '518ba4e088d4472a81fa55707090007b',
})


kucoin = ccxta.kucoin({
    'apiKey': '62a3e8bd2b57f600014eb518',
    'secret': '83dcc4b9-61e1-4e01-82cc-6bec1cfd8b3a',
    'password': 'fevath12QW@',
})
ftx = ccxta.ftx({
    'apiKey': '1OCXHzNKjXMrg7WtX4q8FS8QQUW523XoaQZCbaxJ',
    'secret': 'FCMpn3-qqX8okAnltR16hzTPIPd85jmj66JWH3Ve',
    'password': 'fevath12QW@',
})

exchanges = {}
exchanges['mexc'] = mexc
exchanges['binance'] = binance
# exchanges['okex'] = okex
exchanges['kucoin'] = kucoin
exchanges['ftx'] = ftx

flag=False

coindictnew={}
coinData={}
coinAnalyseRet={}
suggestCoin={}
coinManage={}
orderList={}
orderList['mexc']=[]
orderList['binance']=[]
# orderList['okex']=[]
orderList['ftx']=[]
orderList['kucoin']=[]
orderid=0

async def async_client(exchange_id,exchange,coin):
    orderbook = None
    try:
        start = time.time()
        orderbook = await exchange.fetch_order_book(coin[exchange_id]['symbol'])
        end = time.time()
        if end-start>0.5:
            print(exchange_id, time.strftime("!%H:%M:%S", time.localtime()),end-start)
    except Exception as e:
        print(type(e).__name__, str(e))
        await exchange.close()
    return { 'exchange': exchange.id, 'orderbook': orderbook }

async def  quickOpenOrder(exchange,symbol,priceSpot,amount,side):
    global orderList
    global orderid
    try:
        orderid+=1
        strorderid= 'order'+str(orderid)
        if exchange.id=='mexc':
            side1 = 1 if side == 'buy' else 3
            priceSpot = priceSpot if side=='buy' else priceSpot
            trade_type = 'ASK' if side == 'sell' else 'BID'
            order = await asycreteOrder(exchange,symbol,'limit',side1,amount,priceSpot,params={'openType':1,"trade_type":trade_type})
        else:
            order = await asycreteOrder(exchange,symbol,'limit',side,amount,priceSpot,None)
        if order:
            orderList[exchange.id].append(order)
            return order
    except Exception as e:
        print(type(e).__name__, str(e))
        return None

async def LeftMoney(exchange):
    ret ={}
    ret['pos']=[]
    try:
        balance = await exchange.fetch_balance()
        if balance:
            if balance.get('free'):
                kys= list(balance['free'].keys())
                for i in range(len(kys))[::-1]:
                    if balance['free'][kys[i]]<0.0001:
                        del balance['free'][kys[i]]
                return balance['free']
        else:
            return None
    except Exception as e:
        print('\n\nError in LeftMoney() ', e)
        time.sleep(1)
        return None


# async def getOrderbookpair(coin,ex1name,ex2name):
#     value = coindictnew[coin]['value']
#     input_coroutines = []
#     input_coroutines.append(async_client(ex1name, exchanges[ex1name], value))
#     input_coroutines.append(async_client(ex2name, exchanges[ex2name], value))
#     orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
#     i = 0
#     j = 1
    # if orderbooks[i]['orderbook'] and orderbooks[j]['orderbook'] \
    #         and len(orderbooks[i]['orderbook']['bids']) > 0 and len(orderbooks[j]['orderbook']['bids']) > 0:
    #    return {'bids0':orderbooks[i]['orderbook']['bids'][0][0],\
    #            'bids0Amt':orderbooks[i]['orderbook']['bids'][0][1],\
    #            'ask0':orderbooks[i]['orderbook']['asks'][0][0],\
    #            'ask0Amt':orderbooks[i]['orderbook']['asks'][0][1],\
    #            'bids1':orderbooks[j]['orderbook']['bids'][0][0],\
    #            'bids1Amt':orderbooks[j]['orderbook']['bids'][0][1],\
    #            'ask1':orderbooks[j]['orderbook']['asks'][0][0],\
    #            'ask1Amt':orderbooks[j]['orderbook']['asks'][0][1]}

def getOrderbookpair(orderbooks1,orderbooks2):
    return {'bids0': orderbooks1['orderbook']['bids'][0][0], \
            'bids0Amt': orderbooks1['orderbook']['bids'][0][1], \
            'ask0': orderbooks1['orderbook']['asks'][0][0], \
            'ask0Amt': orderbooks1['orderbook']['asks'][0][1], \
            'bids1': orderbooks2['orderbook']['bids'][0][0], \
            'bids1Amt': orderbooks2['orderbook']['bids'][0][1], \
            'ask1': orderbooks2['orderbook']['asks'][0][0], \
            'ask1Amt': orderbooks2['orderbook']['asks'][0][1]}

def getbookfromOrder(orderbook):
    return {
        'bid': orderbook['orderbook']['bids'][0][0],
        'ask': orderbook['orderbook']['asks'][0][0],
        'bidAmt': orderbook['orderbook']['bids'][0][1],
        'askAmt': orderbook['orderbook']['asks'][0][1],
    }

def loadjsonfile():
    global coinManage
    print('===============load suggestcoin===============')
    with open('suggestCoin.json', 'r') as f:
        suggestCoin = json.load(f)  # 解码JSON数据
    try:
        if len(suggestCoin):
            j=0
            for keystr in suggestCoin.keys():
                j+=1
                strlist = keystr.split('@')
                if len(strlist)==3:
                    coin = strlist[0]
                    exchange1 = strlist[1]
                    exchange2 = strlist[2]
                    coinKey = SingleCoinPair(coin,exchange1,exchange2)
                    if coinManage.get(coinKey):
                        coinManage[coinKey]= suggestCoin[keystr]
                        coinManage[coinKey]['active'] = 10000 - j
                    else:
                        if len(coinManage)<4:
                            coinManage[coinKey]= suggestCoin[keystr]
                            coinManage[coinKey]['active']=10000-j
            length = len(coinManage)
            if length >3:
                result = sorted(coinManage.items(), key=lambda x: x[1]['active'])
                for i in range(0,1):
                    del coinManage[result[i][0]]
    except Exception as e:
            sendMsg(3,'\n\nError in loadjsonfile()'+str(e))
            return None

async def managerpostion():
    global exchanges
    global coindictnew
    global coinManage

    try:
        for key in coinManage.keys():
            coin = key.coin
            totalcoin =0
            totalusdt =0
            value = coindictnew[coin]['value']
            maxusdtex =0.0
            maxex=''
            for ex in value.keys():
                if my_wallet[ex].get(coin):
                    totalcoin+=my_wallet[ex][coin]
                totalusdt+=my_wallet[ex]['USDT']
                if my_wallet[ex]['USDT'] > maxusdtex:
                    maxex = ex
                    maxusdtex = my_wallet[ex]['USDT']
            if coinManage[key].get('price'):
                price = coinManage[key]['price']
                margin = (totalusdt*0.2-price*totalcoin)/price
                if margin >0:
                    order = await quickOpenOrder(exchanges[maxex],value[maxex]['symbol'], price*1.01,33/price, 'buy')
                    if order:
                        if my_wallet[maxex].get(coin):
                            my_wallet[maxex][coin]+=33/price
                        else:
                            my_wallet[maxex][coin] = 33 / price
                        my_wallet[maxex]['USDT'] -= 33
            else:
                continue
    except Exception as e:
        sendMsg(3, '\n\nError in managerpostion()' + str(e))


async def refreshWallet():
    for exchangeName in exchanges.keys():
        leftmoney = await LeftMoney(exchanges[exchangeName])
        if leftmoney:
            my_wallet[exchangeName] = leftmoney

async def cancelallpendingorders():
    for exchangeid in orderList.keys():
        list = orderList[exchangeid]
        for i in range(len(list))[::-1]:
            order = await asyfetchOrder(exchanges[exchangeid], list[i]['id'], list[i]['symbol'])
            if order:
                if not order['status'] == 'closed':
                    cancelorder = await asycancelOrder(exchanges[exchangeid], order['id'], order['symbol'])
                    if cancelorder:
                        del list[i]
                else:
                    del list[i]

async def openorderPair(interval,book1,book2,coinAmt,exName1,exName2,coin,value,coinprice,type):
    global my_wallet
    if type =='balance':
        amount = coinAmt / 10
    else:
        amount = coinAmt / 5
    minamount = min(book1['askAmt'], book2['bidAmt'])
    amount = amount if amount < minamount else minamount
    amount = amount if amount * coinprice > 10 else 10 / coinprice
    if my_wallet[exName2].get(coin):
        if my_wallet[exName2][coin] > amount and my_wallet[exName1]['USDT'] > amount * coinprice:
            order1 = await quickOpenOrder(exchanges[exName1], value[exName1]['symbol'], book1['ask'], amount,'buy')
            order2 = await quickOpenOrder(exchanges[exName2], value[exName2]['symbol'], book2['bid'], amount,'sell')
            if order1:
                my_wallet[exName1]['USDT']-=amount * coinprice
            if order2:
                my_wallet[exName2][coin] -= amount
            if order1 and order2:
                str1 = str(coin) + str('@') + str(exName1) +format(book1['ask'],'.4f') +'@' +\
                       str(exName2) + format(book2['bid'],'.4f')+'@'+\
                       format(interval,'.4f') + ':' + str('amt:') + str(amount) + '@'+\
                       str('profit')+ format(interval*amount*coinprice,'.2f')
            else:
                str1='failde to open pair order!'
            await refreshWallet()
            sendMsg(3, str1)
        else:
            print('not enough coin')

async def managerorder():
    global exchanges
    global coindictnew
    global coinManage
    tick=0
    while True:
        tick+=1
        await asyncio.sleep(4)
        # ---------------load suggest coin---------
        #---------------check wallet usdt and coin amount---------
        # ---------------buy initial coin ---------
        if tick%1200==1:
            loadjsonfile()
        if tick%60==1:
            await cancelallpendingorders()
            await refreshWallet()
            await managerpostion()
            await refreshWallet()
        for key in coinManage.keys():
            coinManage[key]['active'] -= 1
            value = coindictnew[key.coin]['value']
            # start = time.time()
            input_coroutines = [async_client(exchangeName, exchanges[exchangeName], value) for exchangeName in value.keys()]
            orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
            # end  = time.time()
            # print(str('time ellapsed :')+format((end-start),'.4f'))
            for i in range(0, len(orderbooks)):
                for j in range(i, len(orderbooks)):
                    if i == j:
                        continue
                    else:
                        if not orderbooks[i] or not orderbooks[j] or not orderbooks[i].get('orderbook') or not orderbooks[j].get('orderbook'):
                            continue
                        exchange1 = orderbooks[i]['exchange']
                        exchange2 = orderbooks[j]['exchange']
                        coinAmt1=0
                        coinAmt2=0
                        if not my_wallet.get(exchange1):
                            continue
                        if not my_wallet.get(exchange2):
                            continue
                        if my_wallet[exchange1].get(key.coin):
                            coinAmt1=my_wallet[exchange1][key.coin]
                        if my_wallet[exchange2].get(key.coin):
                            coinAmt2=my_wallet[exchange2][key.coin]
                        if not coinAmt1==0 or not coinAmt2==0:
                            migrateCoinRatio =coinAmt1/(coinAmt1+coinAmt2)  #migrateCoinRatio范围0 ～1 ，0.5时不需要进行平衡
                        else:
                            migrateCoinRatio=0
                        book1 = getbookfromOrder(orderbooks[i])
                        book2 = getbookfromOrder(orderbooks[j])
                        coinprice = (book1['bid'] + book1['ask'] + book2['bid'] + book2['ask']) / 4
                        coinManage[key]['price']=coinprice
                        interal1= (book2['bid']-book1['ask'])/coinprice
                        interal2= (book1['bid']-book2['ask'])/coinprice
                        if interal1 <0.004 and interal1 >0.002 and migrateCoinRatio <0.2:  #只能平衡
                            str1 = str(key.coin) + str("-itvl1:") + format(interal1, '.4f') + str('itvl2') + \
                                   format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
                            print(str1)
                            coinManage[key]['active'] += 2
                            await openorderPair(interal1,book1,book2,coinAmt2,key.exchange1,
                               key.exchange2, key.coin, value, coinprice,'balance')
                        elif interal1 >0.004:
                            coinManage[key]['active'] += 4
                            str1 = str(key.coin) + str(":itvl1:") + format(interal1, '.4f') + str('itvl2') + \
                                   format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
                            print(str1)
                            await openorderPair(interal1,book1,book2,coinAmt2,key.exchange1,
                               key.exchange2, key.coin, value, coinprice,'profit')
                        if interal2 <0.004 and interal2 >0.002 and migrateCoinRatio>0.8:  #只能平衡
                            str1 = str(key.coin) + str(":itvl1:") + format(interal1, '.4f') + str('itvl2') + \
                                   format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
                            print(str1)
                            coinManage[key]['active'] += 2
                            await openorderPair(interal2,book2,book1,coinAmt1,key.exchange2,
                               key.exchange1, key.coin, value,coinprice, 'balance')
                        elif interal2 >0.004:
                            coinManage[key]['active'] += 4
                            str1 = str(key.coin) + str(":itvl1:") + format(interal1, '.4f') + str('itvl2') + \
                                   format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
                            print(str1)
                            await openorderPair(interal2,book2,book1,coinAmt1,key.exchange2,
                               key.exchange1, key.coin, value, coinprice,'profit')

async def run():
    global coindictnew

    # try:
    #     order =  mexcn.create_order('OLE/USDT', 'limit', 'buy', 164, 0.0766)
    # except Exception as e:
    #     sendMsg(3,'create_order() failed')
    #     sendMsg(3,e)
    with open('coindictnew.json', 'r') as f:
        coindictnew = json.load(f)  # 解码JSON数据
    tasklist=[]


    # th1=asyncio.create_task(managerpostion())
    # tasklist.append(th1)
    th2=asyncio.create_task(managerorder())
    tasklist.append(th2)
    result = await asyncio.gather(*tasklist)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

if __name__ == '__main__':
    main()