import threading
import traceback
import time

from threading import Timer
# import sched
# def sayhello():
#     strtime = time.strftime("hello world %Y-%m-%d-%H:%M:%S", time.localtime())
#     print(strtime)
#


# def func():
#     strtime = time.strftime("hello world %Y-%m-%d-%H:%M:%S", time.localtime())
#     time.sleep(3)
#     print(strtime)
#
# class RepeatingTimer(Timer):
#     def run(self):
#         while not self.finished.is_set():
#             self.function(*self.args, **self.kwargs)
#             self.finished.wait(self.interval)
# # t = RepeatingTimer(5.0,func)
# # t.start()
# def main():
#     t = RepeatingTimer(2.0, func)
#     t.start()
#
# try:
#      main()
# except Exception as e:
#     print(e)
#     traceback.print_exc()
#
#
#
# import threading
# def func1():
#     #Do something
#     print('Do something')
#
#     tread = threading.current_thread()
#     print('当前线程数为{}'.format(tread))
#     t=threading.Timer(5, func1)
#     t.start()
# t=threading.Timer(5,func1)
# t.start()


###########phase1###############
# import time
# import threading
# import ccxt
# biance = ccxt.binance()
# biance.apiKey='kFL6HJH7bv1kwSElGxzkI6BkcC0ZiUpM3qe2lWEBZk9Ba2QyAkpbB9vDoCb6KKSk'
# biance.secret='5eW823yAcwGh8sPGewolb9HGVRCL8hWFnBqNSB9S1FV6xVhBXWeMJiEeQF64bhyh'
# biance.options['defaultType']='future'
# biance.load_markets()
# tradepairs=biance.markets
#
# def analyse1Min():
#     t = threading.Timer(2, repeat1min)
#     t.start()
#
#
# def repeat1min():
#     analyse1Min()
#     print('Now-1:', time.strftime('%H:%M:%S', time.localtime()))
#     time.sleep(3)
#     tread = threading.current_thread()
#     print('当前线程{}'.format(tread))
#     print('Now-2:', time.strftime('%H:%M:%S', time.localtime()))
#
# analyse1Min()
###########phase2###############

from queue import Queue
from queue import PriorityQueue
queue = PriorityQueue()
mylock = threading.Lock()

import asyncio
import ccxt
from gloabalfunc import *
biance = ccxt.binance()
#69y 1
biance.apiKey='vc80GCBbsx4iWZ5fzJVCn3pn5Aczybj9mKsdGuWeJFbhVPmpyjrmsYjj9qRKn69y'
biance.secret='0jKZL2cSBof1TejOq7kdJ34BgVxegZ6MJ9Bi3P8poAKfAH5qkd1Ub7rFxhlRbuXK'
biance.options['defaultType']='future'
biance.load_markets()

# async def a(tick):
#     print("check top point:"+str(tick))
#     while True:
#         try:
#             orderbook = getOrderbook(biance, 'SUSHI/USDT')
#         except Exception as e:
#             await asyncio.sleep(10)
#             continue
#         await asyncio.sleep(5)
#         return price = orderbook["bids"][0][0]
#     tick+=4
#     await asyncio.sleep(10)
#     print("finish check top point"+str(tick))
#     return tick


# async def a(tick):
#     print("check top point:"+str(tick))
#     price =0.0
#     overtime =0
#     while True:
#         try:
#             orderbook = getOrderbook(biance, 'SUSHI/USDT')
#         except Exception as e:
#             await asyncio.sleep(10)
#             continue
#         if orderbook["bids"][0][0] > price:
#             overtime +=1
#
#         return price = orderbook["bids"][0][0]
#     tick+=4
#     await asyncio.sleep(10)
#     print("finish check top point"+str(tick))
#     return tick

async def a(ddd):
    trend='up'
    overtime =0
    tick=0
    price = None
    sleeptime = 5
    priceH=0.0
    priceL=0.0
    while True:
        try:
            orderbook = getOrderbook(biance,'BTC/USDT')
            if orderbook is not None:
                if trend == 'up':
                    if orderbook["asks"][0] is not None:
                        price = orderbook["asks"][0][0]
                        if price > priceH:
                            priceH= price
                            tick=0
                elif trend == 'down':
                    if orderbook["bids"][0] is not None:
                        price = orderbook["bids"][0][0]
                        if price <priceL:
                            priceL=price
                            tick=0
                tick+=1
        except Exception as e:
            print(e)
            await asyncio.sleep(10)
            tick =0
            continue
        if tick * sleeptime > 300:
            return price
        await asyncio.sleep(sleeptime)


def repeat1min():
    while True:
        mylock.acquire()
        if not queue.empty():
            task = queue.get()
            print(task[1])
        mylock.release()

       # time.sleep(7)


def insertPriOrderlist():
    tick=0
    while True:
        trade={}
        trade['tick']=tick
        trade['flower'] = 'flower'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task1 =loop.create_task(a(tick))
        # 执行coroutine
        loop.run_until_complete(task1)
        loop.close()
        trade['money']=task1.result()
        mylock.acquire()
        queue.put((1,trade))
        mylock.release()
        time.sleep(1)


def callback(task):
    print('task done'+str(task.result()))

def dealallorders():
    tick = 0
    while True:
        task={}
        task['tick']=tick
        task['gun'] = 'gun'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task1 =loop.create_task(a(tick))
        task1.add_done_callback(callback)
        # 执行coroutine
        loop.run_until_complete(task1)
        loop.close()
        task['money']=task1.result()
        print(task)
        # mylock.acquire()
        # queue.put((10,task))
        # mylock.release()
        time.sleep(1)


def main():
    #删除成交量太低的交易对

    #threading.Thread(name='watchOHLC',target=repeat1min).start()
    #threading.Thread(name='createorder', target=insertPriOrderlist).start()
    threading.Thread(name='managerorder', target=dealallorders).start()

try:
     main()
except Exception as e:
    sendMsg(e)
    traceback.print_exc()
