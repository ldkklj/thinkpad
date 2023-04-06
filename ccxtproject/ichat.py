# coding:utf-8
import requests
import json
import time
url = 'https://oapi.dingtalk.com/robot/send?access_token=f53ecde4568ac70ad6057e62c5bbe05295218280dc8dbc3cc20a555f9df936df'
headers = {
    "Content-Type": "application/json; charset=utf-8"
}
msglist=[]
def sendMsg(level,msg):
    if len(msglist)>20:
        del msglist[0]
    if msg in msglist:
        return
    strtime = time.strftime("!%H:%M:%S", time.localtime())
    if (level >2):
        msg1=strtime+str(msg)
        data = {
            "msgtype": "text",
            "text": {
                "content": msg1
            },
        }

        # 发送请求
        try:
            resp = requests.post(url,
                                 data=json.dumps(data).encode('utf8'),
                                 headers=headers,
                                )
        except:
            time.sleep(1)
            msglist.clear()
    msglist.append(msg)
    print (msg)
