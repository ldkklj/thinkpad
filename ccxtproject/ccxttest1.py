#!/usr/bin/env python
# -*- coding: utf-8 -*
#import ccxtpro
import ccxt
import queue
import pandas as pd
import time
import logging

CONST_INTERVEL =4
CONST_LISTLEN  =600/CONST_INTERVEL

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
biance.apiKey='vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y'
biance.secret='0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK'
biance.options['defaultType']='future'
biance.load_markets()
tradepairs=biance.markets
preTradeQueue = {}  #定义全局变量用来存放策略结果
OrderList ={}  #定义全局变量存储所有订单

strtime=time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
logging.basicConfig(level=sendMsg,#控制台打印的日志级别
                    filename=strtime+str(".log"),
                    filemode='a',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    #a是追加模式，默认如果不写的话，就是追加模式
                    format=
                    '%(asctime)s -: %(message)s'
                    #日志格式
                    )
#定义嵌套字典
class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value
records = Vividict()

records.fromkeys(tradepairs)
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
        print('get tickers time out:', e)
        return
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
                    deltaRatio = round(deltaprice / midPrice,4)
                singleRecord['delta']=deltaRatio
                records[key]['data'].append(singleRecord)

def cleardata():
    if 'DEFI/USDT' in records.keys():
        records.pop('DEFI/USDT')


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
                if not key in preTradeQueue.keys():
                    preTradeQueue[key]=preOrder



def analyse1():
    for key in records:
        data = records[key]['data']
        period = Vividict()
        idx=0
        tmpc=1
        for i in range(len(data)):
            if data[i]['delta'] <0.00000001 and not i==0:  #小于0且不是第一个
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
            maxidx = min(period,key=lambda x:period[x]['sumdelta'])
            averageDelta = period[maxidx]['sumdelta'] /period[maxidx]['interval']
            if averageDelta <-0.001 and period[maxidx]['sumdelta'] <-0.01:
                ltime1 = time.localtime(period[maxidx]['starttime']/1000)
                ltime2 = time.localtime(period[maxidx]['endtime']/1000)
                strltime1 = time.strftime("%Y-%m-%d %H:%M:%S", ltime1)
                strltime2 = time.strftime("%Y-%m-%d %H:%M:%S", ltime2)
                debugstr = str("coin：%s--start:%s-end:%s-sumdelta:%0.8f-price1:%0.8f-price2:%0.8F \n" % (
                key, strltime1, strltime2,period[maxidx]['sumdelta'],period[maxidx]['startprice'],period[maxidx]['endprice']))
                sendMsg(debugstr)

        # tempkeymin = min(records[key]['data'], key=lambda x: x['price'])
        # minIndex = records[key]['data'].index(tempkeymin)
        # tempkeymax = max(records[key]['data'], key=lambda x: x['price'])
        # maxIndex = records[key]['data'].index(tempkeymax)
        # midPrice = (tempkeymax['price'] + tempkeymin['price'])/2
        # deltaPrice = tempkeymax['price'] - tempkeymin['price']
        # deltaRatio = deltaPrice /midPrice
        # deltaMSecs = tempkeymin['time'] - tempkeymax['time']
        # deltaSecs = deltaMSecs/1000
        # # 条件一：跌幅超过1% 条件2 下降趋势 条件3 最低值保持15秒以上
        # # 即使取得最小值，仍需至少等待15秒并判断这15秒的值是否有上升趋势
        # if deltaRatio>0.02 and deltaSecs > 0 and minIndex<CONST_LISTLEN-3:
        #     ltime = time.localtime(tempkeymin['time'])
        #     strltime = time.strftime("%Y-%m-%d %H:%M:%S", ltime)
        #     debugstr = str("%s----%s---%0.2f---%0.4f \n" % (key, strltime, tempkeymax['price'], deltaRatio))
        #     sendMsg(debugstr)
        #
        #     dPrice1 = records[key]['data'][-1]['price']-tempkeymin['price']-midPrice*0.0005
        #     dPrice2 = records[key]['data'][-2]['price']-tempkeymin['price']-midPrice*0.0005
        #     dPrice3 = records[key]['data'][-3]['price']-tempkeymin['price']-midPrice*0.0005
        #     if dPrice1>0 and dPrice2 >0 and dPrice3 >0 :
        #         preOrder={}
        #         preOrder['side']='buy'
        #         preOrder['price']=records[key]['data'][-1]['price']*1.0006
        #         preOrder['symbol']=key
        #         preOrder['status']='unused'
        #         debugstr = str("%s-%s-p:%0.8f-p1:%0.8f-p2:%0.8f-p3:%0.8f \n" % (
        #         key, preOrder['side'], preOrder['price'], records[key]['data'][-1]['price'],
        #         records[key]['data'][-2]['price'], records[key]['data'][-3]['price']))
        #         sendMsg(debugstr)
        #         if not key in preTradeQueue.keys():
        #             preTradeQueue[key]=preOrder



def createOrder():
    for key in preTradeQueue:
        if preTradeQueue[key]['status']=='unused':
            preOrder = preTradeQueue[key]
            # try:
            #     order = biance.create_order(preOrder['symbol'],'limit',preOrder['side'],2,preOrder['price'],'recvWindow': 10000000)
            # except Exception as e:
            #     sendMsg(e)
            # else:
            #     preTradeQueue[key]['status'] == 'used'
            #     OrderList.append(order)
            #     sendMsg(order)


def main():
    while True:
        updateTicks(tradepairs)
        cleardata()
        analyse1()
       #createOrder()
        time.sleep(CONST_INTERVEL)


try:
    main()
except Exception as e:
    print(e)