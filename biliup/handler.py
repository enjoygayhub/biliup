import copy
import logging
import subprocess
import time
import json

from . import plugins
from .common.tools import NamedLock
from .downloader import download
from .engine import invert_dict, Plugin
from biliup.config import config
from .engine.event import EventManager
from .uploader import upload

DOWNLOAD = 'download'

logger = logging.getLogger('biliup')


def create_event_manager():
    
    nameMapUrl = {k: v['url'] for k, v in config['streamers'].items()}
    urlMapName = { value:key for key, value in nameMapUrl.items() }
    # urls = list(urlMapName.keys())
    pool1_size = config.get('pool1_size', 2)
    
    # 初始化事件管理器
    app = EventManager(config, pool1_size=pool1_size)
    
    # 正在上传的文件 用于同时上传一个url的时候过滤掉正在上传的
    app.context['inverted_index'] = urlMapName
    app.context['streamer_url'] = nameMapUrl
    return app


event_manager = create_event_manager()


@event_manager.register(DOWNLOAD, block='Asynchronous1')
def process(name, url):
   
    # 下载开始
    try:
        stream_info = download(name, url)
        logger.info(stream_info)
    except Exception as e:
        logger.exception(f"下载错误: {name} - {e}")
    finally:
        # 下载结束
        pass


# @event_manager.register('upload', block='Asynchronous2')
# def process_upload(stream_info):
#     url = stream_info['url']
#     url_upload_count = event_manager.context['url_upload_count']
#     # 上传开始
#     try:
#         upload(stream_info)
#     except Exception as e:
#         logger.exception(f"上传错误: {stream_info['name']} - {e}")
#     finally:
#         # 上传结束
#         # 有可能有两个同url的上传线程 保证计数正确
#         with NamedLock(f'upload_count_{url}'):
#             url_upload_count[url] -= 1

#  run subprocess cmd with data
def runProcessors(processors, data):
    for processor in processors:
        if processor.get('run'):
            try:
                process_output = subprocess.check_output(
                    processor['run'], shell=True,
                    input=data,
                    stderr=subprocess.STDOUT, text=True)
                logger.info(process_output.rstrip())
            except subprocess.CalledProcessError as e:
                logger.exception(e.output)
                continue
