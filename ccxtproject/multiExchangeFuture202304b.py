# -*- coding: utf-8 -*-
#配合202304使用
#现货
#用于对所有交易所的交易对进行扫描，每1个小时周期更新coinAnalyseRet202304b.json 文件


import asyncio
import ccxt
import ccxt.pro
import ccxt.async_support as ccxta  # noqa: E402
import time
import os
import sys
import traceback
import copy

from gloabalfunc import *
from  ichat import *
import json
import numpy as np
from collections import OrderedDict
from Config import *



proxies = {
    'https': 'http://127.0.0.1:7890',
    'http': 'http://127.0.0.1:7890'
}

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')


orderid=0

exchanges = {}
exchanges['bitget'] = bitgeta
exchanges['okex']=okexa
exchanges['bybit'] = bybita
exchanges['mexc'] = mexca
exchanges['binance'] = binancea


my_pos={}
coinManage={}
coinData = {}
coinAnalyseRet = {}
suggestCoin = OrderedDict()
coindictnew={}
futurePos={}
orderList={}
bookSreenWall={}



async def async_client(exchange_id,exchange,coin):
    orderbook = None
    try:
        start = time.time()
        orderbook = await exchange.fetch_order_book(coin[exchange_id]['symbol'])
        end = time.time()
        if end -start >0.3:
            return { 'exchange': exchange.id, 'orderbook': None }
    except Exception as e:
        print(type(e).__name__, str(e))
    return { 'exchange': exchange.id, 'orderbook': orderbook }




async def multi_orderbooks(coindict,tick,exchanges):
    await asyncio.sleep(6)
    global coinAnalyseRet
    global coinData
    coinRecord={}
    if tick % 60== 1:
        for data in coinData.values():
            for key in data.keys():
                list1 = data[key]
                if len(list1) > 0:
                    ret = {}
                    ret['var'] = np.var(list1)
                    ret['std'] = np.std(list1)
                    ret['mean'] = np.mean(list1)
                    ret['uplimit'] = ret['mean']+ret['std']
                    ret['lowerlimit']=ret['mean']-ret['std']
                    coinAnalyseRet[key.coin+'@'+key.exchange1+'@'+key.exchange2] = ret
                    coinRecord[key.coin+'@'+key.exchange1+'@'+key.exchange2]=list1
                data[key]=[]
        if len(coinAnalyseRet):
            result = sorted(coinAnalyseRet.items(), key=lambda x: x[1]['std'], reverse=True)
            if len(result) > 20:
                for i in range(0, len(result)):
                    val = result[i][1]
                    keyStr = result[i][0]
                    strr = keyStr + '-var:' + format(val['var'],'.4f') + \
                           str('-std:')+format(val['std'],'.4f') + str('-mean:')+format(val['mean'],'.4f')
                    print(strr)
                    if abs(val['std']) > 0.0015 and abs(val['mean'])<0.03:
                        suggestCoin[keyStr] = val
                    if len(suggestCoin)>0:
                        with open('suggestCoin.json', 'w') as f:
                            json.dump(suggestCoin, f)  # 编码JSON数据
                with open('coinAnalyseRet.json', 'w') as f:
                    json.dump(result, f)  # 编码JSON数据
                with open('coinRecord.json', 'w') as f:
                    json.dump(coinRecord, f)  # 编码JSON数据

    tick2=0
    for key in coindict.keys():
        tick2+=1
        if tick2%20==0:
            await asyncio.sleep(1)
        value = coindict[key]['spot']
        input_coroutines = [async_client(exchangeName, exchanges[exchangeName], value) for exchangeName in value.keys()]
        orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
        for i in range(0, len(orderbooks)):
            for j in range(i, len(orderbooks)):
                if i == j:
                    continue
                else:
                    if orderbooks[i] and orderbooks[j] and  orderbooks[i]['orderbook'] and orderbooks[j]['orderbook'] \
                            and len(orderbooks[i]['orderbook']['bids']) > 0 and len(orderbooks[j]['orderbook']['bids']) > 0:
                        global coinprice
                        coinprice = (orderbooks[i]['orderbook']['bids'][0][0] + orderbooks[i]['orderbook']['asks'][0][ 0]) / 2
                        interal1 = (orderbooks[i]['orderbook']['bids'][0][0] - orderbooks[j]['orderbook']['asks'][0][0])/orderbooks[i]['orderbook']['bids'][0][0]
                        interal2 = (orderbooks[j]['orderbook']['bids'][0][0] - orderbooks[i]['orderbook']['asks'][0][0])/orderbooks[j]['orderbook']['bids'][0][0]
                        coinpair = SingleCoinPair(key, orderbooks[i]['exchange'], orderbooks[j]['exchange'])
                        realinv = None
                        if interal1 > 0:
                            realinv = interal1
                        if interal2 > 0:
                            realinv = -interal2
                        if realinv :
                            if coinData[key].get(coinpair):
                                coinData[key][coinpair].append(realinv)
                            else:
                                datalist = []
                                datalist.append(realinv)
                                coinData[key][coinpair] = datalist




async def loadAllSpotDataOnTime():
    global exchanges
    temp = {}
    coindict = {}
    global coindictnew
    market = {}

    for exName in exchanges.keys():
        exchange = exchanges[exName]
        try:
            market[exName] = await exchange.load_markets()
            with open(exName + '.json', 'w') as f:
                json.dump(market[exName], f)  # 编码JSON数据
            for key in market[exName].keys():
                pair = market[exName][key]
                if pair['type'] == 'spot' or pair['type'] == 'SPOT':
                    if pair['quote'] == 'USDT' or pair['quote'] == 'usdt':
                        if not pair['base'] in temp:
                            coin = {}
                            coin[exchange.id] = pair
                            temp[pair['base']] = coin
                        else:
                            temp[pair['base']][exchange.id] = pair
        except Exception as e:
            print(e)
            continue
        for key in temp.keys():
            coindict[key] = {'spot': temp[key],'diff':{}}
    dellist=[]
    for key in coindict.keys():
        if len(coindict[key]['spot'])<2:
            dellist.append(key)
    for item in dellist:
        del coindict[item]
    with open('multiExchangeSpot.json', 'w') as f:
        json.dump(coindict, f)  # 编码JSON数据


async def analyseCoin():
    global exchanges
    global coinData


    for key in coindictnew.keys():
        coinData[key] = {}
    tick = 0
    while True:
        tick += 1
        a = await multi_orderbooks(coindictnew, tick, exchanges)



async def run():
    global coindictnew
    global orderList
    global bookSreenWall
    for key in exchanges.keys():
        orderList[key] = []
    if False:
        await loadAllSpotDataOnTime()

    with open('multiExchangeSpot.json', 'r') as f:
        coindictnew = json.load(f)  # 解码JSON数据

    await analyseCoin()



def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        traceback.print_exc()