#!/usr/bin/env python
# -*- coding: utf-8 -*
#import ccxtpro
import ccxt
import traceback
#import queue
#import pandas as pd
import time
import logging
import log
from gloabalfunc import *
# import configparser as config
# cfg = config.ConfigParser()
# cfg.read('config.txt')




CONST_LISTLEN  =30
CONST_TRIGERRATIO=0.01

VERYSMALLNUM=0.0000001
MAXTRADENUM=7       #同时处理的交易对上限
TIMEOUTTICK=30      #超时撤销订单的超时时间
TOLERANCE = 0.01   #加单或者止损点比例
ratioAddList=[1,1,1,3,6,9,9,10,10]
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
#biance.apiKey='vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y'
#biance.secret='0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK'
biance.apiKey='kFL6HJH7bv1kwSElGxzkI6BkcC0ZiUpM3qe2lWEBZk9Ba2QyAkpbB9vDoCb6KKSk'
biance.secret='5eW823yAcwGh8sPGewolb9HGVRCL8hWFnBqNSB9S1FV6xVhBXWeMJiEeQF64bhyh'
biance.options['defaultType']='future'
biance.load_markets()
tradepairs=biance.markets
#allTradeQueue = {}  #定义全局变量用来存放策略结果

# order1 = biance.create_order('BTC/USDT','limit','buy',0.001,'6666',{'recvWindow': 10000000})
# order2 = biance.create_market_order('FIL/USDT','market','sell',0.1,{'recvWindow': 10000000})
# order3 = biance.fetch_order(order2['id'],'FIL/USDT',{'recvWindow': 10000000})
# ret =biance.cancel_order(order2['id'],'FIL/USDT',{'recvWindow': 10000000})
# strtime=time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
# logging.basicConfig(level=sendMsg,#控制台打印的日志级别
#                     filename=strtime+str(".log"),
#                     filemode='a',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
#                     #a是追加模式，默认如果不写的话，就是追加模式
#                     format=
#                     '%(asctime)s -: %(message)s'
#                     #日志格式
#                     )
#symbol='BTCUSDT'
#ohllc =biance.fetch_ohlcv(symbol, '1d')

log.createlogfile()

#定义嵌套字典
# class Vividict(dict):
#     def __missing__(self, key):
#         value = self[key] = type(self)()
#         return value

records = Vividict()
allTradeQueue = Vividict()

#records.fromkeys(tradepairs)
for key in tradepairs:
    records[key]['data'] = []
    market=biance.market(key)
    leverage = 20 #合约杠杆
    try:
        response = biance.fapiPrivate_post_leverage({'symbol': market['id'],'leverage': leverage,'recvWindow': 10000000})
    except Exception as e:
        print(e)


def updateTicks(alltrades): #获取所有交易对行情
    try:
        tickers = biance.fetch_tickers(symbols=alltrades)
    except Exception as e:
        sendMsg( e)
        return None
    for key in tickers:
        if key in records:
            singleRecord={}
            lastRecord={}
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

def insertPriOrderlist(direct,key,price1,price2,tick):
    if key in allTradeQueue.keys():#有可能需要加仓和更新目标价格
        return False
    else:#没有目标添加目标
        if len(allTradeQueue) >= MAXTRADENUM:
            return False
        preOrder = {}
        if direct == 'buy':
            ticker = getticker(biance, key)
            if ticker:
                if ticker['last'] < price2:
                    return False
            preOrder['priceH'] = max(price1, price2)
            preOrder['priceL'] = min(price1, price2)
            preOrder['price'] = price2
            preOrder['distPrice'] = downPrice(abs(price1 - price2) * 0.618 + price2)
            preOrder['stopPrice'] = min(price1, price2) * (1 - TOLERANCE)
        elif direct == 'sell':
            ticker = getticker(biance, key)
            if ticker:
                if ticker['last'] > price2:
                    return False
            preOrder['priceH'] = max(price1, price2)
            preOrder['priceL'] = min(price1, price2)
            preOrder['price'] = price2
            preOrder['distPrice'] = upPrice(price2 - abs(price1 - price2) * 0.618)
            preOrder['stopPrice'] = max(price1, price2) * (1 + TOLERANCE)
        else:
            return False
        preOrder['side'] = direct
        preOrder['symbol'] = key
        preOrder['status'] = 'unused'
        preOrder['starttick'] = tick
        preOrder['starttime'] = time.time()
        sendMsg('insert init order')
        sendMsg(preOrder)
        allTradeQueue[key]=preOrder
        return True



def analyse(): #进行分析，给出买卖提示
    for key in records:
        tempkeymin = min(records[key]['data'], key=lambda x: x['price'])
        minIndex = records[key]['data'].index(tempkeymin)
        tempkeymax = max(records[key]['data'], key=lambda x: x['price'])
        maxIndex = records[key]['data'].index(tempkeymax)
        midPrice = (tempkeymax['price'] + tempkeymin['price'])/2
        deltaPrice = tempkeymax['price'] - tempkeymin['price']
        deltaRatio = deltaPrice /midPrice
        deltaMSecs = tempkeymin['time'] - tempkeymax['time']
        deltaSecs = deltaMSecs/1000
        # 条件一：跌幅超过1% 条件2 下降趋势 条件3 最低值保持15秒以上
        # 即使取得最小值，仍需至少等待15秒并判断这15秒的值是否有上升趋势
        if deltaRatio>0.02 and deltaSecs > 0 and minIndex<CONST_LISTLEN-3:
            ltime = time.localtime(tempkeymin['time'])
            strltime = time.strftime("%Y-%m-%d %H:%M:%S", ltime)
            debugstr = str("%s----%s---%0.2f---%0.4f \n" % (key, strltime, tempkeymax['price'], deltaRatio))
            sendMsg(debugstr)

            dPrice1 = records[key]['data'][-1]['price']-tempkeymin['price']-midPrice*0.0005
            dPrice2 = records[key]['data'][-2]['price']-tempkeymin['price']-midPrice*0.0005
            dPrice3 = records[key]['data'][-3]['price']-tempkeymin['price']-midPrice*0.0005
            if dPrice1>0 and dPrice2 >0 and dPrice3 >0 :
                preOrder={}
                preOrder['side']='buy'
                preOrder['price']=records[key]['data'][-1]['price']*1.0006
                preOrder['symbol']=key
                preOrder['status']='unused'
                debugstr = str("%s-%s-p:%0.8f-p1:%0.8f-p2:%0.8f-p3:%0.8f \n" % (
                key, preOrder['side'], preOrder['price'], records[key]['data'][-1]['price'],
                records[key]['data'][-2]['price'], records[key]['data'][-3]['price']))
                sendMsg(debugstr)
                if not key in allTradeQueue.keys():
                    allTradeQueue[key]=preOrder



def analyseDecrease(tick):
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
                #增加到预买单中
                #sendMsg(period[-10:-1])
                if not insertPriOrderlist('buy', key, period[minidx]['startprice'],period[minidx]['endprice'],tick):
                    continue
                #获取资产
                balance = getAccount(biance)
                if balance:
                    #下初始单
                    createInitOrder(balance, tick, key)
                #打印日志
                ltime1 = time.localtime(period[minidx]['starttime']/1000)
                ltime2 = time.localtime(period[minidx]['endtime']/1000)
                strltime1 = time.strftime("%Y-%m-%d %H:%M:%S", ltime1)
                strltime2 = time.strftime("%Y-%m-%d %H:%M:%S", ltime2)
                debugstr = str("coin：%s--start:%s-end:%s-sumdelta:%0.8f-price1:%0.8f-price2:%0.8F \n" % (
                key, strltime1, strltime2,period[minidx]['sumdelta'],period[minidx]['startprice'],period[minidx]['endprice']))
                sendMsg(debugstr)


def analyseIncrease(tick):
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
            if averageDelta >0.0005  and period[maxidx]['sumdelta'] > CONST_TRIGERRATIO: #
                #增加预下单
                if not insertPriOrderlist('sell', key, period[maxidx]['startprice'],period[maxidx]['endprice'],tick):
                    continue
                #获取资产
                balance = getAccount(biance)
                if balance:
                    #下初始单
                    createInitOrder(balance, tick, key)
                #打印日志
                ltime1 = time.localtime(period[maxidx]['starttime']/1000)
                ltime2 = time.localtime(period[maxidx]['endtime']/1000)
                strltime1 = time.strftime("%Y-%m-%d %H:%M:%S", ltime1)
                strltime2 = time.strftime("%Y-%m-%d %H:%M:%S", ltime2)
                debugstr = str("coin：%s--start:%s-end:%s-sumdelta:%0.8f-price1:%0.8f-price2:%0.8F \n" % (
                key, strltime1, strltime2,period[maxidx]['sumdelta'],period[maxidx]['startprice'],period[maxidx]['endprice']))
                sendMsg(debugstr)

def removeUnstablePairs():
    # 获取最近3天的成交量，移除交易量太小的交易对
  #  tradepairs.pop('DEFIUSDT')
    volumelist = {}
    badpairs = []
    for trade in tradepairs:
        ohlcv=biance.fetch_ohlcv(trade, '1d')
        if len(ohlcv) <4:
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



def createInitOrder(balance,tick,key):
    #剩下的USDT
    leftmoney = balance['USDT']['free']
    if allTradeQueue[key]['status']== 'unused':
        preOrder = allTradeQueue[key]
        amount = leftmoney*0.006*20/records[key]['data'][-1]['price']
        order = createOrder(biance,preOrder['symbol'], 'limit', preOrder['side'], amount, preOrder['price'])
        if order:
            records[key]['data'].clear()
            if not preOrder.get('orderlist'):
                preOrder['orderlist']=[]
                preOrder['orderlist'].append(order)
                preOrder['dealordercnt']=0
                preOrder['remainamount']=0.0
                preOrder['remainusdt'] = 0.0
                preOrder['remainprice']=preOrder['price']
                preOrder['status']= 'created'
                allTradeQueue[key]=preOrder

def getPosition(balance):
    positions=balance['info']['positions']
    for pos in positions:
        fakesymbol=pos['symbol']
        symbol=biance.markets_by_id[fakesymbol]['symbol']
        if pos['positionInitialMargin']=='0':
            continue
        else:
            if symbol in allTradeQueue:
                position={}
                position['symbol']=symbol
                position['costusdt']=float(pos['initialMargin']) #消耗的usdt
                position['iniPrice']=float(pos['entryPrice'])  #初始价格
                position['profit']=float(pos['unrealizedProfit'])#已实现盈利
                allTradeQueue[symbol]['postion']=position

def managerOrderstatus(tick):
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
                    order0 = fetchOrder(biance,trade['orderlist'][i]['id'],key)
                    if order0:
                        trade['orderlist'][i] = order0
                        if order0['status'] == 'closed':
                            trade['dealordercnt'] +=1
                            trade['remainamount'] += order0['amount']
                            trade['remainusdt']+=order0['amount']*order0['price']
                if  trade['dealordercnt'] == len(trade['orderlist']):#所有的订单都已成交
                    trade['status']='alldeal'
                elif  trade['dealordercnt'] <len(trade['orderlist']):
                    if trade['dealordercnt'] > 0:
                        trade['status']='partdeal'

        #查看平单状态
        if trade.get('coverorderlist'):
            for j in range(len(trade['coverorderlist'])):
                coverorder0=fetchOrder(biance,trade['coverorderlist'][j]['id'],key)
                if coverorder0:
                    trade['coverorderlist'][j] = coverorder0
                    #平单已生效且与订单成交总量一致
                    if coverorder0['status']=='closed':
                        trade['remainamount'] -= coverorder0['amount']
                        trade['remainusdt'] -= coverorder0['amount'] * coverorder0['price']
        if trade['remainamount']<-VERYSMALLNUM:
            sendMsg("出现错误，平单数量超过开单数量！")
            sendMsg(trade)
        elif abs(trade['remainamount']) < VERYSMALLNUM and trade.get('coverorderlist'):
            if trade['status'] == 'alldeal':
                endlist[key]=0
                sendMsg("订单成功结束")
                sendMsg(trade)
                continue
        #计算当前持仓价格
        if abs(trade['remainamount']>VERYSMALLNUM):
            trade['remainprice']=trade['remainusdt']/trade['remainamount']

        if trade['status']=='unused' or trade['status']=='created':
            if tick - trade['starttick']>TIMEOUTTICK:
                endlist[key]=0
                if trade.get('orderlist'):
                    sendMsg('timeout,cancel order')
                    cancelOrder(biance, trade['orderlist'][0]['id'], key)
                continue
        if trade.get('stoplossoerder'):
            slorder = fetchOrder(biance, trade['stoplossoerder']['id'], key)
            if slorder:
                if slorder['status']=='closed':
                    sendMsg('success failed')
                    endlist[key]=0
        allTradeQueue[key] =trade
    for key in endlist.keys():
        allTradeQueue.pop(key)
        sendMsg('pop key:')
        sendMsg(key)

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
        if  trade['status'] != 'alldeal':
            continue
        if not trade.get('orderlist'):
            continue
        # 重新计算目标价
        isdistpricechanged = False
        newDistprice = recaculateDistPrice(biance, key, trade['priceL'], trade['priceH'], trade['side'])
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
                if trade['remainamount'] > VERYSMALLNUM:
                    # for covertrade in trade['coverorderlist']:
                    #     if covertrade['status'] == 'open' and abs(covertrade['remaining']-covertrade['amount'])<VERYSMALLNUM:
                    covertrade = trade['coverorderlist'][-1]
                    if covertrade['status'] == 'open' and abs(covertrade['remaining'] - covertrade['amount']) < VERYSMALLNUM:
                        if covertrade['amount']<trade['remainamount'] or isdistpricechanged:
                            canceled = cancelOrder(biance, covertrade['id'], key)
                            if canceled:
                                trade['coverorderlist'][-1] = canceled
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
                if order['status']=='open':
                    if abs(order['remaining']- order['amount'])<VERYSMALLNUM:   #不存在部分成交的情况
                        cancelOrder(biance, order['id'], symbol)
                    else:
                        return False  #存在部分成交的情况
        if trade.get('coverorderlist'):
            for order in trade['coverorderlist']:
                if order['status']=='open':
                    if abs(order['remaining']- order['amount'])<VERYSMALLNUM:   #不存在部分成交的情况
                        cancelOrder(biance, order['id'], symbol)
                    else:
                        return False  #存在部分成交的情况
    return True

def StopLossOrAddPositon():
    TOLERANCE=0.01
    faillist= {}
    for key in allTradeQueue:
        trade = allTradeQueue[key]
        if  trade['status'] == 'unused': #还没下单，不处理
            continue
        if not trade.get('orderlist'): #订单列表为空，不处理
            continue
        if abs(trade['remainamount'])<0.0001:#剩余量为0，不处理
            continue
        ticker = getticker(biance, key)
        if ticker:
            currentprice=ticker['last']
            multi=len(trade['orderlist'])
            if multi>0  :
                if trade['side']=='buy':
                    if currentprice <trade['stopPrice']:
                        order = createOrder(biance, key, 'limit', trade['side'], trade['orderlist'][0]['amount']*ratioAddList[multi], upPrice(currentprice))
                        if order:
                            trade['orderlist'].append(order)
                            trade['stopPrice']= currentprice *(1-TOLERANCE*1.6*multi)
                            sendMsg('加仓')
                            logging.warning(trade)
                elif trade['side']=='sell':
                    if currentprice>trade['stopPrice']:
                        order = createOrder(biance, key, 'limit', trade['side'], trade['orderlist'][0]['amount']*ratioAddList[multi], downPrice(currentprice))
                        if order:
                            trade['orderlist'].append(order)
                            trade['stopPrice'] = currentprice *(1+TOLERANCE*1.6*multi)
                            logging.warning('加仓')
                            logging.warning(trade)
            now = time.time()
            if now - trade['starttime'] > 40000:
                cancelAllOpenOrder(key)
                if trade['side']=='buy':
                        order = createOrder(biance, key, 'limit','sell', trade['remainamount'],downPrice(currentprice))
                        if order:
                            trade['stoplossoerder']=order
                            trade['status']='failed'
                        logging.warning('failed')
                        logging.warning(trade)
                        continue
                elif trade['side']=='sell':
                        order = createOrder(biance, key, 'limit', 'buy', trade['remainamount'],upPrice(currentprice))
                        if order:
                            trade['stoplossoerder']=order
                            trade['status'] = 'failed'
                        logging.warning('failed')
                        logging.warning(trade)
                        continue
            # elif multi>=5:
            #     if trade['side']=='buy':
            #         if currentprice <trade['stopPrice']*(1-TOLERANCE):
            #             cancelAllOpenOrder(key)
            #             order = createOrder(biance, key, 'limit','sell', trade['remainamount'],downPrice(currentprice))
            #             if order:
            #                 trade['stoplossoerder']=order
            #                 trade['status']='failed'
            #             logging.warning('failed')
            #             logging.warning(trade)
            #             continue
            #     elif trade['side']=='sell':
            #         if currentprice > trade['stopPrice']*(1+TOLERANCE):
            #             cancelAllOpenOrder(key)
            #             order = createOrder(biance, key, 'limit', 'buy', trade['remainamount'],upPrice(currentprice))
            #             if order:
            #                 trade['stoplossoerder']=order
            #                 trade['status'] = 'failed'
            #             logging.warning('failed')
            #             logging.warning(trade)
            #             continue

def overtimeadjustTarget(tick):
    for key in allTradeQueue.keys():
        trade = allTradeQueue[key]
        deltatick=tick-trade['starttick']
        if trade.get('coverorderlist'):
            covertrade = trade['coverorderlist'][-1]
            if deltatick >=2000 and deltatick <6000:
                if trade['side'] == 'buy':
                    if  trade['distPrice'] > trade['remainprice']:
                        trade['distPrice']=downPrice(trade['distPrice'])
                        canceled = cancelOrder(biance, covertrade['id'], key)
                        if canceled:
                            debugstr = str("adjust %s dist price to :%0.8f  \n" % (key, trade['distPrice']))
                            logging.warning(debugstr)
                            trade['coverorderlist'][-1] = canceled
                            order = createSingelCoverOrder(key, trade['side'], trade['distPrice'],trade['remainamount'])
                            if order:
                                trade['coverorderlist'].append(order)
                elif trade['side'] == 'sell':
                        trade['distPrice'] = upPrice(trade['distPrice'])
                        if trade['distPrice'] < trade['remainprice']:
                            trade['distPrice'] = upPrice(trade['distPrice'])
                            canceled = cancelOrder(biance, covertrade['id'], key)
                            if canceled:
                                debugstr = str("adjust %s dist price to :%0.8f  \n" % (key, trade['distPrice']))
                                logging.warning(debugstr)
                                trade['coverorderlist'][-1] = canceled
                                order = createSingelCoverOrder(key, trade['side'], trade['distPrice'],trade['remainamount'])
                                if order:
                                    trade['coverorderlist'].append(order)
            elif deltatick >=6000:
                if trade['side'] == 'buy':
                        trade['distPrice']=downPrice(trade['distPrice'])
                        debugstr = str("adjust %s dist price to :%0.8f  \n" % (key, trade['distPrice']))
                        logging.warning(debugstr)
                        canceled = cancelOrder(biance, covertrade['id'], key)
                        if canceled:
                            trade['coverorderlist'][-1] = canceled
                            order = createSingelCoverOrder(key, trade['side'], trade['distPrice'],trade['remainamount'])
                            if order:
                                trade['coverorderlist'].append(order)
                elif trade['side'] == 'sell':
                        trade['distPrice']=upPrice(trade['distPrice'])
                        debugstr = str("adjust %s dist price to :%0.8f  \n" % (key, trade['distPrice']))
                        logging.warning(debugstr)
                        canceled = cancelOrder(biance, covertrade['id'], key)
                        if canceled:
                            trade['coverorderlist'][-1] = canceled
                            order = createSingelCoverOrder(key, trade['side'], trade['distPrice'], trade['remainamount'])
                            if order:
                                trade['coverorderlist'].append(order)



def main():
    #删除成交量太低的交易对
    removeUnstablePairs()
    tick=0
    while True:
        if tick % 2 == 0:
            updateTicks(tradepairs)
            analyseDecrease(tick)
            analyseIncrease(tick)
            managerOrderstatus(tick)
            createCoverOrder()
            StopLossOrAddPositon()
        #if tick % 10000 == 0:
           # overtimeadjustTarget(tick)
        if tick % 120 == 0:
            logging.warning(allTradeQueue.keys())
        time.sleep(1)
        tick +=1
try:
     main()
except Exception as e:
    print(e)
    traceback.print_exc()
