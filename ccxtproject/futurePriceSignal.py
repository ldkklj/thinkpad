#!/usr/bin/env python
# -*- coding: utf-8 -*

import ccxt
import traceback
import time
import logging
import log
from gloabalfunc import *
import pandas as pd
import time
import requests
import json
import decimal
from analyse import *

pd.set_option('display.precision', 10)
CONST_TRIGERRATIO=0.01
OFFSET=0.002
url = 'https://oapi.dingtalk.com/robot/send?access_token=f53ecde4568ac70ad6057e62c5bbe05295218280dc8dbc3cc20a555f9df936df'
headers = {
    "Content-Type": "application/json; charset=utf-8"
}
msglist={}

def cllectSignal():
    currenttime = time.time()
    listkeys=[]
    for key in msglist.keys():
        shottimes = 0
        str1 =''
        str2 = ''
        str3 =''
        str4 = ''
        str5 =''
        str6 = ''
        if abs(currenttime - msglist[key]['current']) < 60:
            shottimes += 1
            str1 = 'cr:'
        if abs(currenttime - msglist[key]['15m']) < 60:
            shottimes += 1
            str3 = '15m:'
        if abs(currenttime - msglist[key]['1m']) < 60:
            shottimes += 1
            str2 = '1m:'
        if abs(currenttime - msglist[key]['1h']) < 60:
            shottimes += 1
            str4 = '1h:'
        if abs(currenttime - msglist[key]['4h']) < 60:
            shottimes += 1
            str5 = '4h:'
        if abs(currenttime - msglist[key]['1d']) < 60:
            shottimes += 1
            str6 = '1d:'
        strtime = time.strftime("!%H:%M:%S", time.localtime())
        if (shottimes > 2):
            listkeys.append(key)
            msg1 = strtime + str(key) +':'+ str(shottimes)+str1+str2+str3+str4+str5+str6
            data = {
                "msgtype": "text",
                "text": {
                    "content": msg1
                },
            }

            # 发送请求
            try:
                resp = requests.post(url,
                                     data=json.dumps(data).encode('utf8'),
                                     headers=headers,
                                     )
            except:
                time.sleep(120)
                msglist.clear()
            print(msg1)

    for delkey in listkeys:
        del msglist[delkey]

def sendSignal(key,msg):
    currenttime= time.time()
    shottimes = 0
    if not msglist.get(key):
        msglist[key]={
            '15m':0,
            '1m':0,
            '1h':0,
            '4h':0,
            '1d':0,
            'current':0,
        }
    else:
        if msg == '15m':
            msglist[key]['15m']=currenttime
        elif msg == '1m':
            msglist[key]['1m']=currenttime
        elif msg == '1h':
            msglist[key]['1h']=currenttime
        elif msg == '4h':
            msglist[key]['4h']=currenttime
        elif msg == '1d':
            msglist[key]['1d']=currenttime
        elif msg == 'current':
            msglist[key]['current']=currenttime









CONST_LISTLEN  =30
VERYSMALLNUM=0.0000001


biance = ccxt.binance()
biance.apiKey='SmsHHG3GiRFuqjMOBS7OfKDMUxhPEH5xswyhAr1LSpswN9WYFZCC47KjAIPNhiiJ'
biance.secret='N9zFx7xBpSI7v9BJ7QIGXKBuzsvczqyZYGcuVf6fyX0E5GOyd5PKgjvcU1wn2340'
biance.options['defaultType']='future'
biance.load_markets()
tradepairs=biance.markets

del tradepairs['HOT/USDT']
del tradepairs['DENT/USDT']
del tradepairs['SPELL/USDT']
del tradepairs['LEVER/BUSD']
records = Vividict()
allTradeQueue = Vividict()

for key in tradepairs:
    records[key]['data'] = []
    market=biance.market(key)
    leverage = 20 #合约杠杆
    try:
        response = biance.fapiPrivate_post_leverage({'symbol': market['id'],'leverage': leverage,'recvWindow': 10000000})
    except Exception as e:
        print(1,e)

def updateTicks(alltrades): #获取所有交易对行情
    try:
        tickers = biance.fetch_tickers()
    except Exception as e:
        sendMsg(1,e)
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
                #打印日志
                ltime1 = time.localtime(period[minidx]['starttime']/1000)
                ltime2 = time.localtime(period[minidx]['endtime']/1000)
                strltime1 = time.strftime("%Y-%m-%d %H:%M:%S", ltime1)
                strltime2 = time.strftime("%Y-%m-%d %H:%M:%S", ltime2)
                debugstr = str("coin：%s--start:%s-end:%s-sumdelta:%0.8f-price1:%0.8f-price2:%0.8F \n" % (
                key, strltime1, strltime2,period[minidx]['sumdelta'],period[minidx]['startprice'],period[minidx]['endprice']))
                sendSignal(key,'current')

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
                #打印日志
                ltime1 = time.localtime(period[maxidx]['starttime']/1000)
                ltime2 = time.localtime(period[maxidx]['endtime']/1000)
                strltime1 = time.strftime("%Y-%m-%d %H:%M:%S", ltime1)
                strltime2 = time.strftime("%Y-%m-%d %H:%M:%S", ltime2)
                debugstr = str("coin：%s--start:%s-end:%s-sumdelta:%0.8f-price1:%0.8f-price2:%0.8F \n" % (
                key, strltime1, strltime2,period[maxidx]['sumdelta'],period[maxidx]['startprice'],period[maxidx]['endprice']))
                sendSignal(key,'current')


def getBollingResult(biance,key,period='15m'):
    result={}
    try:
        ohlc = biance.fetch_ohlcv(key, period, limit=120)
    except Exception as e:
        sendMsg(3,e)
        return None
    try:
        df = pd.DataFrame(ohlc, columns=['time', 'open', 'high', 'low', 'close', 'vol'],dtype='double')
        if df['close'].mean()<0.1:
            df['close']=df['close'].mul(1000)
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

def isCreateby15minBoll(key):
    result={}
    bollResult = getBollingResult(biance, key, period='15m')
    currentprice = bollResult['currentprice']
    if bollResult:
        #计算当前价与高低点的差距
        if (currentprice - bollResult['upper'])/currentprice>OFFSET or (bollResult['lower']-currentprice)/currentprice>OFFSET:
            sendSignal(key, '15m')
            isCreateby1hnBoll(key)
    else:
        return None

def isCreateby1hnBoll(key):
    result={}
    bollResult = getBollingResult(biance, key, period='1h')
    currentprice = bollResult['currentprice']
    if bollResult:
        #计算当前价与高低点的差距
        if (currentprice - bollResult['upper'])/currentprice>OFFSET or (bollResult['lower']-currentprice)/currentprice>OFFSET:
            sendSignal(key, '1h')
            isCreateby4hnBoll(key)
    else:
        return None

def isCreateby4hnBoll(key):
    result={}
    bollResult = getBollingResult(biance, key, period='4h')
    currentprice = bollResult['currentprice']
    if bollResult:
        #计算当前价与高低点的差距
        if (currentprice - bollResult['upper'])/currentprice>OFFSET or (bollResult['lower']-currentprice)/currentprice>OFFSET:
            sendSignal(key, '4h')
            isCreateby1dnBoll(key)
    else:
        return None

def isCreateby1dnBoll(key):
    result={}
    bollResult = getBollingResult(biance, key, period='1d')
    currentprice = bollResult['currentprice']
    if bollResult:
        #计算当前价与高低点的差距
        if (currentprice - bollResult['upper'])/currentprice>OFFSET or (bollResult['lower']-currentprice)/currentprice>OFFSET:
            sendSignal(key, '1d')
    else:
        return None

def repeat1min():
    # ohlc={}
    # for key in tradepairs:
    #     try:
    #         ohlc[key] = biance.fetch_ohlcv(key,'1m',limit=60)
    #     except Exception as e:
    #         sendMsg(3,e)
    #         time.sleep(60)
    #         continue
    #     try:
    #         if ohlc.get(key):
    #             df = pd.DataFrame(ohlc[key],columns=['time','open','high','low','close','vol'],dtype='str').round(10)
    #             # df['close'] = df['close'].astype('float64').round(8)
    #             df['close'] = df['close'].apply(lambda x: decimal.Decimal(x))
    #             df['close'] = df['close'].apply(pd.to_numeric, downcast='float')
    #
    #             currentprice = df.iat[-1, 4]
    #             dfbolling = dataAnalyseboll(df)
    #             if dfbolling is not None:
    #                 boll_up1min = dfbolling["BBANDS_upper"].iloc[-1]
    #                 boll_low1min = dfbolling["BBANDS_lower"].iloc[-1]
    #                 boll_mid1min = dfbolling["BBANDS_middle"].iloc[-1]
    #                 if (currentprice - boll_up1min)/boll_mid1min >OFFSET or (currentprice - boll_low1min)/boll_mid1min <-OFFSET:
    #                     isCreateby15minBoll(key)
    #                     sendSignal(key, '1m')
    #     except Exception as e:
    #         sendMsg(3,e)
    #         continue
    icount =0
    for key in tradepairs:
        try:
            icount +=1
            if icount%15==1:
                time.sleep(1)
            bollResult = getBollingResult(biance, key, period='1m')
            currentprice = bollResult['currentprice']
            if bollResult:
                #计算当前价与高低点的差距
                if (currentprice - bollResult['upper'])/currentprice>OFFSET or (bollResult['lower']-currentprice)/currentprice>OFFSET:
                    sendSignal(key, '1m')
                    isCreateby15minBoll(key)
            else:
                continue
        except Exception as e:
            sendMsg(3,e)
            continue

def main():
    #删除成交量太低的交易对
    tick=0
    while True:
        if tick % 2 == 0:
            updateTicks(tradepairs)
            analyseDecrease(tick)
            analyseIncrease(tick)
            repeat1min()
            cllectSignal()
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
