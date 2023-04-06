# -*- coding: utf-8 -*-
#每个币种能只能开一次单，错失大量价差机会
#稳定可运行2天

import asyncio
import ccxt
import ccxt.async_support as ccxta  # noqa: E402
import time
import os
import sys

from gloabalfunc import *
from  ichat import *
import json
import numpy as np
from collections import OrderedDict
from Config import *



from urllib import request
import  requests
proxies = {
    'https': 'http://127.0.0.1:7890',
    'http': 'http://127.0.0.1:7890'
}

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

my_wallet ={}
openorderoffset= 0.005
closeoffset =0.002
orderid=0


exchanges = {}
exchanges['binance']=binancea
exchanges['kucoinfutures'] = kucoina
exchanges['okex']=okexa
exchanges['bybit'] = bybita
# for key in exchanges.keys():
#     exchange = exchanges[key]
#     exchange.aiohttp_proxy = proxies['http']
#     exchange.aiohttpProxy = proxies['http']



# pos = huobiN.fetch_balance()
# huobiN.options['createMarketBuyOrderRequiresPrice'] = False
# mm = huobiN.load_markets()
#huobiN.create_market_order('BTC/USDT:USDT', 'buy' ,10, None,params = {'offset': 'open', 'lever_rate': 1,'marginType': 'cross'})
# huobiN.create_market_order('BTC/USDT:USDT','buy',1,23340,params = {'offset': 'open', 'lever_rate': 1,'marginType': 'cross'})
# mm = kucoinN.load_markets()
#mexcN.create_market_order('BTC/USDT','buy',1,23340,params = {'offset': 'open', 'lever_rate': 1,'marginType': 'cross'})
# pos = huobiN.fetch_positions(symbols=['BTC/USDT:USDT'])

orderclient=0
flag=False
my_pos={}
coinManage={}
coinData = {}
coinAnalyseRet = {}
suggestCoin = OrderedDict()
coindictnew={}
futurePos={'jjfiejffda':None}
orderList={}

dd=\
    {'buyorder': {'side': 'buy', 'exchange':1, 'intprice': 1, 'realprice':0, 'intAmt':1
                                  ,'realAmt':0,'status':'open','id':1,'symbol':1},
     'sellorder': {'side': 'sell','exchange':2,'intprice':2,'realprice':0,'intAmt':3
                                  ,'realAmt':0,'status':'open','id':3,'symbol':3}
    }


async def async_client(exchange_id,exchange,coin):
    orderbook = None
    try:
        start = time.time()
        orderbook = await exchange.fetch_order_book(coin[exchange_id]['symbol'])
        end = time.time()
        # print(exchange_id, time.strftime("!%H:%M:%S", time.localtime()),end-start)
        if end -start >0.3:
            return { 'exchange': exchange.id, 'orderbook': None }
    except Exception as e:
        print(type(e).__name__, str(e))
    # await exchange.close()
    return { 'exchange': exchange.id, 'orderbook': orderbook }


async def  quickOpenOrder(exchange,symbol,priceSpot,amount,size,side):
    global orderList
    global orderid
    try:
        orderid+=1
        strorderid= 'order'+str(orderid)
        order = await asycreteOrder(exchange,symbol,'limit',side,round(amount/size),priceSpot,None)
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
        if exchange.id == 'bybit':
            customTimestamp = await exchange.fetch_time()
            exchange.options['recvWindow'] = 100000000
        balance = await exchange.fetch_balance()
        if balance:
            if balance.get('USDT'):
                usdtleft= balance['USDT']['free']
                ret['USDT']=usdtleft
            # positons = balance['info']['positions']
            # for item in positons:
            #     if float(item['positionAmt'])>0.01:
            #         coinname = item['symbol']
            #         coinname.rstrip('USDT')
            #         ret['pos'].append({coinname:int(item['positionAmt'])})
            return ret
        else:
            return None
    except Exception as e:
        print('\n\nError in LeftMoney() ', e)
        await asyncio.sleep(1)
        return None


async def multi_orderbooks(coindict,tick,exchanges):
    await asyncio.sleep(6)
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




async def loadAllFutureDataOnTime():
    global exchanges
    temp = {}
    coindict = {}
    global coindictnew

    for key in exchanges.keys():
        exchange = exchanges[key]
        try:
            market = await exchange.load_markets()
            for key in market.keys():
                pair = market[key]
                if  pair['type'] == 'swap' or pair['type'] == 'future' :
                    if pair['quote'] == 'USDT' or pair['quote'] == 'usdt':
                        if not pair['expiry']:
                        # if not pair['info']['contractType'] or not pair['info']['contractType'] == 'PERPETUAL':
                        #     continue
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
    with open('coindictnewfuture.json', 'w') as f:
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


async def refreshWallet():
    total =0
    for exchangeName in exchanges.keys():
        leftmoney = await LeftMoney(exchanges[exchangeName])
        if leftmoney:
            my_wallet[exchangeName] = leftmoney
            total+=leftmoney['USDT']
    print('--------------Mywallet Usdt---------'+str(total))

def getbookfromOrder(orderbook):
    if not orderbook['orderbook']:
        return None
    return {
        'bid': orderbook['orderbook']['bids'][0][0],
        'ask': orderbook['orderbook']['asks'][0][0],
        'bidAmt': orderbook['orderbook']['bids'][0][1],
        'askAmt': orderbook['orderbook']['asks'][0][1],
        'exchange':orderbook['exchange']
    }

async def openorderPair(interval,book1,book2,exName1,exName2,coin,value,coinprice,amt=0,type='profit'):
    print('open order @@@@@@@@@@'+type+''+exName1+''+exName2+coin)
    global my_walletq
    global futurePos
    if type == 'profit':
        amount = round(40/coinprice)
        # if my_wallet[exName2]['USDT'] > 30 and my_wallet[exName1]['USDT'] > 30 and not futurePos.get(coin):
        if my_wallet.get(exName1) and my_wallet.get(exName2) and my_wallet[exName2]['USDT'] > 30 and my_wallet[exName1]['USDT'] > 30 and not futurePos.get(coin):
            input_coroutines=[]
            input_coroutines.append(quickOpenOrder(exchanges[exName1], value[exName1]['symbol'], book1['ask']*1.02, amount,value[exName1]['contractSize'],'buy'))
            input_coroutines.append(quickOpenOrder(exchanges[exName2], value[exName2]['symbol'], book2['bid']*0.98, amount,value[exName2]['contractSize'],'sell'))
            pairOrders = await asyncio.gather(*input_coroutines, return_exceptions=True)
            if pairOrders[0]:
                my_wallet[exName1]['USDT']-=amount * coinprice
                futurePos[coin] = {}
                futurePos[coin]['buyorder']={'side': 'buy', 'exchange': exName1, 'intprice': book1['ask'], 'realprice': 0,'intAmt': amount,
                                             'realAmt': 0, 'status': 'open', 'id': pairOrders[0]['id'], 'symbol': value[exName1]['symbol']}
            else:
                futurePos[coin]={}
                futurePos[coin]['buyorder'] = {'side': 'buy', 'exchange': exName1, 'intprice': book1['ask'],
                                               'realprice': 0, 'intAmt': amount,
                                               'realAmt': 0, 'status': 'open', 'id': 0,
                                               'symbol': value[exName1]['symbol']}
            if pairOrders[1]:
                my_wallet[exName2]['USDT'] -= amount* coinprice
                if not futurePos.get(coin):
                    futurePos[coin] = {}
                futurePos[coin]['sellorder']= {'side': 'sell','exchange':exName2,'intprice': book2['bid'],'realprice':0,'intAmt':amount
                                  ,'realAmt':0,'status':'open','id':pairOrders[1]['id'],'symbol':value[exName2]['symbol']}
            else:
                futurePos[coin]['sellorder'] = {'side': 'sell', 'exchange': exName2, 'intprice': book2['bid'],
                                                'realprice': 0, 'intAmt': amount
                    , 'realAmt': 0, 'status': 'open', 'id': 0, 'symbol': value[exName2]['symbol']}
            if pairOrders[0] and pairOrders[1]:
                str1 = str(coin) + str('@') + str(exName1) +format(book1['ask'],'.4f') +'@' +\
                       str(exName2) + format(book2['bid'],'.4f')+'@'+\
                       format(interval,'.4f') + ':' + str('amt:') + str(amount) + '@'+\
                       str('profit')+ format(interval*amount*coinprice,'.2f')
            else:
                str1='failed to open pair order! '
            # await refreshWallet()
            sendMsg(3, str1)
            return 'success'
        else:
            print('not enough coin')
            return None
    else:
        input_coroutines=[]
        input_coroutines.append(quickOpenOrder(exchanges[exName1], value[exName1]['symbol'], book1['ask']*1.01, amt,value[exName1]['contractSize'],'buy'))
        input_coroutines.append(quickOpenOrder(exchanges[exName2], value[exName2]['symbol'], book2['bid']*0.99, amt,value[exName2]['contractSize'],'sell'))
        pairOrders = await asyncio.gather(*input_coroutines, return_exceptions=True)
        if pairOrders[0] and pairOrders[1]:
            profit = pairOrders[1]['price']
            del futurePos[coin]
            sendMsg(3, 'succeed close pair order!')
            return 'success'
        else:
            print('error close pair order')
            return None
async def updateFuturePos():
    for key in futurePos.keys():
        fupos =futurePos[key]
        if not fupos:
            continue
        if not fupos['buyorder']['status']=='closed':
            order = await asyfetchOrder(exchanges[fupos['buyorder']['exchange']], fupos['buyorder']['id'],  fupos['buyorder']['symbol'])
            if order and order['status']=='closed':
                fupos['buyorder']['status']='closed'
                fupos['buyorder']['realprice'] = order['cost']
                fupos['buyorder']['realAmt'] = order['amount']
        if not fupos['sellorder']['status']=='closed':
            order = await asyfetchOrder(exchanges[fupos['sellorder']['exchange']], fupos['sellorder']['id'], fupos['sellorder']['symbol'])
            if order and order['status']=='closed':
                fupos['sellorder']['status']='closed'
                fupos['sellorder']['realprice'] = order['cost']
                fupos['sellorder']['realAmt'] = order['amount']
        if fupos['buyorder']['status']=='closed' and fupos['sellorder']['status']=='closed':
                profitgap = (fupos['sellorder']['realprice']-fupos['buyorder']['realprice'])*2/(fupos['sellorder']['realprice']+fupos['buyorder']['realprice'])
                fupos['profitNeed2']=0.006-profitgap
def exchg(a,b):
    a,b=b,a
    return (a,b)

async def judgeAndCloseBalance(coin,interal2,book1,book2,ex1Name,ex2Name,value,coinprice):
    global futurePos
    fupos = futurePos[coin]
    if not fupos.get('profitNeed2'):
        return
    # if fupos['buyorder']['exchange'] == ex2Name and fupos['sellorder']['exchange'] == ex1Name:
    #     exchg(interal1, interal2)
    #     exchg(book1, book2)
    #     exchg(ex1Name, ex2Name)
    #fullfill profit condition ,create double order
    if interal2>fupos.get('profitNeed2') or interal2>-0.001:
        print('near close :'+str(book1)+str(book2))
        await openorderPair(interal2, book2, book1, ex2Name,ex1Name, coin, value['value'], coinprice,fupos['sellorder']['realAmt']*value['value'][ex2Name]['contractSize'],'balance')


def avg(nums):
    nums = list(nums)
    return round(sum(nums) / len(nums), 10)

async def managerOrder():
    tick =0
    global exchanges
    global coindictnew
    global coinManage
    global futurePos
    tick=0
    while True:
        tick+=1
        strtime = time.strftime("!%H:%M:%S", time.localtime())
        print(strtime)
        # await asyncio.sleep(4)
        if tick%10==1:
            await refreshWallet()
        await updateFuturePos()
        for key in coindictnew.keys():
            await asyncio.sleep(0.5)
            value = coindictnew[key]
            input_coroutines = [async_client(exchangeName, exchanges[exchangeName], value['value']) for exchangeName in value['value'].keys()]
            orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
            book= {}
            bad = False
            for i in range(0, len(orderbooks)):
                tempbook = getbookfromOrder(orderbooks[i])
                if not tempbook:
                    bad =True
                    continue
                else:
                    book[tempbook['exchange']]=tempbook
            if bad :
                continue
            coinprice = (avg(bkorder['bid'] for bkorder in book.values())+avg(bkorder['ask'] for bkorder in book.values()))/2
            if coinprice <0.00000001:
                dde=12
            if futurePos.get(key) and book.get(futurePos[key]['buyorder']['exchange'])  and book.get(futurePos[key]['sellorder']['exchange']):
                book1= book[futurePos[key]['buyorder']['exchange']]
                book2= book[futurePos[key]['sellorder']['exchange']]
                interal2 = (book1['bid'] - book2['ask']) / coinprice
                await judgeAndCloseBalance(key,
                                           interal2,
                                           book1,
                                           book2,
                                           futurePos[key]['buyorder']['exchange'],
                                           futurePos[key]['sellorder']['exchange'],
                                           value,coinprice)
            minAskExchange = min(book.keys(), key=(lambda k: book[k]['ask']))
            maxBidExchange = max(book.keys(), key=(lambda k: book[k]['bid']))
            if not minAskExchange == maxBidExchange:
                interval =  (book[maxBidExchange]['bid']-book[minAskExchange]['ask'])/coinprice
                # print(interval)
                if interval>0.008:
                    str1 = str(key) + str(":itvl1:") + format(interval, '.4f') + str(book[minAskExchange]) + str(book[maxBidExchange])
                    print(str1)
                    ret =await openorderPair(interval, book[minAskExchange], book[maxBidExchange], book[minAskExchange]['exchange'], book[maxBidExchange]['exchange'], key, value['value'],coinprice,'profit')
                    str1 = str(key) + str(":itvl:") + format(interval, '.4f') + str(book[minAskExchange]) + str(book[maxBidExchange])
                    print(str1)
                    if ret:
                        await asyncio.sleep(4)
            # for i in range(0, len(orderbooks)):
            #     for j in range(i, len(orderbooks)):
            #         if i == j:
            #             continue
            #         else:
            #             if not orderbooks[i] or not orderbooks[j] or not orderbooks[i].get('orderbook') or not orderbooks[j].get('orderbook'):
            #                 continue
            #             exchange1 = orderbooks[i]['exchange']
            #             exchange2 = orderbooks[j]['exchange']
            #             if not my_wallet.get(exchange1):
            #                 continue
            #             if not my_wallet.get(exchange2):
            #                 continue
            #             book1 = getbookfromOrder(orderbooks[i])
            #             book2 = getbookfromOrder(orderbooks[j])
            #             coinprice = (book1['bid'] + book1['ask'] + book2['bid'] + book2['ask']) / 4
            #             coinManage[key]['price']=coinprice
            #             interal1= (book2['bid']-book1['ask'])/coinprice
            #             interal2= (book1['bid']-book2['ask'])/coinprice
            #             if futurePos.get(key.coin) and futurePos[key.coin]['buyorder']['exchange']==exchange1 and futurePos[key.coin]['sellorder']['exchange']==exchange2:
            #                 await judgeAndCloseBalance(key.coin, interal1, interal2, book1, book2, exchange1, exchange2, value,coinprice)
            #             if interal1 >0.004:
            #                 coinManage[key]['active'] += 4
            #                 await openorderPair(interal1, book1, book2, key.exchange1, key.exchange2, key.coin, value,coinprice)
            #                 str1 = str(key.coin) + str(":itvl1:") + format(interal1, '.4f') + str('itvl2') + \
            #                        format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
            #                 print(str1)
            #             if interal2 >0.004:
            #                 coinManage[key]['active'] += 4
            #                 await openorderPair(interal2, book2, book1, key.exchange2, key.exchange1, key.coin, value,coinprice)
            #                 str1 = str(key.coin) + str(":itvl1:") + format(interal1, '.4f') + str('itvl2') + \
            #                        format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
            #                 print(str1)




async def run():
    tasklist = []
    global coindictnew
    global orderList
    for key in exchanges.keys():
        orderList[key] = []
    if False:
        await loadAllFutureDataOnTime()

    with open('coindictnewfuture.json', 'r') as f:
        coindictnew = json.load(f)  # 解码JSON数据
    del coindictnew['CVC']
    del coindictnew['TLM']
    del coindictnew['SC']
    # for key in coindictnew:
    #     leverage = 10  # 合约杠杆
    #     for ex,vlv in coindictnew[key]['value'].items():
    #         try:
    #             if  vlv.get('binance'):
    #                 response = exchanges[ex].fapiPrivate_post_leverage({'symbol': vlv['id'], 'leverage': leverage, 'recvWindow': 10000000})
    #         except Exception as e:
    #             print(e)

    # await binancea.load_markets()
    # tradepairs=binancea.markets
    #
    # for key,value in tradepairs.items():
    #     leverage = 10  # 合约杠杆
    #     try:
    #         await binancea.fapiPrivate_post_leverage(
    #             {'symbol': value['id'], 'leverage': leverage, 'recvWindow': 10000000})
    #     except Exception as e:
    #         print(key+str(e))
    # ret =await analyseCoin()
    await managerOrder()
    # th1 = asyncio.create_task(analyseCoin())
    # tasklist.append(th1)
    # th2 = asyncio.create_task(managerOrder())
    # tasklist.append(th2)
    # result = await asyncio.gather(*tasklist)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

if __name__ == '__main__':
    main()
