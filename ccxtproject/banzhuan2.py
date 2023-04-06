import traceback
import time
from gloabalfunc import *
import asyncio
import nest_asyncio
import ccxt.async_support as ccxt
import time
from ichat import *
nest_asyncio.apply()

async def load(exchange, symbol):
    starttime = time.time()
    try:
        ret= {'orderbook': await exchange.fetch_order_book(symbol,5)}
        return ret
    except Exception as e:
        print(e)
        raise e

async def LeftMoney(exchange,type):
    try:
        balance = await exchange.fetch_balance()
        if balance:
            if type=='spot':
                return {
                    'usdt':balance['USDT']['free'],
                    'waves':balance['WAVES']['free']
                }
            else:
                waves = [item for item in balance['info']['positions'] if item['symbol'] == 'WAVESUSDT']
                amountfuture = float(waves[0]['positionAmt'])
                return {
                    'usdt':balance['USDT']['free'],
                    'waves':amountfuture
                }

    except Exception as e:
        print('\n\nError in load() with type =', type, '-', e)
        time.sleep(60)
        return None


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

async def run():
    exchangeSpot = ccxt.binance({
        'apiKey': 'vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y',
        'secret': '0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK',
    })

    await exchangeSpot.load_markets(True)
    exchangeFuture = ccxt.binance({
        'apiKey': 'vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y',
        'secret': '0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK',
    })
    exchangeFuture.options['defaultType'] = 'future'
    await exchangeFuture.load_markets(True)
    symbol = 'WAVES/USDT'
    maxint = 0
    minint = 1

    while True:
        time.sleep(0.1)
        leftmoneyS = await LeftMoney(exchangeSpot,'spot');
        leftmoneyF = await LeftMoney(exchangeFuture,'future');
        try:
            everything = {
                'spot': await load(exchangeSpot, symbol),
                'future': await load(exchangeFuture, symbol)
            }
        except Exception as e:
            print('\n\nError in load() with type =', type, '-', e)
            time.sleep(60)
            continue
        spotprice = everything['spot']['orderbook']['asks'][0][0]
        spotvolume = everything['spot']['orderbook']['asks'][0][1]
        futureprice = everything['future']['orderbook']['bids'][0][0]
        futurevolume = everything['future']['orderbook']['bids'][0][1]
        pricegap = (spotprice-futureprice)/spotprice
        if pricegap > maxint:
            maxint = pricegap
        elif pricegap < minint:
            minint = pricegap

        if pricegap <0.0015 and leftmoneyF['usdt']>10 and leftmoneyS['usdt']>10:
             loop = asyncio.get_event_loop()
             tasks = [quickOpenOrder(exchangeSpot, symbol, spotprice, 1.3, 'buy'),
                      quickOpenOrder(exchangeFuture, symbol, futureprice, 1.3, 'sell')]
             loop.run_until_complete(asyncio.wait(tasks))
        elif pricegap >0.01 and leftmoneyS['waves']>1.3 and leftmoneyF['waves']<-1.3:
             loop = asyncio.get_event_loop()
             tasks = [quickOpenOrder(exchangeSpot, symbol, spotprice, 1.3, 'sell'),
                      quickOpenOrder(exchangeFuture, symbol, futureprice, 1.3, 'buy')]
             loop.run_until_complete(asyncio.wait(tasks))
        sendMsg(3,str("pricegap:")+str(pricegap)+str("maxgap:")+str(maxint)+str("minint:")+str(minint))
    await exchangeSpot.close()
    await exchangeFuture.close()
    return everything



asyncio.run(run())