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

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

symbol = 'LUNC/USDT'
my_wallet ={}
openorderoffset= 0.0025
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
coinprice=0.00006

def sync_client(exchange_id):
    orderbook = None
    exchange = getattr(ccxt, exchange_id)()
    try:
        exchange.load_markets()
        market = exchange.market(symbol)
        orderbook = exchange.fetch_order_book(market['symbol'])
    except Exception as e:
        print(type(e).__name__, str(e))
    return { 'exchange': exchange.id, 'orderbook': orderbook }


async def async_client(exchange_id,exchange):
    orderbook = None
    # exchange = getattr(ccxta, exchange_id)()
    try:
        # await exchange.load_markets()
        start = time.time()
        market = exchange.market(symbol)
        orderbook = await exchange.fetch_order_book(market['symbol'])
        end = time.time()
        print(exchange_id, time.strftime("!%H:%M:%S", time.localtime()),end-start)
    except Exception as e:
        print(type(e).__name__, str(e))
    await exchange.close()
    return { 'exchange': exchange.id, 'orderbook': orderbook }

async def  quickOpenOrder(exchange,symbol,priceSpot,amount,side):
    order = await asycreteOrder(exchange,symbol,'limit',side,amount,priceSpot)
    tick=0
    while True:
        if(tick>500):
            if order:
                await asycancelOrder(exchange,order['id'],symbol)
                return None
        else:
            tick+=1
            time.sleep(2)
            if  order:
                order = await asyfetchOrder(exchange,order['id'],symbol)
                if order:
                    if not order['status'] == 'closed':
                        continue
                    else:
                        return order
                else:
                    return None
            else:
                return None


async def LeftMoney(exchange,symbol):
    try:
        balance = await exchange.fetch_balance()
        coinname = symbol[:-5]
        coinleft =0
        usdtleft =0
        if balance:
            if balance.get(coinname):
                coinleft = balance[coinname]['free']
            if balance.get('USDT'):
                usdtleft= balance['USDT']['free']
            return {coinname:coinleft,'USDT':usdtleft}
        else:
            return None
    except Exception as e:
        print('\n\nError in LeftMoney() ', e)
        time.sleep(1)
        return None

def innertransfer(exchange,amount,coin,direct):
    try:
        if exchange.id=='okex':
            if direct =='+':
                response = exchange.transfer(coin,amount,'6','18',params={})
            else:
                response = exchange.transfer(coin, amount, '18', '6', params={})
        elif exchange.id == 'kucoin':
            if direct == '+':
                response = exchange.transfer(coin, amount, 'main', 'trade', params={})
            else:
                response = exchange.transfer(coin, amount, 'trade','main', params={})
        print(response)
    except Exception as e:
        print('\n\nError in innertransfer() ', e)
        return None

async def transferMoney(exchange1,exchange2,coin,amount):
    try:
        code = coin
        amount = amount
        if  coin =='LUNC':
            tgtaddress = address[exchange2.id]['LUNC']
            if address[exchange2.id].get('meme'):
                tag = address[exchange2.id]['meme']
            else:
                tag = None
            if  address[exchange1.id].get('web'):
                params = {
                    'chain': address[exchange1.id]['web'],  # 'ERC20', 'TRC20', default is ERC20
                }
            else:
                params = {
                    'chain':'LUNC',
                }
            if  exchange1.id=='okex':
                params['fee']='1000'
                params['pwd'] = 'fevath12QW@'
                # params['chain'] = 'TRC20'
                innertransfer(okexNa, amount, coin, '-')
        else:
            tgtaddress = address[exchange2.id]['USDT']
            tag = None
            params = {}
            params['chain'] = 'TRC20'
            if exchange1.id == 'okex':
                params['fee'] = '0.8'
                params['pwd'] = 'fevath12QW@'
                params['chain'] = 'USDT-TRC20'
                innertransfer(okexNa,amount,coin,'-')
                amount -=1.5
        if exchange1.id=='huobi' or exchange1.id=='kucoin':
            response = await exchange1.withdraw(code, amount, tgtaddress, tag)
        else:
            response = await exchange1.withdraw(code, amount, tgtaddress, tag,params)
        print(response)
        offset = 1.5 if coin == 'USDT' else 2500
        if exchange2.id=='okex':
            s= threading.Timer(120, innertransfer, (okexNa, amount-offset, coin,'+'))
            s.start()
        elif exchange2.id=='kucoin':
            s= threading.Timer(20, innertransfer, (kucoinNa, amount-offset, coin,'+'))
            s.start()
    except Exception as e:
        print(type(e).__name__, str(e))

async def startBalance(exchangeAttrs):
    min_usdt_key = min(my_wallet,key=lambda k:my_wallet[k]['USDT'])
    max_usdt_key = max(my_wallet, key=lambda k:my_wallet[k]['USDT'])
    deltaUSDT = my_wallet[max_usdt_key]['USDT']-my_wallet[min_usdt_key]['USDT']
    if deltaUSDT>50:
        await transferMoney(exchangeAttrs[max_usdt_key], exchangeAttrs[min_usdt_key], 'USDT', deltaUSDT/2)
        print("transfer usdt from ",exchangeAttrs[max_usdt_key].id, exchangeAttrs[min_usdt_key].id,deltaUSDT/2)

    min_lunc_key = min(my_wallet, key=lambda k: my_wallet[k]['LUNC'])
    max_lunc_key = max(my_wallet, key=lambda k: my_wallet[k]['LUNC'])
    deltaLunc = my_wallet[max_lunc_key]['LUNC'] - my_wallet[min_lunc_key]['LUNC']
    if deltaLunc*coinprice > 30:
        await transferMoney(exchangeAttrs[max_lunc_key], exchangeAttrs[min_lunc_key], 'LUNC', deltaLunc / 2)
        print("transfer lunc from ",exchangeAttrs[max_lunc_key].id,exchangeAttrs[min_lunc_key].id,deltaLunc / 2)

def openOppositeMarginOrder():
    while True:
        time.sleep(60)
        luncNo=0
        for key in my_wallet.keys():
            luncNo += my_wallet[key]['LUNC']
        totalLuncValue = luncNo*coinprice
        try:
            balance =  bnfuture.fetch_balance()
            if balance:
                positions = balance['info']['positions']
                for pos in positions:
                    if pos['symbol']=='1000LUNCBUSD':
                        entryprice = float(pos['entryPrice'])
                        amt =float(pos['positionAmt'])
                        bnfutureValue = amt*entryprice
                        delta =  totalLuncValue+bnfutureValue
                        if delta>5:
                            orderbook = bnfuture.fetch_order_book('1000LUNC/BUSD')
                            if orderbook:
                                price = orderbook['bids'][0][0]
                                amount = delta /price
                                createOrder(bnfuture, '1000LUNC/BUSD', 'limit', 'sell', amount, price)
                        elif delta<-5:
                            orderbook = bnfuture.fetch_order_book('1000LUNC/BUSD')
                            if orderbook:
                                price = orderbook['asks'][0][0]
                                amount = abs(delta /price)
                                createOrder(bnfuture, '1000LUNC/BUSD', 'limit', 'buy', amount, price)
        except Exception as e:
            print(type(e).__name__, str(e))
            continue

async def multi_orderbooks(exchangeAttrs,tick):
    time.sleep(3)
    #########先看看每个钱包有多少钱多少币
    if tick %10==1:
        for exchangeName in exchangeAttrs.keys():
            leftmoney = await LeftMoney(exchangeAttrs[exchangeName],symbol)
            if leftmoney:
                my_wallet[exchangeName]=leftmoney
    print("--------------------------------------------------")
    # if tick % 60 == 1:
    #     await startBalance(exchangeAttrs)

    input_coroutines = [async_client(exchangeName,exchangeAttrs[exchangeName]) for exchangeName in exchangeAttrs.keys()]
    orderbooks = await asyncio.gather(*input_coroutines, return_exceptions=True)
    for i in range(0,len(orderbooks)):
        for j in range(0,len(orderbooks)):
            if i==j:
                continue
            else:
                if orderbooks[i]['orderbook'] and orderbooks[j]['orderbook']:
                    global coinprice
                    coinprice =(orderbooks[i]['orderbook']['bids'][0][0] + orderbooks[i]['orderbook']['asks'][0][0])/2
                    interal1 = (orderbooks[i]['orderbook']['bids'][0][0] - orderbooks[j]['orderbook']['asks'][0][0])/orderbooks[i]['orderbook']['bids'][0][0]
                    interal2 = (orderbooks[j]['orderbook']['bids'][0][0] - orderbooks[i]['orderbook']['asks'][0][0])/orderbooks[j]['orderbook']['bids'][0][0]
                    if interal1>openorderoffset :
                        ratio = (interal1-0.0002)/0.0008
                        amount = 11/orderbooks[i]['orderbook']['bids'][0][0]*ratio
                        minamount = min(orderbooks[j]['orderbook']['asks'][0][1],orderbooks[i]['orderbook']['bids'][0][1])
                        amount = amount if amount<minamount else minamount
                        if my_wallet[orderbooks[i]['exchange']]['LUNC']>amount and my_wallet[orderbooks[j]['exchange']]['USDT']>11:
                            # await quickOpenOrder(exchangeAttrs[orderbooks[j]['exchange']], symbol,orderbooks[j]['orderbook']['asks'][0][0], amount,'buy')
                            # await quickOpenOrder(exchangeAttrs[orderbooks[i]['exchange']], symbol,orderbooks[i]['orderbook']['bids'][0][0], amount, 'sell')
                           str1= str("interval1:")+format(interal1, '.4f')+str('interval2')+format(interal2, '.4f')+str(orderbooks[i]['exchange'])+str(orderbooks[j]['exchange'])
                           sendMsg(3,str1)
                    # if interal2 > openorderoffset :
                    #     amount = 11/orderbooks[i]['orderbook']['bids'][0][0]
                    #     if my_wallet[orderbooks[j]['exchange']]['LUNC'] > amount and my_wallet[orderbooks[i]['exchange']]['USDT']>11:
                    #         await quickOpenOrder(exchangeAttrs[orderbooks[j]['exchange']], symbol, orderbooks[j]['orderbook']['bids'][0][0], amount, 'sell')
                    #         await quickOpenOrder(exchangeAttrs[orderbooks[i]['exchange']], symbol, orderbooks[i]['orderbook']['asks'][0][0], amount, 'buy')
                    #         print("interval1:", interal1, 'interval2', interal2, i, j)
                    #         print(orderbooks[j]['exchange'], '>', orderbooks[i]['exchange'],orderbooks[j]['orderbook']['bids'][0][0],
                    #           orderbooks[j]['orderbook']['bids'][0][1], orderbooks[i]['orderbook']['asks'][0][0],
                    #               orderbooks[i]['orderbook']['asks'][0][1])
    return orderbooks


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
okexNa = ccxt.okex({
    'apiKey': '53edb788-6d50-45be-a44f-ebc2f448f8ef',
    'secret': '5EEE95F9706CD887CEB0982F49EDF338',
    'password': 'fevath12QW@',
})
bnfuture = ccxt.binance({
    'apiKey': 'vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y',
    'secret': '0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK',
})
bnfuture.options['defaultType']='future'
bnmarket =bnfuture.load_markets()

mexc = ccxta.mexc({
    'apiKey': 'mx0WY9l3iaNYWXpvo8',
    'secret': '518ba4e088d4472a81fa55707090007b',
})


kucoin = ccxta.kucoin({
    'apiKey': '62a3e8bd2b57f600014eb518',
    'secret': '83dcc4b9-61e1-4e01-82cc-6bec1cfd8b3a',
    'password': 'fevath12QW@',
})
kucoinNa = ccxt.kucoin({
    'apiKey': '62a3e8bd2b57f600014eb518',
    'secret': '83dcc4b9-61e1-4e01-82cc-6bec1cfd8b3a',
    'password': 'fevath12QW@',
})
# if __name__ == '__main__':
async def run():
    # Consider review request rate limit in the methods you call
    # exchanges = ["kucoin", "binance","okex","mexc","huobi"]
    exchangeAttrs = {}
    exchanges=[]
    exchanges.append(huobi)
    exchanges.append(binance)
    exchanges.append(mexc)
    exchanges.append(okex)
    exchanges.append(kucoin)

    # okexNa.load_markets()
    # kucoinNa.load_markets()
    #反向做空
    # th=threading.Thread(target=openOppositeMarginOrder,name="thread_1")
    # th.start()
    for i in range (0,len(exchanges)):
        exchange = exchanges[i]
        try:
            market= await exchange.load_markets()
            if  market.get(symbol) or market.get(symbol.strip('/')):
                exchangeAttrs[exchange.id]=exchange
        except Exception as e:
            print(e)
            continue

    # await transferMoney(mexc, kucoin, 'LUNC', 1035)
    # await transferMoney(okex, mexc, 'LUNC', 1035)
    # await transferMoney(okex, kucoin, 'LUNC', 1035)
    # await transferMoney(okex, huobi, 'LUNC', 1035)
    # transferMoney(mexc, okex, 'LUNC', 102)

    tick =0
    while True:
        tick+=1
        a = await multi_orderbooks(exchangeAttrs,tick)
    # print("async call spend:", time.time() - tic)
    time.sleep(1)

    # tic = time.time()
    a = [sync_client(exchange) for exchange in exchanges]
    print("sync call spend:", time.time() - tic)

asyncio.run(run())
