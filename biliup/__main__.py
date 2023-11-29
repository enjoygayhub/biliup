#!/usr/bin/python3
#coding:utf8
import argparse
import asyncio
import logging.config
import platform
import shutil
import threading
import time
import biliup.common.reload
from biliup.config import config
from biliup.database import DB as db
from biliup import __version__, LOG_CONF
from biliup.common.Daemon import Daemon
from biliup import plugins
from biliup.common import logger
from biliup.engine import invert_dict, Plugin
from downloader import download


async def main():
    # from biliup.handler import event_manager
    # 初始化数据库
    # db.init()
    
    # event_manager.start()
    nameMapUrl = {k: v['url'] for k, v in config['streamers'].items()}
    urlMapName = { value:key for key, value in nameMapUrl.items() }
    urls = list(urlMapName.keys())
        
    for url in urls:
        # 线程数量是固定的在开始运行的时候创建不会产生变化也不会闲置或者复用线程 所以无需使用线程池
        # 这里也无需使用异步方法 一个线程一个检测 异步方法让渡控制权没用
        # new_thread = threading.Thread(target=check_url, args=(checkerPlugins[plugin],))
        # new_thread.start()
        download(urlMapName[url], url)
    


if __name__ == '__main__':
    
    # daemon = Daemon('watch_process.pid', lambda: main())
    parser = argparse.ArgumentParser(description='Stream download')
    parser.add_argument('--version', action='version', version=f"v{__version__}")
    parser.add_argument('--configPath', type=argparse.FileType(mode='rb'),
                        help='Location of the configuration file (default "./config.yaml")')

    args = parser.parse_args()
   
    config.load(args.configPath)

    logging.config.dictConfig(LOG_CONF)
    
    logger.info('start main:')
    
    asyncio.run(main()) 
    # args.func()
    
    time.sleep(10*1000)   