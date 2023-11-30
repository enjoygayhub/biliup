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
from downloader import download, sendDownload


async def main():
    from biliup.handler import event_manager

    event_manager.start()

    nameMapUrl = {k: v['url'] for k, v in config['streamers'].items()}
    urlMapName = { value:key for key, value in nameMapUrl.items() }
    urls = list(urlMapName.keys())
        
    for url in urls:
        # 线程数量是固定的在开始运行的时候创建不会产生变化也不会闲置或者复用线程 所以无需使用线程池
       
        new_thread = threading.Thread(target=sendDownload, args=(urlMapName[url], url,))
        new_thread.start()
        # download(urlMapName[url], url)
    
    runMinute = config.get("runMinute",1)
    logger.info('主进程挂起！')
    time.sleep(runMinute*60)
    logger.info('stop event_manager') 
    event_manager.stop()
    

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
    
   
    logger.info('end main exe')   