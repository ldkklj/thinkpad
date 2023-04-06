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
from ichat import *
import json
from collections import OrderedDict

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

openorderoffset = 0.005
closeoffset = 0.002

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

gateio = ccxta.gateio(
    {'apiKey':'61ab9289c4bf2cf5f373f5daba6a3460',
     'secret':'f1f4b2d60964e79d11c6855768716304d785b8d270d76ac0771a4de4a3292975',
     'password': 'windows-999'
})
gateio.options['defaultType']='future'

gateN = ccxt.gateio(
    {'apiKey':'61ab9289c4bf2cf5f373f5daba6a3460',
     'secret':'f1f4b2d60964e79d11c6855768716304d785b8d270d76ac0771a4de4a3292975',
        'password': 'windows-999'
})
gateN.options['defaultType']='future'

exchanges = {}
# exchanges.append(huobi)
# exchanges['mexc'] = mexc
# exchanges['binance'] = binance
# exchanges['okex'] = okex
exchanges['kucoin'] = kucoin
exchanges['ftx'] = ftx
exchanges['gateio']=gateio

coinprice = 0.00006
flag = False
my_pos = {}

coinData = {}
coinAnalyseRet = {}
suggestCoin = OrderedDict()

proxies = {
    'https': 'http://127.0.0.1:10807/pac?auth=7cjiXKnWYJi1WOfYRn6U',
    'http': 'https://127.0.0.1:10807/pac?auth=7cjiXKnWYJi1WOfYRn6U'
}

async def async_client(exchange_id, exchange, coin):
    orderbook = None
    # exchange = getattr(ccxta, exchange_id)()
    try:
        start = time.time()
        orderbook = await exchange.fetch_order_book(coin[exchange_id]['symbol'])
        end = time.time()
        if end-start>2:
            print(exchange_id, time.strftime("!%H:%M:%S", time.localtime()),end-start)
            return None
    except Exception as e:
        print(type(e).__name__, str(e))
        await exchange.close()
    return {'exchange': exchange.id, 'orderbook': orderbook}



async def multi_orderbooks(coindict, tick, exchanges):
    time.sleep(3)
    #########先看看每个钱包有多少钱多少币
    print("--------------------------------------------------")
    # 计算数据统计结果
    global my_pos
    global coinAnalyseRet
    global coinData
    coinRecord={}
    if tick % 11 == 1:
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
        if len(coinAnalyseRet):
            result = sorted(coinAnalyseRet.items(), key=lambda x: x[1]['std'], reverse=True)
            if len(result) > 10:
                for i in range(0, len(result)):
                    val = result[i][1]
                    keyStr = result[i][0]
                    strr = keyStr + '-var:' + format(val['var'],'.4f') + \
                           str('-std:')+format(val['std'],'.4f') + str('-mean:')+format(val['mean'],'.4f')
                    print(strr)
                    if abs(val['std']) > 0.0035 and abs(val['mean']) < 2*val['std']:
                        suggestCoin[keyStr] = val
                with open('suggestCoin.json', 'w') as f:
                    json.dump(suggestCoin, f)  # 编码JSON数据
                with open('coinAnalyseRet.json', 'w') as f:
                    json.dump(result, f)  # 编码JSON数据
                with open('coinRecord.json', 'w') as f:
                    json.dump(coinRecord, f)  # 编码JSON数据

    for key in coindict.keys():
        value = coindict[key]['value']
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
                        if realinv:
                            if coinData[key].get(coinpair):
                                coinData[key][coinpair].append(realinv)
                            else:
                                datalist = []
                                datalist.append(realinv)
                                coinData[key][coinpair] = datalist

                        if interal1 > openorderoffset:
                            str1 = str(key) + str("itvl1:") + format(interal1, '.4f') + str('itvl2') + \
                                   format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(
                                orderbooks[j]['exchange'])
                            sendMsg(3, str1)

async def loadAllMarketDataOnTime():
    global exchanges
    temp = {}
    coindict = {}
    coindictnew = {}

    for key in exchanges.keys():
        exchange = exchanges[key]
        # exchange.proxies =proxies
        try:
            market = await exchange.load_markets()
            for key in market.keys():
                pair = market[key]
                if pair['quoteId'] == 'USDT' and pair['future'] == True:
                    if not temp.get(pair['base']):
                        coin = {}
                        coin[exchange.id] = pair
                        temp[pair['base']] = coin
                    else:
                        temp[pair['base']][exchange.id] = pair
        except Exception as e:
            print(e)
            continue
        for key in temp.keys():
            if len(temp[key]) > 1:
                coindict[key] = {'tradeAmt': 0, 'value': temp[key]}

    volumelist = {}
    for key in coindict.keys():
        coinExcgValue = coindict[key]['value']
        tradeAmt1d = 0
        for exchangeName in coinExcgValue.keys():
            if exchangeName == 'kucoin':
                continue
            try:
                ohlcv = await exchanges[exchangeName].fetch_ohlcv(coinExcgValue[exchangeName]['symbol'], '1d', None, 1)
                if len(ohlcv):
                    tradeAmt1d += ohlcv[-1][5] * ohlcv[-1][4]
            except Exception as e:
                print(type(e).__name__, str(e))
                continue
        coindict[key]['tradeAmt'] = tradeAmt1d
        volumelist[key] = tradeAmt1d
    volumelist = sorted(volumelist.items(), key=lambda x: x[1], reverse=True)
    for i in range(len(volumelist))[::-1]:
        if '3S' in volumelist[i][0] or '3L' in volumelist[i][0]:
            del volumelist[i]
    global coinData
    for each in volumelist[:250]:
        coindictnew[each[0]] = coindict[each[0]]
        coinData[each[0]] = {}

    with open('coindictnew.json', 'w') as f:
        json.dump(coindictnew, f)  # 编码JSON数据


async def analyseCoin():
    global exchanges
    global coinData

    if True:
        await loadAllMarketDataOnTime()

    with open('coindictnew.json', 'r') as f:
        coindictnew = json.load(f)  # 解码JSON数据
    for key in coindictnew.keys():
        coinData[key] = {}
    tick = 0
    while True:
        tick += 1
        a = await multi_orderbooks(coindictnew, tick, exchanges)

async def run():
    tasklist = []
    th1 = asyncio.create_task(analyseCoin())
    tasklist.append(th1)
    result = await asyncio.gather(*tasklist)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


if __name__ == '__main__':
    main()