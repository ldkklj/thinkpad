import ccxt
import ccxt.async_support as ccxta  # noqa: E402
import time
import os
import sys
import threading
from gloabalfunc import *
from  ichat import *

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

# proxies = {
#     'https': 'http://127.0.0.1:10807/pac?auth=7cjiXKnWYJi1WOfYRn6U',
#     'http': 'https://127.0.0.1:10807/pac?auth=7cjiXKnWYJi1WOfYRn6U'
# }

proxies = {
    'https': 'http://127.0.0.1:7890',
    'http': 'http://127.0.0.1:7890'
}


#id:474202743@qq.com
#pw:fevath12@QW123
bitmex = ccxta.bitmex({
    'apiKey': 'qSCt5vDAXREpMumdjlZInju6',
    'secret': 'x7HXqYbvMEwQfm6Vi5pxpYm1CzxUjnMz440nn-7fPm4k6BdH',
})

#id:ldkkldkklj@gmail.com
#pw:fevath12QW@

bybit = ccxt.bybit({
    'apiKey': 'k4uvrsxPVf4SoItWoe',
    'secret': 'XTET4mCMf9neOdDgKa81fEsKM0bt8KwXUlBk',
})
bybit.proxies =proxies
bybitmk = bybit.load_markets()


okex = ccxt.okex({
    'apiKey': '1319ef8f-8524-441e-9c00-39fd9841fa12',
    'secret': '4EB4520B33CA3476B4618DE28094D40A',
    'password': 'fevath12QW@',
})
okex.proxies =proxies
okex.options['defaultType']='swap'
okexmk = okex.load_markets()


okex.create_order('BTC/USDT:USDT', 'market', 'buy', 1, 60000, {})
ddd=1
