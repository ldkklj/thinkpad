# -*- coding: utf-8 -*-

import asyncio
import ccxt
import ccxt.async_support as ccxta  # noqa: E402
import time
import os
import sys
import threading
import copy
from gloabalfunc import *
from  ichat import *
import json
import numpy as np
from collections import OrderedDict


from urllib import request
import  requests
proxies = {
    'https': 'http://127.0.0.1:10807/pac?auth=7cjiXKnWYJi1WOfYRn6U',
    'http': 'https://127.0.0.1:10807/pac?auth=7cjiXKnWYJi1WOfYRn6U'
}
# try:
#     response = requests.get('https://www.google.com', proxies=proxies)
#     print(response.text)
# except requests.exceptions.ConnectionError as e:
#     print('Error', e.args)

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

my_wallet ={}
openorderoffset= 0.005
closeoffset =0.002
orderid=0
address={}
address['mexc']={
    'LUNC':'terra1tqem8yep4r86cxck2hf5cx87tms7ll4rtm4ytp',
    'USDT':'TD6btpko9tsdeuJCf6tXToZpVcfRLhLg8v'
}
address['okex']={
    'LUNC':'terra14cyve7ngc9mvm5q8lr5fpqxdu9xwupvrwyj7up',
    'USDT':'TRoYQFoj9e8HUhRncdZwEDHBEznTw2kyVH',
    'web':'LUNC-Terra'
}
address['binance']={
    'LUNC':'terra1ncjg4a59x2pgvqy9qjyqprlj8lrwshm0wleht5',
    'USDT':'THxD5pRwQUqHoV9636C1q3WSu5uEpyTdDS',
    'meme':'105429324'
}
address['huobi']={
    'LUNC':'terra1dj9qllvhtk50zfhu0qtswzvjzf4z5ul7k8k9p6',
    'USDT':'TUyepRXwKYUiuDqKjvW6g4TBREMciamMT7',
}
address['kucoin']={
    'LUNC':'terra14l46jrdgdhaw4cejukx50ndp0hss95ekt2kfmw',
    'USDT':'TTQLH5AXNWN4ee63af6naTFarSmxnnMUbw',
    'meme':'1921837824'
}






# huobi = ccxta.huobi({
#     'apiKey': '146d5676-ur2fg6h2gf-5f6cff3b-50178',
#     'secret': '40f5fa81-aee281b4-ae61fea3-fdea0',
# })
# huobi.options['defaultType']='future'
# huobiN = ccxt.huobipro({
#     'apiKey': '146d5676-ur2fg6h2gf-5f6cff3b-50178',
#     'secret': '40f5fa81-aee281b4-ae61fea3-fdea0',
# })
# huobiN.options['defaultType']='future'
# huobiN.options['defaultSubType']='inverse'
# huobiN.verbose = True
binance = ccxta.binance({
    'apiKey': 'vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y',
    'secret': '0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK',
})
binance.options['defaultType']='future'
binanceN = ccxt.binance({
    'apiKey': '146d5676-ur2fg6h2gf-5f6cff3b-50178',
    'secret': '40f5fa81-aee281b4-ae61fea3-fdea0',
})
binanceN.options['defaultType']='future'


okex = ccxta.okex({
    'apiKey': '53edb788-6d50-45be-a44f-ebc2f448f8ef',
    'secret': '5EEE95F9706CD887CEB0982F49EDF338',
    'password': 'fevath12QW@',
})
okex.options['defaultType']='swap'
okexN = ccxt.okex5({
    'apiKey': '53edb788-6d50-45be-a44f-ebc2f448f8ef',
    'secret': '5EEE95F9706CD887CEB0982F49EDF338',
    'password': 'fevath12QW@',
})
# okexN.proxies=proxies
# okexN.options['defaultType']='swap'
# mm = okexN.load_markets()
# order =okexN.create_order('LINK/USDT:USDT',1,1,50,7.0)


mexc = ccxta.mexc({
    'apiKey': 'mx0WY9l3iaNYWXpvo8',
    'secret': '518ba4e088d4472a81fa55707090007b',
})
mexc.options['defaultType']='swap'
mexcN = ccxt.mexc({
    'apiKey': 'mx0WY9l3iaNYWXpvo8',
    'secret': '518ba4e088d4472a81fa55707090007b',
})
# mexcN.proxies=proxies
# markets = mexcN.load_markets()
# order =mexcN.create_order('LINK/USDT:USDT',1,1,50,7.0,params = {'openType': 1, "leverage": 1, "positionType":1})


kucoin = ccxta.kucoin({
    'apiKey': '62a3e8bd2b57f600014eb518',
    'secret': '83dcc4b9-61e1-4e01-82cc-6bec1cfd8b3a',
    'password': 'fevath12QW@',
})

kucoinN = ccxt.kucoin({
    'apiKey': '62a3e8bd2b57f600014eb518',
    'secret': '83dcc4b9-61e1-4e01-82cc-6bec1cfd8b3a',
    'password': 'fevath12QW@',
})
kucoinN.options['defaultType']='future'
kucoinN.proxies=proxies
# mar = kucoinN.load_markets()
# order =kucoinN.create_order('LINK/USDT:USDT',1,1,50,7.0,params = {'openType': 1, "leverage": 1, "positionType":1})

ftx = ccxta.ftx({
    'apiKey': '1OCXHzNKjXMrg7WtX4q8FS8QQUW523XoaQZCbaxJ',
    'secret': 'FCMpn3-qqX8okAnltR16hzTPIPd85jmj66JWH3Ve',
    'password': 'fevath12QW@',
})
ftx.options['defaultType']='future'
ftxN = ccxt.ftx({
    'apiKey': '1OCXHzNKjXMrg7WtX4q8FS8QQUW523XoaQZCbaxJ',
    'secret': 'FCMpn3-qqX8okAnltR16hzTPIPd85jmj66JWH3Ve',
    'password': 'fevath12QW@',
})
# ftxN.proxies=proxies
# ftxN =ftxN.create_order('LINK/USDT:USDT',1,1,50,7.0,params = {'openType': 1, "leverage": 1, "positionType":1})

gate = ccxta.gateio(
    {'apiKey':'61ab9289c4bf2cf5f373f5daba6a3460',
     'secret':'f1f4b2d60964e79d11c6855768716304d785b8d270d76ac0771a4de4a3292975',
     'password': 'windows-999'
})
gate.options['defaultType']='swap'
gateN = ccxt.gateio(
    {'apiKey':'61ab9289c4bf2cf5f373f5daba6a3460',
     'secret':'f1f4b2d60964e79d11c6855768716304d785b8d270d76ac0771a4de4a3292975',
        'password': 'windows-999'
})
gateN.options['defaultType']='future'
# gateN.proxies=proxies
# order =gateN.create_order('LINK/USDT:USDT',1,1,50,7.0,params = {'openType': 1, "leverage": 1, "positionType":1})

exchanges = {}
# exchanges['huobi'] = huobi
# exchanges['mexc'] = mexc
exchanges['gateio']=gate
# exchanges['binance'] = binance
# exchanges['okex'] = okex
exchanges['kucoin'] = kucoin
exchanges['ftx'] = ftx


# exchangesN ={}
# exchangesN['huobi'] = huobiN
# exchangesN['mexc'] = mexcN
# exchangesN['binance'] = binanceN
# exchanges['okex'] = okex
#exchanges['kucoin'] = kucoin  #ccxt dont support kucoin future
# exchangesN['ftx'] = ftxN

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

dd=\
    {'buyorder': {'side': 'buy', 'exchange':1, 'intprice': 1, 'realprice':0, 'intAmt':1
                                  ,'realAmt':0,'status':'open','id':1,'symbol':1},
     'sellorder': {'side': 'sell','exchange':2,'intprice':2,'realprice':0,'intAmt':3
                                  ,'realAmt':0,'status':'open','id':3,'symbol':3}
    }
ff=45
async def async_client(exchange_id,exchange,coin):
    orderbook = None
    try:
        start = time.time()
        orderbook = await exchange.fetch_order_book(coin[exchange_id]['symbol'])
        end = time.time()
        # print(exchange_id, time.strftime("!%H:%M:%S", time.localtime()),end-start)
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
        if exchange.id=='mexc':
            side1 = 1 if side == 'buy' else 3
            priceSpot = priceSpot*1.02 if side=='buy' else priceSpot*0.98
            trade_type = 'ASK' if side == 'sell' else 'BID'
            order = await asycreteOrder(exchange,symbol,'limit',side1,amount/size,priceSpot,params={'openType':1,"trade_type":trade_type})
        else:
            order = await asycreteOrder(exchange,symbol,'limit',side,amount/size,priceSpot,None)
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
                if  pair['expiry']:
                    continue
                if pair['type'] == 'future'  or pair['type'] == 'swap' :
                    if exchange.id == 'ftx':
                        if pair['quoteId'] == 'USD' or pair['quoteId'] == 'usd':
                                if pair['expiry']:
                                    continue
                                if not temp.get(pair['base']):
                                    coin = {}
                                    coin[exchange.id] = pair
                                    temp[pair['base']] = coin
                                else:
                                    temp[pair['base']][exchange.id] = pair
                    else:
                        if pair['quoteId'] == 'USDT' or pair['quoteId'] == 'usdt':
                            if pair['expiry']:
                                continue
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

def loadjsonfile():
    global coinManage
    print('===============load suggestcoin===============')
    try:
        with open('suggestCoin.json', 'r') as f:
            suggestCoin = json.load(f)  # 解码JSON数据
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
                return True
            else:
                return False
    except Exception as e:
            sendMsg(3,'\n\nError in loadjsonfile()'+str(e))
            return False

async def refreshWallet():
    for exchangeName in exchanges.keys():
        leftmoney = await LeftMoney(exchanges[exchangeName])
        if leftmoney:
            my_wallet[exchangeName] = leftmoney

def getbookfromOrder(orderbook):
    return {
        'bid': orderbook['orderbook']['bids'][0][0],
        'ask': orderbook['orderbook']['asks'][0][0],
        'bidAmt': orderbook['orderbook']['bids'][0][1],
        'askAmt': orderbook['orderbook']['asks'][0][1],
    }

async def openorderPair(interval,book1,book2,exName1,exName2,coin,value,coinprice,amt=0,type='profit'):
    print('open order @@@@@@@@@@')
    global my_wallet
    global futurePos
    if type == 'profit':
        # minamount = min(book1['askAmt'], book2['bidAmt'])
        # if minamount < value[exName1]['precision']['amount'] or minamount < value[exName2]['precision']['amount']:
        #     return
        # amount = max(value[exName1]['precision']['amount'],10/coinprice,value[exName2]['precision']['amount'])
        amount = 11/coinprice
        # if my_wallet[exName2]['USDT'] > 30 and my_wallet[exName1]['USDT'] > 30 and not futurePos.get(coin):
        if my_wallet[exName2]['USDT'] > 30 and my_wallet[exName1]['USDT'] > 30 and not futurePos:
            input_coroutines=[]
            input_coroutines.append(quickOpenOrder(exchanges[exName1], value[exName1]['symbol'], book1['ask'], amount,value[exName1]['contractSize'],'buy'))
            input_coroutines.append(quickOpenOrder(exchanges[exName2], value[exName2]['symbol'], book2['bid'], amount,value[exName2]['contractSize'],'sell'))
            pairOrders = await asyncio.gather(*input_coroutines, return_exceptions=True)
            if pairOrders[0]:
                my_wallet[exName1]['USDT']-=amount * coinprice
                futurePos[coin] = {}
                futurePos[coin]['buyorder']={'side': 'buy', 'exchange': exName1, 'intprice': book1['ask'], 'realprice': 0,'intAmt': amount,
                                             'realAmt': 0, 'status': 'open', 'id': pairOrders[0]['id'], 'symbol': value[exName1]['symbol']}
            if pairOrders[1]:
                my_wallet[exName2]['USDT'] -= amount* coinprice
                if not futurePos.get(coin):
                    futurePos[coin] = {}
                futurePos[coin]['sellorder']= {'side': 'sell','exchange':exName2,'intprice': book2['bid'],'realprice':0,'intAmt':amount
                                  ,'realAmt':0,'status':'open','id':pairOrders[1]['id'],'symbol':value[exName2]['symbol']}
            if pairOrders[0] and pairOrders[1]:
                str1 = str(coin) + str('@') + str(exName1) +format(book1['ask'],'.4f') +'@' +\
                       str(exName2) + format(book2['bid'],'.4f')+'@'+\
                       format(interval,'.4f') + ':' + str('amt:') + str(amount) + '@'+\
                       str('profit')+ format(interval*amount*coinprice,'.2f')
            else:
                str1='failed to open pair order! '
            # await refreshWallet()
            sendMsg(3, str1)
        else:
            print('not enough coin')
    else:
        input_coroutines=[]
        input_coroutines.append(quickOpenOrder(exchanges[exName1], value[exName1]['symbol'], book1['ask'], amt,'buy'))
        input_coroutines.append(quickOpenOrder(exchanges[exName2], value[exName2]['symbol'], book2['bid'], amt,'sell'))
        pairOrders = await asyncio.gather(*input_coroutines, return_exceptions=True)
        if pairOrders[0] and pairOrders[1]:
            profit = pairOrders[1]['price']
            sendMsg(3, 'succeed close pair order!')

async def updateFuturePos():
    for key in futurePos.keys():
        fupos =futurePos[key]
        if not fupos['buyorder']['status']=='closed':
            order = await asyfetchOrder(exchanges[fupos['buyorder']['exchange']], fupos['buyorder']['id'], fupos['buyorder']['symbol'])
            if order and order['status']=='closed':
                fupos['buyorder']['status']='closed'
                fupos['buyorder']['realprice'] = order['price']
                fupos['buyorder']['realAmt'] = order['amount']
        if not fupos['sellorder']['status']=='closed':
            order = await asyfetchOrder(exchanges[fupos['sellorder']['exchange']], fupos['sellorder']['id'], fupos['sellorder']['symbol'])
            if order and order['status']=='closed':
                fupos['sellorder']['status']='closed'
                fupos['sellorder']['realprice'] = order['price']
                fupos['sellorder']['realAmt'] = order['amount']
        if fupos['buyorder']['status']=='closed' and fupos['sellorder']['status']=='closed':
                profitgap = (fupos['sellorder']['realprice']-fupos['buyorder']['realprice'])*2/(fupos['sellorder']['realprice']+fupos['buyorder']['realprice'])
                fupos['profitNeed2']=0.006-profitgap
def exchg(a,b):
    a,b=b,a
    return (a,b)

async def judgeAndCloseBalance(coin,interal1,interal2,book1,book2,ex1Name,ex2Name,value,coinprice):
    global futurePos
    fupos = futurePos[coin]
    if not fupos.get('profitNeed2'):
        return
    if fupos['buyorder']['exchange'] == ex2Name and fupos['sellorder']['exchange'] == ex1Name:
        exchg(interal1, interal2)
        exchg(book1, book2)
        exchg(ex1Name, ex2Name)
    #fullfill profit condition ,create double order
    if interal2>fupos.get('profitNeed2'):
        await openorderPair(interal2, book2, book1, ex2Name,
                      ex1Name, coin, value, coinprice, 'balance')


async def managerOrder():
    tick =0
    global exchanges
    global coindictnew
    global coinManage
    global futurePos
    tick=0
    while True:
        tick+=1
        await asyncio.sleep(7)
        if tick%1200==1:
            loadjsonfile()
        if tick%60==1:
            await refreshWallet()
        await updateFuturePos()
        for key in coinManage.keys():
            coinManage[key]['active'] -= 1
            value = coindictnew[key.coin]['value']
            input_coroutines = [async_client(exchangeName, exchanges[exchangeName], value) for exchangeName in value.keys()]
            orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
            for i in range(0, len(orderbooks)):
                for j in range(i, len(orderbooks)):
                    if i == j:
                        continue
                    else:
                        if not orderbooks[i] or not orderbooks[j] or not orderbooks[i].get('orderbook') or not orderbooks[j].get('orderbook'):
                            continue
                        exchange1 = orderbooks[i]['exchange']
                        exchange2 = orderbooks[j]['exchange']
                        if not my_wallet.get(exchange1):
                            continue
                        if not my_wallet.get(exchange2):
                            continue
                        book1 = getbookfromOrder(orderbooks[i])
                        book2 = getbookfromOrder(orderbooks[j])
                        coinprice = (book1['bid'] + book1['ask'] + book2['bid'] + book2['ask']) / 4
                        coinManage[key]['price']=coinprice
                        interal1= (book2['bid']-book1['ask'])/coinprice
                        interal2= (book1['bid']-book2['ask'])/coinprice
                        if futurePos.get(key.coin) and futurePos[key.coin]['buyorder']['exchange']==exchange1 and futurePos[key.coin]['sellorder']['exchange']==exchange2:
                            await judgeAndCloseBalance(key.coin, interal1, interal2, book1, book2, exchange1, exchange2, value,coinprice)
                        if interal1 >0.004:
                            coinManage[key]['active'] += 4
                            await openorderPair(interal1, book1, book2, key.exchange1, key.exchange2, key.coin, value,coinprice)
                            str1 = str(key.coin) + str(":itvl1:") + format(interal1, '.4f') + str('itvl2') + \
                                   format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
                            print(str1)
                        if interal2 >0.004:
                            coinManage[key]['active'] += 4
                            await openorderPair(interal2, book2, book1, key.exchange2, key.exchange1, key.coin, value,coinprice)
                            str1 = str(key.coin) + str(":itvl1:") + format(interal1, '.4f') + str('itvl2') + \
                                   format(interal2, '.4f') + str(orderbooks[i]['exchange']) + str(orderbooks[j]['exchange'])
                            print(str1)




async def run():
    tasklist = []
    global coindictnew
    global orderList
    for key in exchanges.keys():
        orderList[key] = []
    if True:
        await loadAllFutureDataOnTime()

    with open('coindictnewfuture.json', 'r') as f:
        coindictnew = json.load(f)  # 解码JSON数据
    th1 = asyncio.create_task(analyseCoin())
    tasklist.append(th1)
    coindictnew['EXCH']['value']['gateio']['precision']['amount']=0.001
    th2 = asyncio.create_task(managerOrder())
    tasklist.append(th2)
    result = await asyncio.gather(*tasklist)

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

if __name__ == '__main__':
    main()