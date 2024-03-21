#!/usr/bin/python3
#coding:utf8
import argparse
import asyncio
import logging.config
import multiprocessing
import os
import time
import re

import requests
from biliup.config import config
from biliup import __version__, LOG_CONF
from biliup.common import logger
from downloader import download
from biliup.plugins import general
from biliup import plugins
from biliup.engine.decorators import Plugin
from biliup.transformat import transform_parts_to_mp4

def main():
    Plugin(plugins)
    max_pool = config.get("max_process",3)
    duration = config.get("video_duration",200)
    run_duration = config.get("run_duration",200)
    
    # 读取配置文件
    nameMapUrl = config['streamers']
    loopTimes = run_duration//duration
    
    for _ in range(loopTimes):
        onlineRooms = getOnlineRooms(max_pool)
        nameMapUrl = onlineRooms if onlineRooms else nameMapUrl
        downloadUrls(nameMapUrl,max_pool,duration)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    flv_dir = os.path.join(current_dir, '../')
    transform_parts_to_mp4(flv_dir)
    
    
def downloadUrls(nameMapUrl,max_pool,duration):
    
    processes = []
    pool_size = 0
    for name, url in nameMapUrl.items():
        plugin = getDownloader(name, url)
        
        has_stream = plugin.check_stream()
        
        if has_stream:
            p = multiprocessing.Process(target=download,args=(name, url,))
            p.start()
            processes.append(p)
            pool_size += 1
        if pool_size >= max_pool:
            logger.info('主进程挂起！等在下载指定时间后结束')
            time.sleep(duration)
            logger.info('终止子进程')
            for p in processes:
                p.terminate()  # 终止子进程
            pool_size = 0
            processes = [] 
    #  收尾
    if pool_size:
        logger.info('等在下载指定时间后结束')
        time.sleep(duration)
        logger.info('终止子进程')
        for p in processes:
            p.terminate()  # 终止子进程

def getDownloader(fname, url):
    # 根据传入的文件名 fname 和 URL url 调用 general.__plugin__ 方法获取通用插件对象 pg 。
    logger.info("choose plugin!")
    pg = general.__plugin__(fname, url)
    
    # 然后遍历 Plugin.download_plugins 中的所有插件，若存在一个插件的 VALID_URL_BASE 正则表达式匹配 URL url ，则实例化这个插件并将其赋值给 pg
    for plugin in Plugin.download_plugins:
        if re.match(plugin.VALID_URL_BASE, url):
            pg = plugin(fname, url)
            break
    return pg
# def split_array(arr):
#     return [arr[i:i+3] for i in range(0, len(arr), 3)]

def getOnlineRooms(max_pool):
    fake_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
        }
    target ='https://live.huya.com/liveHttpUI/getTmpLiveList?iTmpId=116&iPageNo=1&iPageSize=20&iLibId=122&iGid=1663'
    try:
        res = requests.get(target, timeout=5,headers=fake_headers)
        res.close()
        resData = res.json()
        topItems = resData['vList'][:max_pool]
        nameUrls = {item['sNick']: f"https://www.huya.com/{item['lProfileRoom']}" for item in topItems}
        
    except:
        logger.warning(f"获取错误")
        return None
    
    return nameUrls

if __name__ == '__main__':
   
    logger.info('start main:')
   
    config.load()

    logging.config.dictConfig(LOG_CONF)
    
    main()
    logger.info('end wait')  
    time.sleep(20)
    logger.info('end main exe')   