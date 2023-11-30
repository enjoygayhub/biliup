import logging
import re
import threading
import time
from urllib.error import HTTPError
# from .common.tools import NamedLock
from biliup.engine.decorators import Plugin
from biliup.engine.download import DownloadBase
from biliup.engine.event import Event
from biliup.plugins import general
# from biliup.config import config
from biliup.common import logger
from biliup import plugins


check_flag = threading.Event()
Plugin(plugins)

def download(fname, url, **kwargs):
    # 根据传入的文件名 fname 和 URL url 调用 general.__plugin__ 方法获取通用插件对象 pg 。
    logger.info("choose plugin!")
    pg = general.__plugin__(fname, url)
    
    # 然后遍历 Plugin.download_plugins 中的所有插件，若存在一个插件的 VALID_URL_BASE 正则表达式匹配 URL url ，则实例化这个插件并将其赋值给 pg
    for plugin in Plugin.download_plugins:
        if re.match(plugin.VALID_URL_BASE, url):
            pg = plugin(fname, url)
            for k in pg.__dict__: # 将插件中同名成员变量替换为关键字参数 kwargs 中的对应值
                if kwargs.get(k):
                    pg.__dict__[k] = kwargs.get(k)
            break
    # pg.check_stream(True)
    return pg.start()



# def check_url(checker):
#     from .handler import event_manager
#     # 单主播检测延迟
#     checker_sleep = config.get('checker_sleep', 10)
#     # 平台检测延迟
#     event_loop_interval = config.get('event_loop_interval', 30)
#     context = event_manager.context
#     class_reference = type(checker('', ''))
   
#     try:
#         # 待检测url
#         check_urls = []
#         # 过滤url
#         for url in checker.url_list:
#             # 同一主播多个url
#             # 多个url只能同时下载一个
#             is_download = False
#             streamer_urls = context['streamers'][context['inverted_index'][url]]['url']
#             for streamer_url in streamer_urls:
#                 if context['url_status'][streamer_url] == 1:
#                     logger.debug(f'{url}-{streamer_url}-正在下载中，跳过检测')
#                     is_download = True
#                     break
#             if is_download:
#                 continue

#             send_upload_event({'name': context['inverted_index'][url], 'url': url})
#             check_urls.append(url)

#         for (index, url) in enumerate(check_urls):
#                 # 某个检测异常略过不应影响其他检测
#                 try:
#                     if index > 0:
#                         logger.debug('歇息会')
#                         time.sleep(checker_sleep)

#                     if checker(context['inverted_index'][url], url).check_stream(True):
#                         send_download_event(context['inverted_index'][url], url)
#                 except HTTPError as e:
#                     logger.error(f'{checker.__module__} {e.url} => {e}')
#                 except IOError:
#                     logger.exception("IOError")
#                 except:
#                     logger.exception("Uncaught exception:")

#     except:
#         # 除了单个检测异常 其他异常会影响整体 直接略过本次 等待下次整体检测
#         logger.exception("Uncaught exception:")

def sendDownload(name,url):
    from biliup.handler import event_manager, DOWNLOAD
    event_manager.send_event(Event(DOWNLOAD, args=(name, url,)))


# def send_download_event(name, url):
#     # 永远不可能对同一个url同时发送两次下载事件
#     from .handler import event_manager, DOWNLOAD
#     content = event_manager.context
#     # 需要等待上传文件列表检索完成后才可以开始下次下载
#     with NamedLock(f'upload_file_list_{name}'):
#         for streamer_url in content['streamers'][content['inverted_index'][url]]['url']:
#             if content['url_status'][streamer_url] == 1:
#                 return False
#         content['url_status'][url] = 1
#         event_manager.send_event(Event(DOWNLOAD, args=(name, url,)))
#     return True


# def send_upload_event(stream_info):
#     # 可能对同一个url同时发送两次上传事件
#     with NamedLock(f"upload_count_{stream_info['url']}"):
#         from .handler import event_manager, UPLOAD
#         # += 不是原子操作
#         event_manager.context['url_upload_count'][stream_info['url']] += 1
#         event_manager.send_event(Event(UPLOAD, (stream_info,)))
