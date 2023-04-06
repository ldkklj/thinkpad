# -*- coding: utf-8 -*-
#尝试币和合约对冲操作
#合约只做空来吃资金费率
#1.买卖币，如果一边有U，一边有币，则买卖币
#2.买币，如果合约价格大于现货，则买入现货，卖出合约

#持币后，交易所之间进行币币的买卖对冲套利
#如果资金费率为负数，此时有大量人做空，此时币本身存在较大的下行风险，例如ftt，
#但是也存在较大的币币套利的可能，如果8小时单位周期内币币套利仍存在较大利润，可持续保持空单；否则此时套利空间不大可以考虑换仓
#初始开单时机：循环读取各币种现货和合约差价，如果超过一定阈值，就买入现货并做空合约
#退出开单时机：如果单位周期内某币币持续资金费率为负，且币币套利利润少于资金费率扣减，则减仓以

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
# exchanges['kucoinfutures'] = kucoina
# exchanges['kucoin'] = kucoin
exchanges['bitget']=bitgeta
exchanges['okex']=okexa
exchanges['bybit'] = bybita

# for key in exchanges.keys():
#     exchange = exchanges[key]
#     exchange.aiohttp_proxy = proxies['http']
#     exchange.aiohttpProxy = proxies['http']

# fundingrates = await binancea.fetchFundingRates()


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
futurePos={}
orderList={}
bookSreenWall={}

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
        value = coindict[key]['future']
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
    tempspot = {}
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
                            str = pair['base'].replace('1000', '')
                            str = str.replace('2', '')
                            str = str.replace('0', '')
                            if not temp.get(str):
                                coin = {}
                                coin[exchange.id] = pair
                                temp[str] = coin
                            else:
                                temp[str][exchange.id] = pair
                elif  pair['type'] == 'spot':
                    if pair['quote'] == 'USDT' or pair['quote'] == 'usdt':
                        if not tempspot.get(pair['base']):
                            coin = {}
                            coin[exchange.id] = pair
                            tempspot[pair['base']] = coin
                        else:
                            tempspot[pair['base']][exchange.id] = pair
        except Exception as e:
            print(e)
            continue
        for key in temp.keys():
            if len(temp[key]) > 0:
                coindict[key] = {'tradeAmt': 0, 'future': temp[key]}
                if   tempspot.get(key):
                    coindict[key]['spot']=tempspot[key]
    dellist=[]
    for key in coindict.keys():
        if len(coindict[key])==2:
            dellist.append(key)
    for item in dellist:
        del coindict[item]
    with open('multiExchangeFuture202302.json', 'w') as f:
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
    books={}
    books['future']={}
    books['spot'] = {}
    if not orderbook:
        return None
    else:
        now = time.time()
        for ex,value in orderbook['future'].items():
            if value and value[3] and abs(now-value[3]/1000.0)<1:
                books['future'][ex]={}
                books['future'][ex]['bid']=value[2][0]
                books['future'][ex]['ask']=value[1][0]
        for ex,value in orderbook['spot'].items():
            if value and value[3] and abs(now-value[3]/1000.0)<1:
                books['spot'][ex]={}
                books['spot'][ex]['bid']=value[2][0]
                books['spot'][ex]['ask']=value[1][0]
        return books

async def openorderPair(interval,book1,book2,exName1,exName2,coin,value,coinprice,amt=0,type='profit',idx=0):
    print('open order @@@@@@@@@@'+type+''+exName1+''+exName2+coin)
    global my_walletq
    global futurePos
    if not  futurePos.get(coin):
       futurePos[coin]=[]
    if type == 'profit':
        amount = round(20 / coinprice)
        pair = \
            {'buyorder': {'side': 'buy', 'exchange': exName1, 'intprice': book1['ask'], 'realprice': 0, 'intAmt': amount
                , 'realAmt': 0, 'status': 'init', 'id': 0, 'symbol': value[exName1]['symbol']},
             'sellorder': {'side': 'sell', 'exchange': exName2, 'intprice': book2['bid'], 'realprice': 0, 'intAmt': amount
                 , 'realAmt': 0, 'status': 'init', 'id': 0, 'symbol': value[exName2]['symbol']}
             }

        # if my_wallet[exName2]['USDT'] > 30 and my_wallet[exName1]['USDT'] > 30 and not futurePos.get(coin):
        if my_wallet.get(exName1) and my_wallet.get(exName2) and my_wallet[exName2]['USDT'] > 30 and my_wallet[exName1]['USDT'] > 30 :
            input_coroutines=[]
            input_coroutines.append(quickOpenOrder(exchanges[exName1], value[exName1]['symbol'], book1['ask']*1.02, amount,value[exName1]['contractSize'],'buy'))
            input_coroutines.append(quickOpenOrder(exchanges[exName2], value[exName2]['symbol'], book2['bid']*0.98, amount,value[exName2]['contractSize'],'sell'))
            pairOrders = await asyncio.gather(*input_coroutines, return_exceptions=True)
            if pairOrders[0]:
                my_wallet[exName1]['USDT']-= amount * coinprice
                pair['buyorder']['status'] = 'open'
                pair['buyorder']['id'] = pairOrders[0]['id']
            if pairOrders[1]:
                my_wallet[exName2]['USDT'] -= amount* coinprice
                pair['sellorder']['status'] = 'open'
                pair['sellorder']['id'] = pairOrders[1]['id']
            if pairOrders[0] and pairOrders[1]:
                str1 = str(coin) + str(pair)+ str('profit')+ format(interval*amount*coinprice,'.2f')
                futurePos[coin].append(pair)
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
            del futurePos[coin][idx]
            sendMsg(3, 'succeed close pair order!')
            return 'success'
        else:
            print('error close pair order')
            return None

async def updateFuturePos():
    for key in futurePos.keys():
        pairlist =futurePos[key]
        if len(pairlist) == 0:
            continue
        for fupos in pairlist:
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


def avg(nums):
    nums = list(nums)
    return round(sum(nums) / len(nums), 10)



async def getExchangeFundFee(exchange):
    global coindictnew
    if exchange=='binance':
        try:
            response  =await exchanges[exchange].fetchFundingRates()
            for key in coindictnew.keys():
                value = coindictnew[key]['future']
                for resKey,item in response.items():
                    if value.get(exchange) and value[exchange]['id']==item['info']['symbol']:
                        funding_rate = response[resKey]["info"]["lastFundingRate"]
                        if funding_rate:
                            value[exchange]['fundingrate'] = float(funding_rate)
        except Exception as e:
            print('\n\nError in getExchangeFundFee() ', e)
            await asyncio.sleep(1)
            return None
    elif exchange!='kucoin':
        try:
            for key in coindictnew.keys():
                value = coindictnew[key]['future']
                if value.get(exchange):
                    response = await exchanges[exchange].fetchFundingRate(value[exchange]['symbol'])
                    if response and response['fundingRate']:
                        value[exchange]['fundingrate'] = float(response['fundingRate'])
        except Exception as e:
            print('\n\nError in getExchangeFundFee() ', e)
            await asyncio.sleep(1)
            return None


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
        await asyncio.sleep(1)
        if tick%20==1:
            await refreshWallet()
        for key in bookSreenWall.keys():
            book=getbookfromOrder(bookSreenWall[key])
            if book['spot'] and book['future'] and len(book['spot'])>0  and len(book['future'])>0:
                coinprice = (avg(bkorder['bid'] for bkorder in book['spot'].values()) + avg(bkorder['ask'] for bkorder in book['spot'].values())) / 2
                #检查是否存在买币条件
                minAskSpotExchange = min(book['spot'].keys(), key=(lambda k: book['spot'][k]['ask']))
                maxBidFutureExchange = max(book['future'].keys(), key=(lambda k: book['future'][k]['bid']))
                interval = (book['future'][maxBidFutureExchange]['bid'] - book['spot'][minAskSpotExchange]['ask']) / coinprice
                if interval >0.004:
                    str1 = str('buychance')+str(key) + str(":itvl:") + format(interval, '.4f') + str(book['spot'][minAskSpotExchange]) + str(
                        book['future'][maxBidFutureExchange])
                    sendMsg(3, str1)
                if len(book['spot'])>1:
                    maxBidSpotExchange = max(book['spot'].keys(), key=(lambda k: book['spot'][k]['bid']))
                    interval2 = (book['spot'][maxBidSpotExchange]['bid'] - book['spot'][minAskSpotExchange]['ask']) / coinprice
                    if  interval2>0.006:
                        str1 = str('exchance')+str(key) + str(":itvl:") + format(interval2, '.4f') + str(book['spot'][minAskSpotExchange]) + str(
                            book['future'][maxBidFutureExchange])
                        sendMsg(3, str1)

        # await updateFuturePos()
        # for key in coindictnew.keys():
        #     await asyncio.sleep(0.5)
        #     value = coindictnew[key]
        #     input_coroutines = [async_client(exchangeName, exchanges[exchangeName], value['value']) for exchangeName in value['value'].keys()]
        #     orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
        #     start = time.time()
        #     book= {}
        #     bad = False
        #     for i in range(0, len(orderbooks)):
        #         tempbook = getbookfromOrder(orderbooks[i])
        #         if not tempbook:
        #             bad =True
        #             continue
        #         else:
        #             book[tempbook['exchange']]=tempbook
        #     if bad :
        #         continue
        #     coinprice = (avg(bkorder['bid'] for bkorder in book.values())+avg(bkorder['ask'] for bkorder in book.values()))/2
        #     if coinprice <0.00000001:
        #         dde=12
        #     if futurePos.get(key):
        #         await judgeAndCloseBalance(key,book,value,coinprice)
        #     minAskExchange = min(book.keys(), key=(lambda k: book[k]['ask']))
        #     maxBidExchange = max(book.keys(), key=(lambda k: book[k]['bid']))
        #     if not minAskExchange == maxBidExchange:
        #         interval =  (book[maxBidExchange]['bid']-book[minAskExchange]['ask'])/coinprice
        #         # print(interval)
        #         if interval>0.008:
        #             str1 = str(key) + str(":itvl1:") + format(interval, '.4f') + str(book[minAskExchange]) + str(book[maxBidExchange])
        #             print(str1)
        #             end = time.time()
        #             print(time.strftime("!%H:%M:%S", time.localtime()),end-start)
        #             ret =await openorderPair(interval, book[minAskExchange], book[maxBidExchange], book[minAskExchange]['exchange'], book[maxBidExchange]['exchange'], key, value['value'],coinprice,'profit')
        #             str1 = str(key) + str(":itvl:") + format(interval, '.4f') + str(book[minAskExchange]) + str(book[maxBidExchange])
        #             print(str1)
        #             if ret:
        #                 await asyncio.sleep(4)


orderbooks = {}
async def symbol_loop(exchange, symbol):
    # while True:
    #     try:
    #         str1=''
    #         if symbol['type']=='future':
    #             str1 ='value'
    #         elif symbol['type']=='spot':
    #             str1='spot'
    #         orderbook = await exchange.watch_order_book(coindictnew[symbol['key']][str1][exchange.id]['symbol'])
    #         bookSreenWall[symbol['key']][str1][exchange.id]= {1:orderbook['asks'][0],2:orderbook['bids'][0],3:ccxt.pro.Exchange.iso8601(orderbook['timestamp'])}
    #         print(bookSreenWall['AVAX'])
    #         print("---------------------------------------------------------")
    #
    #     except Exception as e:
    #         print(str(e))
    #         break  # you can break just this one loop if it fails
    global bookSreenWall
    while True:
        try:
            orderbook = await exchange.watch_order_book(symbol['symbol'])
            bookSreenWall[symbol['key']][symbol['type']][exchange.id]= {1:orderbook['asks'][0],2:orderbook['bids'][0],3:orderbook['timestamp']}
            # if symbol['key']=='AGLD':
            #     print(bookSreenWall['AGLD'])
            #     print("---------------------------------------------------------")
        except Exception as e:
            print(str(e))
            break  # you can break just this one loop if it fails

async def exchange_loop(exchange_id, symbols):
    exchange = getattr(ccxt.pro, exchange_id)()
    # exchange.aiohttp_proxy = proxies['http']
    # exchange.aiohttpProxy = proxies['http']
    loops = [symbol_loop(exchange, symbol) for symbol in symbols]
    await asyncio.gather(*loops)
    # await exchange.close()


async def getWSSOrderbooks():
    # temp = {}
    # for exName in exchanges.keys():
    #     temp[exName] = []
    # for key in coindictnew:
    #     value = coindictnew[key]
    #     for exchangename in value['value']:
    #         temp[exchangename].append({'key':key,'type':'future'})
    #     for exchangename in value['spot']:
    #         if not exchangename == 'kucoin':
    #             temp[exchangename].append({'key': key, 'type': 'spot'})
    # loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in temp.items()]
    # await asyncio.gather(*loops)

    exchange={}
    for ex in exchanges.keys():
        exchange[ex]=[]
    for key in coindictnew:
        value = coindictnew[key]
        for exchangename in value['future']:
            if  exchangename =='binance':
                exchange[exchangename].append({'key':key,'symbol':value['future'][exchangename]['id'],'type':'future'})
            else:
                exchange[exchangename].append({'key': key, 'symbol': value['future'][exchangename]['symbol'],'type':'future'})
        for exchangename in value['spot']:
            if not exchangename == 'kucoin':
                exchange[exchangename].append({'key': key, 'symbol': value['spot'][exchangename]['symbol'],'type': 'spot'})
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchange.items()]
    await asyncio.gather(*loops)


USERCOINLIST=['POLYDOGE','POLYDOGE','YGG','REEF','GRT','INJ','OGN','DUSK','RNDR','ONT','CELR','LOOKS'
              ,'LDO','DYDX','XCN','MATIC','KAVA','GNS','FIL']
async def run():
    tasklist = []
    global coindictnew
    global orderList
    global bookSreenWall
    for key in exchanges.keys():
        orderList[key] = []
    if False:
        await loadAllFutureDataOnTime()

    with open('multiExchangeFuture202302.json', 'r') as f:
        coindictnew = json.load(f)  # 解码JSON数据
    del coindictnew['CVC']
    del coindictnew['TLM']
    del coindictnew['SC']
    del coindictnew['BNX']

    # 删除费率为负数的币种#########################################
    # for key in exchanges:
    #     await getExchangeFundFee(key)
    # dellist =[]
    # for coin,value in coindictnew.items():
    #     if len(value['spot'])<3:
    #         dellist.append(coin)
    #         continue
    #     minus =True #费率是否全为负，如果全是负数，则删除
    #     for ex in value['value'].keys():
    #         if value['value'][ex].get('fundingrate') and value['value'][ex]['fundingrate']>0.000001:
    #             minus=False
    #     if minus:
    #         dellist.append(coin)
    # for coin in dellist:
    #     del coindictnew[coin]
    ###############################################################

    ###############是否指定币种
    deletelist = []
    for key in coindictnew:
        if not key in USERCOINLIST:
            deletelist.append(key)
    for item in deletelist:
        del coindictnew[item]

    ###########################



    bookSreenWall=copy.deepcopy(coindictnew)
    for key in bookSreenWall.keys():
        book = bookSreenWall[key]
        for ex in book['future'].keys():
            book['future'][ex]=None
        for ex in book['spot'].keys():
            book['spot'][ex]=None
    th2 = asyncio.create_task(getWSSOrderbooks())
    tasklist.append(th2)
    th1 = asyncio.create_task(managerOrder())
    tasklist.append(th1)
    result = await asyncio.gather(*tasklist)
    await managerOrder()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        traceback.print_exc()