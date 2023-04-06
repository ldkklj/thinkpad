
def getAccount():
    try:
        accountinfo=biance.fetch_balance({'recvWindow': 10000000})
        return accountinfo
    except Exception as e:
        sendMsg(e)
        return False