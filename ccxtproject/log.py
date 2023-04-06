import logging
import time
import ichat
def createlogfile():
    strtime=time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
    logging.basicConfig(level=logging.warning,#控制台打印的日志级别
                        filename=strtime+str(".log"),
                        filemode='a',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                        #a是追加模式，默认如果不写的话，就是追加模式
                        format=
                        '%(asctime)s -: %(message)s'
                        #日志格式
                        )