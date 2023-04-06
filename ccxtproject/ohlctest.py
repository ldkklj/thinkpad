#!/usr/bin/env python
# -*- coding: utf-8 -*
#import ccxtpro
import ccxt
import traceback
import queue
import pandas as pd
import time
import logging
import log
import threading
from gloabalfunc import *
from analyse import *
#from queue import PriorityQueue
from queue import Queue
from ichat import *
import math


mylock = threading.Lock()



CONST_INTERVEL =4
CONST_LISTLEN  =12
CONST_TRIGERRATIO=0.01

VERYSMALLNUM=0.00000001
MAXTRADENUM=3     #同时处理的交易对上限
TIMEOUTTICK=60      #超时撤销订单的超时时间
TOLERANCE = 0.02   #加单或者止损点比例
LEVERAGE  = 40      #杠杆比例
OFFSET = 0.001

ratioAddList=[1,2,3,3,4,5,10,10,10]
itvList=[1,2,3,4,5,6,7,8,9]
# huobi =ccxt.binance({
#     'proxies': {
#         'http': 'http://hk1.sgateway.link:706',  # these proxies won't work for you, they are here for example
#         'https': 'https://hk1.sgateway.link:706',
#     },
# })
#huobi = ccxt.huobipro()
#huobi.apiKey='nbtycf4rw2-1b169836-b567486a-26fda'
#huobi.secret='9da5a95d-5aa90559-83b540fb-e0e69'
#huobi.hostname='api.btcgateway.pro'
#huobi.proxies='https://127.0.0.1:1080'

##print(balance)

# huobi.load_markets()
# data = huobi.markets()
# data1 =data

biance = ccxt.binance()
#69y 1
biance.apiKey='vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y'
biance.secret='0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK'
biance.options['defaultType']='future'
biance.load_markets()
tradepairs=biance.markets

queue = Queue()

#log.createlogfile()

records = Vividict()

allTradeQueue = Vividict()

records.fromkeys(tradepairs)
for key in tradepairs:
    records[key]['data'] = []
    market=biance.market(key)
    leverage = LEVERAGE #合约杠杆
    try:
        response = biance.fapiPrivate_post_leverage({'symbol': market['id'],'leverage': leverage,'recvWindow': 10000000})
    except Exception as e:
        print(e)


def getSidebyTrend(trend):
    side =''
    if trend == 'up':
        side = 'sell'
    elif trend == 'down':
        side = 'buy'
    return side

def checklogic(side,result):
    ret = False
    if side == 'sell':
        if (result['priceH']-result['price'])/result['price']>0.01:
            ret = True
    elif side == 'buy':
        if (result['priceH'] - result['price']) / result['price'] < 0.005:
            ret = True
    return ret

def insertPriOrderlist():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        mylock.acquire()
        if not queue.empty():
            try:
                task = queue.get()
                symbol = task['symbol']
                type = task['type']
                ifhas = allTradeQueue.get(symbol)
                if type == 'create':
                    if len(allTradeQueue) >= MAXTRADENUM:
                        mylock.release()
                        continue
                elif type == 'op':
                    if ifhas:
                        if allTradeQueue[symbol]['status']=='alldeal':
                            cancelAllOpenOrder(symbol)
                            trade = allTradeQueue[symbol]
                            order = createOrder(biance, symbol, 'market', getOpsiteSide(trade['side']), trade['remainamount'])
                            if order is not None:
                                allTradeQueue.pop(symbol)
                elif type =='end':
                    if ifhas:
                        if allTradeQueue[symbol]['status'] == 'alldeal':
                            cancelAllOpenOrder(symbol)
                            trade = allTradeQueue[symbol]
                            order = createOrder(biance, symbol, 'market', getOpsiteSide(trade['side']),trade['remainamount'])
                            if order is not None:
                                allTradeQueue.pop(symbol)
                            mylock.release()
                            continue

            except Exception as e:
                sendMsg(3,e)
                traceback.print_exc()
                mylock.release()
                continue
        mylock.release()
        time.sleep(1)
    loop.close()

def dealallorders():
    while True:
        mylock.acquire()
        managerOrderstatus()
        createCoverOrder()
        StopLossOrAddPositon()
        mylock.release()
        time.sleep(2)


def getBollingResult(biance,key,period='15m'):
    result={}
    try:
        ohlc15 = biance.fetch_ohlcv(key, period, limit=60)
    except Exception as e:
        sendMsg(3,e)
        return None
    try:
        df = pd.DataFrame(ohlc15, columns=['time', 'open', 'high', 'low', 'close', 'vol'],dtype='double')
        currentprice = df.iat[-1, 4]
        dfbolling =dataAnalyseboll(df)
        if dfbolling is not None:
            result['upper'] = dfbolling["BBANDS_upper"].iloc[-1]
            result['lower'] = dfbolling["BBANDS_lower"].iloc[-1]
            result['middle'] = dfbolling["BBANDS_middle"].iloc[-1]
            result['mouth'] = result['upper']-result['lower']
            result['currentprice'] = currentprice
            return result
    except Exception as e:
        sendMsg(3,e)
        return None




def removeUnstablePairs():
    # 获取最近3天的成交量，移除交易量太小的交易对
    tradepairs.pop('IOST/USDT')
    tradepairs.pop('DOGE/USDT')
    volumelist = {}
    badpairs = []
    for trade in tradepairs:
        ohlcv=biance.fetch_ohlcv(trade, '1d')
        if len(ohlcv) < 4:
            badpairs.append(trade)
            continue
        avgVolume5d=(ohlcv[-1][5]*ohlcv[-1][4]+ohlcv[-2][5]*ohlcv[-2][4]+ohlcv[-3][5]*ohlcv[-3][4])/3
        volumelist[trade]=avgVolume5d
    volumelist =sorted(volumelist.items(),key=lambda x:x[1],reverse=True)
    keys=[]
    for each in volumelist[-5:]:
        keys.append(each[0])
    for key in keys:
        tradepairs.pop(key)
    for pair in badpairs:
        tradepairs.pop(pair)


def managerOrderstatus():
    endlist={}
    for key in allTradeQueue:
        trade = allTradeQueue[key]
        #更新高/低价
        ticker=getticker(biance,key)
        if ticker:
            currentprice=ticker['last']
            if trade['side']=='sell' and currentprice > trade['priceH']:
                trade['priceH']=currentprice
            elif  trade['side']=='buy' and currentprice < trade['priceL']:
                trade['priceL']=currentprice
        #遍历order列表，累加已成交的数量
        trade['remainamount'] = 0.0
        trade['remainusdt'] = 0.0
        trade['dealordercnt'] = 0
        if trade.get('orderlist'):
            if len(trade['orderlist'])>0:  #已创建初始单
                for i in range(len(trade['orderlist'])):
                    if trade['orderlist'][i]['status'] == 'closed':
                        order0=trade['orderlist'][i]
                        
                        trade['dealordercnt'] += 1
                        trade['remainamount'] += order0['amount']
                        trade['remainusdt'] += order0['amount'] * order0['price']
                    else:
                        order0 = fetchOrder(biance, trade['orderlist'][i]['id'], key)
                        if order0:
                            trade['orderlist'][i] = order0
                            if order0['status'] == 'closed':
                                trade['dealordercnt'] +=1
                                trade['remainamount'] += order0['amount']
                                trade['remainusdt']+=order0['amount']*order0['price']
                if  trade['dealordercnt'] == len(trade['orderlist']):#所有的订单都已成交
                    trade['status']='alldeal'
                elif  trade['dealordercnt'] < len(trade['orderlist']):
                    if trade['dealordercnt'] > 0:
                        trade['status']='partdeal'

        #查看平单状态
        if trade.get('coverorderlist'):
            if len(trade['coverorderlist']) > 0:
                for j in range(len(trade['coverorderlist'])):
                    coverorder0 = trade['coverorderlist'][j]
                    if coverorder0['status'] == 'closed':
                        trade['remainamount'] -= coverorder0['amount']
                        trade['remainusdt'] -= coverorder0['amount'] * coverorder0['price']
                    elif coverorder0['status'] == 'canceled':
                        continue
                    else:
                        coverorder1 = fetchOrder(biance, trade['coverorderlist'][j]['id'], key)
                        if coverorder1 is not None:
                            trade['coverorderlist'][j] = coverorder1
                            #平单已生效且与订单成交总量一致
                            if coverorder1['status']=='closed':
                                trade['remainamount'] -= coverorder1['amount']
                                trade['remainusdt'] -= coverorder1['amount'] * coverorder1['price']
        if trade['remainamount']<-VERYSMALLNUM:
            sendMsg(3,"出现错误，平单数量超过开单数量！")
            sendMsg(3,trade)
        elif abs(trade['remainamount']) < VERYSMALLNUM and trade.get('coverorderlist'):
            if trade['status'] == 'alldeal':
                endlist[key]=0
                sendMsg(3,"订单成功结束")
                sendMsg(3,trade)
                continue
        #计算当前持仓价格
        if abs(trade['remainamount']>VERYSMALLNUM):
            trade['remainprice']=trade['remainusdt']/trade['remainamount']
        currentprice = getAccuratePrice(biance,key,trade['side'])
        if currentprice is not None:
            if trade['side'] == 'sell':
                ratio = (currentprice - trade['price'])/trade['price']
                if currentprice > trade['priceH']:
                    trade['priceH'] = currentprice
                    trade['passcount'] += 1
                    trade['lefttick'] -= 900
            elif trade['side'] == 'buy':
                ratio = (trade['price']-currentprice)/trade['price']
                if currentprice < trade['priceL']:
                    trade['priceL'] = currentprice
                    trade['passcount'] += 1
                    trade['lefttick'] -= 900
            if ratio <0.0002:
                ratio = 0.0002
            delta=ratio*100000+math.pow(abs(ratio), -0.4)*3
            trade['lefttick']-=delta
            trade['price']=currentprice
        sendMsg(1,str(key)+str(trade['lefttick'])+'--ratio:'+str(ratio)+'--delta:'+str(delta)+'passcount'+str(trade['passcount']))
        inteval = time.time()-trade['starttime']
        if trade['status']=='created':
            if inteval> TIMEOUTTICK:
                endlist[key]=0
                if trade.get('orderlist'):
                    sendMsg(3,'timeout,cancel order')
                    cancelOrder(biance, trade['orderlist'][0]['id'], key)
                continue
        if trade.get('stoplossoerder'):
            slorder = fetchOrder(biance, trade['stoplossoerder']['id'], key)
            if slorder:
                if slorder['status'] == 'closed':
                    sendMsg(3,'success failed')
                    endlist[key]=0
        allTradeQueue[key] = trade
    for key1 in endlist.keys():
        allTradeQueue.pop(key1)
        sendMsg(3,str('pop key:')+str(key1))



def createSingelCoverOrder(key,tradeside,disprice,amount):
    ticker = getticker(biance, key)
    if ticker:
        if tradeside == 'buy':
            if ticker['last'] < disprice:
                price = disprice
                direct = 'sell'
            else:
                price = upPrice(ticker['last'])
                direct = 'sell'
        else:
            if ticker['last'] > disprice:
                price = disprice
                direct = 'buy'
            else:
                price = downPrice(ticker['last'])
                direct = 'buy'
        order = createOrder(biance, key, 'limit', direct, amount, price)
        if order :
            return order
    return None


def createCoverOrder():
    for key in allTradeQueue:
        trade = allTradeQueue[key]
        if trade['status'] != 'alldeal':
            continue
        if not trade.get('orderlist'):
            continue
        # 重新计算目标价
        isdistpricechanged = False
        multi = 0
        if trade.get('orderlist'):
            multi = len(trade['orderlist'])
        newDistprice = recaculateDistPrice(biance, key, trade['priceL'], trade['priceH'], trade['side'],multi)
        if newDistprice:
            if trade['side'] == 'buy':
                if newDistprice < trade['distPrice']   and newDistprice > trade['remainprice'] and abs(newDistprice-trade['distPrice'])/newDistprice>0.0002:
                    trade['distPrice'] = newDistprice
                    isdistpricechanged = True
            elif trade['side'] == 'sell':
                if newDistprice >trade['distPrice']  and newDistprice < trade['remainprice']and abs(newDistprice-trade['distPrice'])/newDistprice>0.0002:
                    trade['distPrice'] = newDistprice
                    isdistpricechanged = True
        if trade['status'] == 'alldeal' or trade['status'] == 'partdeal': #有已成交单子
            if not trade.get('coverorderlist'):
                order = createSingelCoverOrder(key, trade['side'], trade['distPrice'], trade['remainamount'])
                if order:
                    trade['coverorderlist'] = []
                    trade['coverorderlist'].append(order)
            else:
                if len(trade['coverorderlist']) >0:
                    if trade['remainamount'] > VERYSMALLNUM:
                        # for covertrade in trade['coverorderlist']:
                        #     if covertrade['status'] == 'open' and abs(covertrade['remaining']-covertrade['amount'])<VERYSMALLNUM:
                        covertrade = trade['coverorderlist'][-1]
                        if covertrade['status'] == 'open' and abs(covertrade['remaining'] - covertrade['amount']) < VERYSMALLNUM:
                            if covertrade['amount'] < trade['remainamount'] or isdistpricechanged:
                                canceled = cancelOrder(biance, covertrade['id'], key)
                                if canceled:
                                    del trade['coverorderlist'][-1]
                                    order = createSingelCoverOrder(key, trade['side'], trade['distPrice'],trade['remainamount'])
                                    if order:
                                        trade['coverorderlist'].append(order)
                        elif covertrade['status'] == 'closed':
                            if covertrade['amount'] < trade['remainamount'] :
                                # canceled = cancelOrder(biance, covertrade['id'], key)
                                # if canceled:
                                #     trade['coverorderlist'][-1] = canceled
                                amount = trade['remainamount']-covertrade['amount']
                                order = createSingelCoverOrder(key, trade['side'], trade['distPrice'],amount)
                                if order:
                                    trade['coverorderlist'].append(order)
        allTradeQueue[key] = trade


#取消序列中所有未成交的单据
def cancelAllOpenOrder(symbol):
    if allTradeQueue.get(symbol):
        trade = allTradeQueue[symbol]
        if trade.get('orderlist'):
            for order in trade['orderlist']:
                if order['status'] == 'open':
                    if abs(order['remaining'] - order['amount']) < VERYSMALLNUM:   #不存在部分成交的情况
                        cancelOrder(biance, order['id'], symbol)
                    else:
                        return False  #存在部分成交的情况
        if trade.get('coverorderlist'):
            for order in trade['coverorderlist']:
                if order['status'] == 'open':
                    if abs(order['remaining'] - order['amount']) < VERYSMALLNUM:   #不存在部分成交的情况
                        cancelOrder(biance, order['id'], symbol)
                    else:
                        return False  #存在部分成交的情况
    return True

def StopLossOrAddPositon():
    for key in allTradeQueue:
        trade = allTradeQueue[key]
        if not trade.get('orderlist'): #订单列表为空，不处理
            continue
        if abs(trade['remainamount']) < 0.0001:#剩余量为0，不处理
            continue
        if trade['status'] == 'created':
            continue
        currentprice = getAccuratePrice(biance, key, trade['side'])
        if trade['lefttick'] < 0 and currentprice is not None:
            result={}
            result['symbol'] = key
            result['side'] = 'buy' if trade['side']=='sell' else 'sell'
            result['trend'] = 'up' if result['side']=='buy' else 'down'
            result['amount'] = 0.2
            result['price'] = currentprice
            result['targetprice1'] = currentprice*1.02 if trade['side']=='sell' else currentprice*0.98
            result['targetprice2'] = currentprice*1.2 if trade['side']=='sell' else currentprice*0.85
            result['targetprice3'] = currentprice*1.2 if trade['side']=='sell' else currentprice*0.85
            result['targetprice4'] = currentprice*1.2 if trade['side']=='sell' else currentprice*0.85
            result['stopprice'] = trade['distPrice']
            result['priceH'] = trade['priceH']
            result['priceL'] = trade['priceL']
            result['type'] = 'op' if  trade['type']=='create' else 'end'
            result['lefttick'] = 12000
            sendMsg(3, str('!!!!reverse:')+str(key)+str(result))
            queue.put(result)


def isCreateby15minBoll(key,trend):
    result={}
    bollResult = getBollingResult(biance, key, period='15m')
    currentprice = bollResult['currentprice']
    if bollResult:
        #计算当前价与高低点的差距
        if trend == 'up':
            out = (bollResult['currentprice'] - bollResult['middle'])/bollResult['middle']
            offset = (currentprice-bollResult['upper'])/bollResult['upper']
        elif trend == 'down':
            out = (bollResult['middle'] - bollResult['currentprice'])/bollResult['middle']
            offset = (bollResult['lower']-currentprice)/bollResult['lower']
        else:
            return None
        if offset > OFFSET:
            result['symbol'] = key
            result['trend'] = trend
            result['side'] = getSidebyTrend(trend)
            #result['amount'] = out
            result['amount'] = 0.2
            result['price'] = bollResult['currentprice']
            result['targetprice1'] = upPrice(bollResult['upper']) if trend == 'up' else downPrice(bollResult['lower'])
            result['targetprice2'] = (bollResult['upper']+bollResult['middle'])/2 if trend == 'up' else (bollResult['lower']+bollResult['middle'])/2
            result['targetprice3'] = bollResult['middle']
            result['targetprice4'] = bollResult['lower'] if trend == 'up' else bollResult['upper']
            result['stopprice'] = bollResult['currentprice'] * (1+TOLERANCE*3) if trend == 'up' else bollResult['currentprice']*(1-TOLERANCE)
            result['priceH'] = max(bollResult['currentprice'], bollResult['middle'])
            result['priceL'] = min(bollResult['currentprice'], bollResult['middle'])
            result['type'] = 'create'
            result['lefttick']=5000
            debugstr = str("15mintrend：%s:%s--mouth:%0.4f-up:%0.8f--lower:%0.8f--off:%0.8f-- \n" % (key, trend, currentprice,bollResult['upper'],bollResult['lower'], offset))
            trendstr = ' 上▲' if trend == 'up' else ' 下■'
            debugstr1 = str(key[0:-5]+'突破15m,向'+trendstr)
            sendMsg(3,debugstr1)
            return result
        else:
            return None
    else:
        return None





def repeat1min():
    while True:
       # mylock.acquire()
        if len(allTradeQueue)>=MAXTRADENUM:
           #mylock.release()
            continue
        ohlc={}
        for key in tradepairs:
            try:
                ohlc[key] = biance.fetch_ohlcv(key,'1m',limit=60)
            except Exception as e:
                sendMsg(3,e)
                #mylock.release()
                time.sleep(60)
                continue
            try:
                if ohlc.get(key):
                    df = pd.DataFrame(ohlc[key],columns=['time','open','high','low','close','vol'],dtype='double')
                    currentprice = df.iat[-1, 4]
                    dfbolling = dataAnalyseboll(df)
                    if dfbolling is not None:
                        boll_up1min = dfbolling["BBANDS_upper"].iloc[-1]
                        boll_low1min = dfbolling["BBANDS_lower"].iloc[-1]
                        boll_mid1min = dfbolling["BBANDS_middle"].iloc[-1]
                        if (currentprice - boll_up1min)/boll_mid1min >0.001:
                            #debugstr = str("↑↑：%s--currentprice:%0.8f-bollingup:%0.8f \n" % (key, currentprice, boll_up1min))
                            #sendMsg(3,debugstr)
                            task = isCreateby15minBoll(key, 'up')
                            if task:
                                queue.put(task)
                        elif (currentprice - boll_low1min)/boll_mid1min <-0.001:
                            #debugstr = str("↓↓：%s--currentprice:%0.8f-boll_low:%0.8f \n" % (key, currentprice, boll_low1min))
                            #sendMsg(3,debugstr)
                            task = isCreateby15minBoll(key,'down')
                            if task:
                                queue.put(task)
            except Exception as e:
                #mylock.release()
                sendMsg(3,e)
                continue
       # if mylock.locked():
       #     mylock.release()
        time.sleep(5)

import asyncio

# async def getPriceLH(key,trend):
#     tick=0
#     sleeptime = 5
#     pricebook={}
#     pricebook['priceH']=0.0
#     pricebook['priceL']=1000000000.0
#     pricebook['price']=0.0
#     while True:
#         try:
#             orderbook = getOrderbook(biance, key)
#             if orderbook is not None:
#                 currentpriceH = orderbook["asks"][0][0]
#                 currentpriceL = orderbook["bids"][0][0]
#                 if trend == 'sell':
#                     pricebook['price'] = currentpriceH
#                     if currentpriceH > pricebook['priceH']:
#                         pricebook['priceH']= currentpriceH
#                         tick=0
#                     if currentpriceL < pricebook['priceL']:
#                         pricebook['priceL'] = currentpriceL
#                 elif trend == 'buy':
#                     pricebook['price'] = currentpriceL
#                     if currentpriceL <pricebook['priceL']:
#                         pricebook['priceL']=currentpriceL
#                         tick=0
#                     if currentpriceH >pricebook['priceH']:
#                         pricebook['priceH'] = currentpriceH
#             tick+=1
#             if tick * sleeptime > 120:
#                 sendMsg(3, str(key) + str(': perio max price:') + str(pricebook)+'tick: '+str(tick))
#                 return pricebook
#             await asyncio.sleep(sleeptime)
#                 continue
#         except Exception as e:
#             sendMsg(3, e)
#             await asyncio.sleep(60)
#             tick =0
#             continue

# async def getPeriodPrice(key,trend):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     task = loop.create_task(getPriceLH(key,trend))
#     loop.run_until_complete(task)
#     loop.close()
#     return task.result()

def updateTicks(alltrades): #获取所有交易对行情
    try:
        tickers = biance.fetch_tickers(symbols=alltrades)
    except Exception as e:
        sendMsg(3,e)
        return None
    for key in tickers:
        if key in records:
            singleRecord={}
            singleRecord['time']=tickers[key]['timestamp']
            singleRecord['price']=tickers[key]['last']
            if singleRecord['price'] is not None:
                if len(records[key]['data'])>CONST_LISTLEN:
                    del records[key]['data'][0]
                deltaRatio = 0.0
                if records[key]['data']:
                    lastRecord = records[key]['data'][-1]
                    deltaprice = singleRecord['price']-lastRecord['price']
                    midPrice = (lastRecord['price']+singleRecord['price'])/2
                    deltaRatio = deltaprice / midPrice
                singleRecord['delta']=deltaRatio
                records[key]['data'].append(singleRecord)


def analyseDecrease():
    for key in records:
        data = records[key]['data']
        period = Vividict()
        idx=0
        tmpc=1
        for i in range(len(data)):
            if data[i]['delta'] <-VERYSMALLNUM and not i==0:  #小于0且不是第一个
                if not period[idx]['starttime']:
                    period[idx]['starttime']=data[i-1]['time']
                    period[idx]['startprice'] = data[i - 1]['price']
                period[idx]['endtime']=data[i]['time']
                period[idx]['endprice'] = data[i]['price']
                if not period[idx]['sumdelta']:
                    period[idx]['sumdelta']=0.0
                period[idx]['sumdelta']+=data[i]['delta']
                tmpc+=1
                period[idx]['interval'] = tmpc
            else:
                idx+=1
                tmpc = 1
        if period:
            minidx = min(period,key=lambda x:period[x]['sumdelta'])
            averageDelta = period[minidx]['sumdelta'] /period[minidx]['interval']
            if averageDelta <-0.0005 and period[minidx]['sumdelta'] <-CONST_TRIGERRATIO:#
                #打印日志
                debugstr = str("快速下降" +str(key))
                sendMsg(3,debugstr)


def analyseIncrease():
    for key in records:
        data = records[key]['data']
        period = Vividict()
        idx=0
        tmpc=1
        for i in range(len(data)):
            if data[i]['delta'] >VERYSMALLNUM and not i==0:  #大于0且不是第一个
                if not period[idx]['starttime']:
                    period[idx]['starttime']=data[i-1]['time']
                    period[idx]['startprice'] = data[i - 1]['price']
                period[idx]['endtime']=data[i]['time']
                period[idx]['endprice'] = data[i]['price']
                if not period[idx]['sumdelta']:
                    period[idx]['sumdelta']=0.0
                period[idx]['sumdelta']+=data[i]['delta']
                tmpc+=1
                period[idx]['interval'] = tmpc
            else:
                idx+=1
                tmpc = 1
        if period:
            maxidx = max(period,key=lambda x:period[x]['sumdelta'])
            averageDelta = period[maxidx]['sumdelta'] /period[maxidx]['interval']
            if averageDelta >0.0005  and period[maxidx]['sumdelta'] > CONST_TRIGERRATIO:
                debugstr = str("快速上升" +str(key))
                sendMsg(3,debugstr)

def analyse():
    while True:
        updateTicks(tradepairs)
        analyseIncrease()
        analyseDecrease()
        time.sleep(8)



def main():
    #删除成交量太低的交易对
    removeUnstablePairs()
    threading.Thread(name='watchOHLC',target=repeat1min).start()
    threading.Thread(name='ddd',target=analyse).start()
    #threading.Thread(name='createorder', target=insertPriOrderlist).start()
    # threading.Thread(name='managerorder', target=dealallorders).start()

try:
     main()
except Exception as e:
    sendMsg(3,e)
    traceback.print_exc()