#!/usr/bin/python3
#coding:utf8
import argparse
import asyncio
import logging.config
import multiprocessing
import time
import re
from biliup.config import config
from biliup import __version__, LOG_CONF
from biliup.common import logger
from downloader import download
from biliup.plugins import general
from biliup import plugins
from biliup.engine.decorators import Plugin

def main():
    Plugin(plugins)
    nameMapUrl = {k: v['url'] for k, v in config['streamers'].items()}
    urlMapName = { value:key for key, value in nameMapUrl.items() }
    urls = list(urlMapName.keys())
    max_pool = config.get("max_process",2)
    duration = config.get("video_duration",60)
    processes = []
    pool_size = 0
    for url in urls:
        plugin = getDownloader(urlMapName[url], url)
        
        has_stream = plugin.check_stream()
        plugin.start()
        if has_stream:
            p = multiprocessing.Process(target=plugin.start)
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
    
def setDownloader(obj):
    return obj.start()

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

if __name__ == '__main__':
   
    logger.info('start main:')
   
    config.load()

    logging.config.dictConfig(LOG_CONF)
    
    main()
    logger.info('end wait')  
    time.sleep(20)
    logger.info('end main exe')   