# -*- coding: utf-8 -*-
#模仿cqz的策略

import asyncio
import ccxt
import ccxt.async_support as ccxta  # noqa: E402
import ccxt.pro
import time
import os
import sys
import traceback
import copy

from gloabalfunc import *
from  ichat import *
import json
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

exchanges['bitget'] = bitgeta
exchanges['okex']=okexa
exchanges['bybit'] = bybita
exchanges['phemex'] = phemexa
exchanges['mexc'] = mexca
exchanges['gateio'] = gateioa



my_pos={}
coinManage={}
coinData = {}
coinAnalyseRet = {}
suggestCoin = OrderedDict()
coindictnew={}
futurePos={}
orderList={}
bookSreenWall={}
totalpofit=0
dd=\
    {'buyorder': {'side': 'buy', 'exchange':1, 'intprice': 1, 'realprice':0, 'intAmt':1
                                  ,'realAmt':0,'status':'open','id':1,'symbol':1},
     'sellorder': {'side': 'sell','exchange':2,'intprice':2,'realprice':0,'intAmt':3
                                  ,'realAmt':0,'status':'open','id':3,'symbol':3}
    }

USERCOINLIST=['FLOKI','SHIB','GRT','PERP','COCOS','RDNT','CFX','GPT']
SPECIALCOINNAME={}
# ('FLOKI','phemex'):{'base':'FLOKI','ex':'phemex','key':'1000FLOKI/USDT','multi':1000}
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


async def  quickOpenOrder(exchange,value,priceSpot,amount,size,side):
    global orderList
    global orderid
    try:
        orderid+=1
        strorderid= 'order'+str(orderid)
        if exchange.id=='phemex':
            priceDot = int(value['info']['pricePrecision'])
            order = await asycreteOrder(exchange, value['symbol'], 'limit', side, round(amount / size), round(priceSpot,priceDot), None)
        else:
            order = await asycreteOrder(exchange,value['symbol'],'limit',side,round(amount/size),priceSpot,None)
        if order:
            orderList[exchange.id].append(order)
            return order
    except Exception as e:
        print(type(e).__name__, str(e))
        return None





# async def multi_orderbooks(coindict,tick,exchanges):
#     await asyncio.sleep(6)
#     #########先看看每个钱包有多少钱多少币
#     print("--------------------------------------------------")
#     # 计算数据统计结果
#     global my_pos
#     global coinAnalyseRet
#     global coinData
#     coinRecord={}
#     if tick % 11 == 1:
#         for data in coinData.values():
#             for key in data.keys():
#                 list1 = data[key]
#                 if len(list1) > 0:
#                     ret = {}
#                     ret['var'] = np.var(list1)
#                     ret['std'] = np.std(list1)
#                     ret['mean'] = np.mean(list1)
#                     ret['uplimit'] = ret['mean']+ret['std']
#                     ret['lowerlimit']=ret['mean']-ret['std']
#                     coinAnalyseRet[key.coin+'@'+key.exchange1+'@'+key.exchange2] = ret
#                     coinRecord[key.coin+'@'+key.exchange1+'@'+key.exchange2]=list1
#                 data[key]=[]
#         if len(coinAnalyseRet):
#             result = sorted(coinAnalyseRet.items(), key=lambda x: x[1]['std'], reverse=True)
#             if len(result) > 20:
#                 for i in range(0, len(result)):
#                     val = result[i][1]
#                     keyStr = result[i][0]
#                     strr = keyStr + '-var:' + format(val['var'],'.4f') + \
#                            str('-std:')+format(val['std'],'.4f') + str('-mean:')+format(val['mean'],'.4f')
#                     print(strr)
#                     if abs(val['std']) > 0.0015 and abs(val['mean'])<0.03:
#                         suggestCoin[keyStr] = val
#                     if len(suggestCoin)>0:
#                         with open('suggestCoin.json', 'w') as f:
#                             json.dump(suggestCoin, f)  # 编码JSON数据
#                 with open('coinAnalyseRet.json', 'w') as f:
#                     json.dump(result, f)  # 编码JSON数据
#                 with open('coinRecord.json', 'w') as f:
#                     json.dump(coinRecord, f)  # 编码JSON数据
#
#     for key in coindict.keys():
#         value = coindict[key]['value']
#         input_coroutines = [async_client(exchangeName, exchanges[exchangeName], value) for exchangeName in value.keys()]
#         orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
#         for i in range(0, len(orderbooks)):
#             for j in range(i, len(orderbooks)):
#                 if i == j:
#                     continue
#                 else:
#                     if orderbooks[i] and orderbooks[j] and  orderbooks[i]['orderbook'] and orderbooks[j]['orderbook'] \
#                             and len(orderbooks[i]['orderbook']['bids']) > 0 and len(orderbooks[j]['orderbook']['bids']) > 0:
#                         global coinprice
#                         coinprice = (orderbooks[i]['orderbook']['bids'][0][0] + orderbooks[i]['orderbook']['asks'][0][ 0]) / 2
#                         interal1 = (orderbooks[i]['orderbook']['bids'][0][0] - orderbooks[j]['orderbook']['asks'][0][0])/orderbooks[i]['orderbook']['bids'][0][0]
#                         interal2 = (orderbooks[j]['orderbook']['bids'][0][0] - orderbooks[i]['orderbook']['asks'][0][0])/orderbooks[j]['orderbook']['bids'][0][0]
#                         coinpair = SingleCoinPair(key, orderbooks[i]['exchange'], orderbooks[j]['exchange'])
#                         realinv = None
#                         if interal1 > 0:
#                             realinv = interal1
#                         if interal2 > 0:
#                             realinv = -interal2
#                         if realinv:
#                             if coinData[key].get(coinpair):
#                                 coinData[key][coinpair].append(realinv)
#                             else:
#                                 datalist = []
#                                 datalist.append(realinv)
#                                 coinData[key][coinpair] = datalist




async def loadAllFutureDataOnTime():
    global exchanges
    temp = {}
    coindict = {}
    market={}
    global coindictnew

    for exName in exchanges.keys():
        exchange = exchanges[exName]
        try:
            market[exName] = await exchange.load_markets()
            with open(exName+'.json', 'w') as f:
                json.dump(market[exName], f)  # 编码JSON数据
            for key in market[exName].keys():
                pair = market[exName][key]
                if exName == 'mexc' and pair['info']['isSpotTradingAllowed']==False:
                    continue
                if pair['base'] in USERCOINLIST  :
                    if  pair['type'] == 'spot' or pair['type'] == 'SPOT' :
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
    # for key,item in SPECIALCOINNAME.items():
    #     value = market[item['ex']][item['key']]
    #     value['base']=item['base']
    #     value['contractSize']=item['multi']
    #     if not coindict.get(item['base']):
    #         coindict[item['base']]={'spot':{item['ex']:value}}
    #     else:
    #         if len(coindict[item['base']]['spot'])==0:
    #             coindict[item['base']]['spot']={item['ex']:value}
    #         else:
    #             coindict[item['base']]['spot'][item['ex']]= value
    with open('multiExchangeFuture202304.json', 'w') as f:
        json.dump(coindict, f)  # 编码JSON数据


async def LeftMoney(exchangeid,exchange):
    ret = {}
    ret['pos'] = []
    global  my_wallet
    try:
        if exchange.id == 'bybit':
            exchange.options['recvWindow'] = 100000000
        balance = await exchange.fetch_balance()
        if balance:
            if exchangeid=='binance':
                if 'info' in balance.keys() and 'balances' in balance['info'].keys():
                    for item in balance['info']['balances']:
                        if float(item['free']) > 0.0001 and item['asset'] in my_wallet[exchangeid].keys():
                            my_wallet[exchangeid][item['asset']]['left'] = float(item['free'])
            elif exchangeid=='bitget':
                if 'info' in balance.keys():
                    for item in balance['info']:
                        if float(item['available'])>0.0001 and item['coinName'] in my_wallet[exchangeid].keys():
                            my_wallet[exchangeid][item['coinName']]['left']=float(item['available'])
            elif exchangeid =='okex':
                 if 'free' in balance.keys():
                    for key in balance['free'].keys():
                        if key in my_wallet[exchangeid]:
                            my_wallet[exchangeid][key]['left']=balance['free'][key]
            elif exchangeid =='bybit':
                if 'free' in balance:
                    for key,item in balance['free'].items():
                        if balance['free'][key]>0.0001  and key in my_wallet[exchangeid]:
                            my_wallet[exchangeid][key]['left']=balance['free'][key]
            elif exchangeid =='lbank':
                if 'free' in balance:
                    for key,item in balance['free'].items():
                        if balance['free'][key]>0.0001  and key in my_wallet[exchangeid]:
                            my_wallet[exchangeid][key]['left']=balance['free'][key]
                for key,item in balance.items():
                    if 'free' in item and item['free']>0.0001:
                        my_wallet[exchangeid][key]['left'] = item['free']
            else :
                if 'free' in balance:
                    for key,item in balance['free'].items():
                        if balance['free'][key]>0.0001  and key in my_wallet[exchangeid]:
                            my_wallet[exchangeid][key]['left']=balance['free'][key]
        else:
            return None
    except Exception as e:
        print('\n\nError in LeftMoney() ', e)
        return None

async def refreshWallet(ifFetch = True):
    global bookSreenWall
    global my_wallet
    total =0

    if ifFetch:
        loops = [LeftMoney(exchange_id, exchange) for exchange_id, exchange in exchanges.items()]
        await asyncio.gather(*loops)

    for coin in bookSreenWall.keys():
        total =0
        exNum = len(bookSreenWall[coin]['spot'])
        if exNum ==0:
            continue
        else:
            for ex in my_wallet.keys():
                if coin in my_wallet[ex]:
                    total =total + my_wallet[ex][coin]['left']
            avg = total/exNum
            if not total ==0:
                for ex1 in my_wallet.keys():
                    for ex2 in my_wallet.keys():
                        if not ex1 == ex2 and coin in my_wallet[ex1] and coin in my_wallet[ex2] and my_wallet[ex1][coin]['left']<my_wallet[ex2][coin]['left']:
                            diff = min(my_wallet[ex2][coin]['left']-avg,avg-my_wallet[ex1][coin]['left'])
                            if diff >avg*0.2:
                                if 'diff' in bookSreenWall[coin]:
                                    bookSreenWall[coin]['diff'][(ex1, ex2)]=diff
                                else:
                                    bookSreenWall[coin]['diff']={(ex1, ex2):diff}
                #
                #
                # for ex1 in bookSreenWall[coin]['spot']:
                #     for ex2 in bookSreenWall[coin]['spot']:
                #         if not ex1==ex2 and ex1 in my_wallet and ex2 in my_wallet and my_wallet[ex2][coin]['left']-my_wallet[ex1][coin]['left']>0.0001:
                #             diff = my_wallet[ex2][coin]['left']-my_wallet[ex1][coin]['left']
                #             if abs(diff/(my_wallet[ex2][coin]['left']+my_wallet[ex1][coin]['left']))>0.8 and my_wallet[ex2][coin]['left']>total/exNum:
                #                 if 'diff' in bookSreenWall[coin] :
                #                     bookSreenWall[coin]['diff'][(ex1,ex2)]=my_wallet[ex2][coin]['left']-my_wallet[ex1][coin]['left']
                #                 else:
                #                     bookSreenWall[coin]['diff']={(ex1,ex2):my_wallet[ex2][coin]['left']-my_wallet[ex1][coin]['left']}
                #             else:
                #                 if (ex1,ex2) in bookSreenWall[coin]['diff']:
                #                     del bookSreenWall[coin]['diff'][(ex1,ex2)]
    print(my_wallet)

def getbookfromOrder(key,orderbook):
    books ={}
    if not orderbook:
        return None
    else:
        now = time.time()
        for ex,value in orderbook['spot'].items():
            if value and value[3] :
                if not ex =='mexc' :
                    if abs(now-value[3]/1000.0)<2:
                    #temptuple =(key,ex)
                    # if not SPECIALCOINNAME.get(temptuple):
                        books[ex]={}
                        books[ex]['bid']=value[2][0]
                        books[ex]['bidamt'] = value[2][1]
                        books[ex]['ask']=value[1][0]
                        books[ex]['askamt'] = value[1][1]
                else:
                    books[ex] = {}
                    books[ex]['bid'] = value[2][0]
                    books[ex]['bidamt'] = value[2][1]
                    books[ex]['ask'] = value[1][0]
                    books[ex]['askamt'] = value[1][1]
                # else:
                #     books[ex]={}
                #     books[ex]['bid']=value[2][0]/SPECIALCOINNAME[temptuple]['multi']
                #     books[ex]['bidamt'] = value[2][1]*SPECIALCOINNAME[temptuple]['multi']
                #     books[ex]['ask']=value[1][0]//SPECIALCOINNAME[temptuple]['multi']
                #     books[ex]['askamt'] = value[1][1]*SPECIALCOINNAME[temptuple]['multi']
        return books

async def openorderPair(interval,book1,book2,exName1,exName2,coin,value,coinprice,type='profit'):
    print('open order @@@@@@@@@@'+type+''+exName1+''+exName2+coin)
    global futurePos
    if not coin in  futurePos:
        futurePos[coin]=[]
        maxV = max(value[exName1]['limits']['amount']['min'],value[exName2]['limits']['amount']['min'])
        minV = min(book1['askamt'],book2['bidamt'],my_wallet[exName1]['USDT']['left']/coinprice,
                         my_wallet[exName2][coin]['left'])
        if maxV > minV:
            return 0
        elif maxV == minV:
            if maxV>0:
                amount = maxV
        else:
            dis = minV -maxV
            if type =='profit':
                amount = maxV+pow(interval-openorderoffset,0.1)
            else:
                amount = bookSreenWall[coin]['diff'][(exName1, exName2)]
    # if type == 'profit':
    #     amount = max(value[exName1]['limits']['amount']['min'],
    #                  value[exName2]['limits']['amount']['min'],
    #                  min(book1['askamt'],book2['bidamt'],
    #                      my_wallet[exName1]['USDT']['left']/coinprice,
    #                      my_wallet[exName2][coin]['left'],
    #                      round((interval/0.0015)/coinprice))),
    # else:
    #     amount = max(min(book1['askamt'],book2['bidamt'],my_wallet[exName1]['USDT']['left']/coinprice,
    #                      bookSreenWall[coin]['diff'][(exName1,exName2)]/2),
    #                  value[exName1]['limits']['amount']['min'],
    #                  value[exName2]['limits']['amount']['min'],
    #                  )

        if amount >0:
            pair = \
                {'buyorder': {'side': 'buy', 'exchange': exName1, 'intprice': book1['ask'], 'realprice': 0, 'intAmt': amount
                    , 'realAmt': 0, 'status': 'init', 'id': 0, 'symbol': value[exName1]['symbol']},
                 'sellorder': {'side': 'sell', 'exchange': exName2, 'intprice': book2['bid'], 'realprice': 0, 'intAmt': amount
                     , 'realAmt': 0, 'status': 'init', 'id': 0, 'symbol': value[exName2]['symbol']}
                 }
            input_coroutines=[]
            input_coroutines.append(quickOpenOrder(exchanges[exName1], value[exName1], book1['ask']*1.01, amount,1,'buy'))
            input_coroutines.append(quickOpenOrder(exchanges[exName2], value[exName2], book2['bid']*0.99, amount,1,'sell'))
            pairOrders = await asyncio.gather(*input_coroutines, return_exceptions=True)
            await asyncio.sleep(1)
            await refreshWallet(True)
            if pairOrders[0]:
                pair['buyorder']['status'] = 'open'
                pair['buyorder']['id'] = pairOrders[0]['id']
            if pairOrders[1]:
                pair['sellorder']['status'] = 'open'
                pair['sellorder']['id'] = pairOrders[1]['id']
            if pairOrders[0] and pairOrders[1]:
                str1 = str(coin) + str(pair)+ str('profit')+ format(interval*amount*coinprice,'.2f')
                futurePos[coin].append(pair)
            else:
                str1='failed to open pair order! '
            sendMsg(3, str1)
            return True
        else:
            print('not enough coin or less than min amount')
            return False


async def updateFuturePos():
    global totalpofit
    for key in futurePos.keys():
        pairlist =futurePos[key]
        if len(pairlist) == 0:
            continue
        for fupos in pairlist:
            if not fupos['buyorder']['status']=='closed':
                order = await asyfetchOrder(exchanges[fupos['buyorder']['exchange']], fupos['buyorder']['id'],  fupos['buyorder']['symbol'])
                if order and order['status']=='closed':
                    fupos['buyorder']['status']='closed'
                    fupos['buyorder']['realprice'] = order['average']
                    fupos['buyorder']['realAmt'] = order['filled']
            if not fupos['sellorder']['status']=='closed':
                order = await asyfetchOrder(exchanges[fupos['sellorder']['exchange']], fupos['sellorder']['id'], fupos['sellorder']['symbol'])
                if order and order['status']=='closed':
                    fupos['sellorder']['status']='closed'
                    fupos['sellorder']['realprice'] = order['average']
                    fupos['sellorder']['realAmt'] = order['filled']
            if fupos['buyorder']['status']=='closed' and fupos['sellorder']['status']=='closed':
                    profitgap = (fupos['sellorder']['realprice']-fupos['buyorder']['realprice'])*2/(fupos['sellorder']['realprice']+fupos['buyorder']['realprice'])
                    fupos['profitNeed2'] = 0.006 - profitgap
                    realprofit = fupos['sellorder']['realprice']*fupos['sellorder']['realAmt']*0.999\
                                 -fupos['buyorder']['realprice']*fupos['buyorder']['realAmt']*1.001
                    totalpofit+=realprofit
                    str1 = str(key) + str(fupos) + str('**Realprofit**') + format(realprofit, '.2f')+str('totalprofit:')+str(totalpofit)
                    sendMsg(3, str1)

def exchg(a,b):
    a,b=b,a
    return (a,b)

# async def judgeAndCloseBalance(coin,interal2,book1,book2,ex1Name,ex2Name,value,coinprice):
async def judgeAndCloseBalance(coin, book, value, coinprice):
    global futurePos

#     'bid': orderbook['orderbook']['bids'][0][0],
#     'ask': orderbook['orderbook']['asks'][0][0],
#     'bidAmt': orderbook['orderbook']['bids'][0][1],
#     'askAmt': orderbook['orderbook']['asks'][0][1],
#     'exchange': orderbook['exchange']

    # dd = \
    #     {'buyorder': {'side': 'buy', 'exchange': 1, 'intprice': 1, 'realprice': 0, 'intAmt': 1
    #         , 'realAmt': 0, 'status': 'open', 'id': 1, 'symbol': 1},
    #      'sellorder': {'side': 'sell', 'exchange': 2, 'intprice': 2, 'realprice': 0, 'intAmt': 3
    #          , 'realAmt': 0, 'status': 'open', 'id': 3, 'symbol': 3}
    #      }
    pairlist = futurePos[coin]
    dellist=[]
    for idx in range(len(pairlist)):
        fupos = pairlist[idx]
        sellex = fupos['buyorder']['exchange']
        buyex = fupos['sellorder']['exchange']
        if 'profitNeed2' in fupos and buyex in book and sellex in book:
            inteval = book[sellex]['bid']-book[buyex]['ask']
            if inteval >-0.001:
                ret = await openorderPair(inteval, book[buyex], book[sellex],
                                    buyex, sellex, coin, value['value'],
                                    coinprice,fupos['sellorder']['realAmt'] * value['value'][buyex]['contractSize'],
                                    'balance', idx)
                if ret == 'successclose':
                    dellist.append(idx)
    for counter,index in dellist:
        index = index-counter
        pairlist.pop(index)



def avg(nums):
    nums = list(nums)
    return round(sum(nums) / len(nums), 10)


async def symbol_loop(exchange, symbol):
    global bookSreenWall
    while True:
        try:
            orderbook = await exchange.watch_order_book(symbol['symbol'])
            bookSreenWall[symbol['key']]['spot'][exchange.id]= {1:orderbook['asks'][0],2:orderbook['bids'][0],3:orderbook['timestamp']}
        except Exception as e:
            print(str(e))
            break

async def exchange_loop(exchange_id, symbols):
    exchange = getattr(ccxt.pro, exchange_id)()
    # exchange =exchanges[exchange_id]
    # exchange.aiohttp_proxy = proxies['http']
    # exchange.aiohttpProxy = proxies['http']
    loops = [symbol_loop(exchange, symbol) for symbol in symbols]
    await asyncio.gather(*loops)
    await exchange.close()


async def WSSgetOrderbooks():
    exchange={}
    for ex in exchanges.keys():
        exchange[ex]=[]

    for key in coindictnew:
        value = coindictnew[key]
        for exchangename in value['spot']:
            if   exchangename =='bitget' or exchangename =='binance':
                exchange[exchangename].append({'key':key,'symbol':value['spot'][exchangename]['id']})
            else:
                exchange[exchangename].append({'key':key,'symbol': value['spot'][exchangename]['symbol']})
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchange.items()]
    await asyncio.gather(*loops)

async def managerOrder():
    global exchanges
    global coindictnew
    global coinManage
    global futurePos
    global bookSreenWall
    global my_wallet
    tick=0
    while True:
        tick+=1
        strtime = time.strftime("!%H:%M:%S", time.localtime())
        print(strtime)
        if tick%500==1:
            await refreshWallet()
        await updateFuturePos()
        for key in bookSreenWall.keys():
            # await asyncio.sleep(0.5)
            value = coindictnew[key]
            book=getbookfromOrder(key,bookSreenWall[key])
            if book and len(book)>1:
                coinprice = (avg(bkorder['bid'] for bkorder in book.values()) + avg(bkorder['ask'] for bkorder in book.values())) / 2
                bookSreenWall[key]['price']=coinprice
                #先检查有没有平衡机会
                for ex1 in book:
                    for ex2 in book:
                        if not ex1 == ex2 and (ex1,ex2) in bookSreenWall[key]['diff']:
                            intervalB = (book[ex2]['bid'] - book[ex1]['ask']) / coinprice
                            if intervalB>closeoffset: #执行交易所迁移
                                str1=str('balance:'+str(key) + '@' + str(intervalB) + '@' + str(ex1) + '/' + str(ex2))
                                sendMsg(3, str1)
                                await openorderPair(intervalB,book[ex1],book[ex2],ex1,ex2,key,value['spot'],coinprice,'balance')
                minAskExchange = min(book.keys(), key=(lambda k: book[k]['ask']))
                maxBidExchange = max(book.keys(), key=(lambda k: book[k]['bid']))
                if not minAskExchange == maxBidExchange:
                    interval = (book[maxBidExchange]['bid'] - book[minAskExchange]['ask']) / coinprice
                    if interval > openorderoffset :  #执行套利
                        str1=(str(key)+'@'+str(interval)+'@'+str(minAskExchange)+'/'+str(maxBidExchange))
                        sendMsg(3,str1)
                        await openorderPair(interval, book[minAskExchange], book[maxBidExchange],minAskExchange,maxBidExchange,key,value['spot'],coinprice,'profit')

            # bad = False
            # for i in range(0, len(       )):
            #     tempbook = getbookfromOrder(orderbooks[i])
            #     if not tempbook:
            #         bad =True
            #         continue
            #     else:
            #         book[tempbook['exchange']]=tempbook
            # if bad :
            #     continue
            # coinprice = (avg(bkorder['bid'] for bkorder in book.values())+avg(bkorder['ask'] for bkorder in book.values()))/2
            # if coinprice <0.00000001:
            #     dde=12
            # if futurePos.get(key):
            #     await judgeAndCloseBalance(key,book,value,coinprice)
            # minAskExchange = min(book.keys(), key=(lambda k: book[k]['ask']))
            # maxBidExchange = max(book.keys(), key=(lambda k: book[k]['bid']))
            # if not minAskExchange == maxBidExchange:
            #     interval =  (book[maxBidExchange]['bid']-book[minAskExchange]['ask'])/coinprice
            #     # print(interval)
            #     if interval>0.008:
            #         str1 = str(key) + str(":itvl1:") + format(interval, '.4f') + str(book[minAskExchange]) + str(book[maxBidExchange])
            #         print(str1)
            #         end = time.time()
            #         print(time.strftime("!%H:%M:%S", time.localtime()),end-start)
            #         ret =await openorderPair(interval, book[minAskExchange], book[maxBidExchange], book[minAskExchange]['exchange'], book[maxBidExchange]['exchange'], key, value['value'],coinprice,'profit')
            #         str1 = str(key) + str(":itvl:") + format(interval, '.4f') + str(book[minAskExchange]) + str(book[maxBidExchange])
            #         print(str1)
            #         if ret:
            #             await asyncio.sleep(4)
            #



async def run():
    tasklist = []
    global coindictnew
    global orderList
    global bookSreenWall
    global my_wallet
    for key in exchanges.keys():
        orderList[key] = []
    if False:
        await loadAllFutureDataOnTime()
        await asyncio.sleep(10)

    with open('multiExchangeFuture202304.json', 'r') as f:
        coindictnew = json.load(f)  # 解码JSON数据

    for exid in exchanges.keys():
        my_wallet[exid] ={}
        my_wallet[exid]['USDT']= {'left':0,'offset':0}

    bookSreenWall=copy.deepcopy(coindictnew)
    for key in bookSreenWall.keys():
        book = bookSreenWall[key]
        for ex in book['spot'].keys():
            book['spot'][ex]=None
            my_wallet[ex][key]= {'left':0}



    th1 = asyncio.create_task(WSSgetOrderbooks())
    tasklist.append(th1)
    th2 = asyncio.create_task(managerOrder())
    tasklist.append(th2)
    result = await asyncio.gather(*tasklist)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        traceback.print_exc()