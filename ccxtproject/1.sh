#!/bin/bash
source="/root/6/ccxtproject"


#判断文件夹是否存在
if [ ! -e $source ]
then
        echo "the source dir doesn't exist."
        exit 1
fi

#获取本地时间，并格式化时间
Date=`date +%Y-%m-%d-%H-%M-%S`

fileName="$Date"_sunlit.tar.gz
#打包文件
tar -zcvf "$fileName" "$source"

echo "backup accomplished."
