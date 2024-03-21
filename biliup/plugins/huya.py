import base64
import hashlib
import json
import random
import time
from urllib.parse import parse_qs, unquote

import requests

from biliup.config import config
from biliup.plugins.Danmaku import DanmakuClient
from ..engine.decorators import Plugin
from ..engine.download import DownloadBase
from ..plugins import match1, logger


@Plugin.download(regexp=r'(?:https?://)?(?:(?:www|m)\.)?huya\.com')
class Huya(DownloadBase):
    def __init__(self, fname, url, suffix='flv'):
        super().__init__(fname, url, suffix)
        
        self.fake_headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'

    def check_stream(self, is_check=False):
        
        try:
            room_id = self.url.split('huya.com/')[1].split('/')[0].split('?')[0]
            if not room_id:
                raise
        except:
            logger.warning(f"{Huya.__name__}: {self.url}: 直播间地址错误")
            return False
        try:
            res = requests.get(f'https://m.huya.com/{room_id}', timeout=5, headers=self.fake_headers)
            res.close()
        except:
            logger.warning(f"{Huya.__name__}: {self.url}: 获取错误，本次跳过")
            return False

        if '"exceptionType":0' in res.text:
            logger.warning(f"{Huya.__name__}: {self.url}: 直播间地址错误")
            return False

        live_info = json.loads(res.text.split('"tLiveInfo":')[1].split(',"_classname":"LiveRoom.LiveInfo"}')[0] + '}')
        if '"eLiveStatus":2' not in res.text:
            logger.warning(f"{Huya.__name__}: {self.url}: 没开播,不下载")
            # 没开播
            return False
        
        if live_info:
            if live_info["iLiveSourceType"] == 10:
                logger.warning(f"{self.url}: 没视频流,不下载")
                return False
            try:
                # 最大录制码率
                huya_max_ratio = config.get('huya_max_ratio', 8000)
                # 码率信息
                ratio_items = live_info['tLiveStreamInfo']['vBitRateInfo']['value']
                #[
                # {'sDisplayName': '蓝光8M', 'iBitRate': 0, 'iCodecType': 0, 'iCompatibleFlag': 0, 'iHEVCBitRate': -1, '_classname': 'LiveRoom.LiveBitRateInfo'},
                # {'sDisplayName': '蓝光4M', 'iBitRate': 4000, 'iCodecType': 0, 'iCompatibleFlag': 0, 'iHEVCBitRate': 4000, '_classname': 'LiveRoom.LiveBitRateInfo'}, 
                # {'sDisplayName': '超清', 'iBitRate': 2000, 'iCodecType': 0, 'iCompatibleFlag': 0, 'iHEVCBitRate': 2000, '_classname': 'LiveRoom.LiveBitRateInfo'},
                # {'sDisplayName': '流畅', 'iBitRate': 500, 'iCodecType': 0, 'iCompatibleFlag': 0, 'iHEVCBitRate': 500, '_classname': 'LiveRoom.LiveBitRateInfo'}
                # ]
                # 最大码率(不含hdr) 一般是蓝光8M 值为8000
                max_ratio = live_info['iBitRate']
                # 录制码率 设为0 代表使用最大
                record_ratio = 0
                # 如果当前存在最大的码率超过8000，则设为小于等于8000的最大值
                if(max_ratio > huya_max_ratio):
                    record_ratio = 2000 # 超清保底
                    for item in ratio_items:
                        iBitRate = item["iBitRate"]
                        if iBitRate <= huya_max_ratio:
                            record_ratio = max(iBitRate , record_ratio)
            

                # 自选cdn
                huya_cdn = config.get('huyacdn', 'AL')
                # 流信息
                stream_items = live_info['tLiveStreamInfo']['vStreamInfo']['value']
                # AL（阿里云）, HW（华为云）, TX（腾讯云）, WS（网宿）, HS（火山引擎）, AL13（阿里云）, HW16（华为云）
                # 自选的流
                stream_selected = stream_items[0]
                for stream_item in stream_items:
                    if stream_item['sCdnType'] == huya_cdn:
                        stream_selected = stream_item
                        break
                if stream_selected["sFlvUrl"].endswith("huyalive"):
                        stream_selected = stream_items[1]

                sFlvUrlSuffix, sStreamName, sFlvAntiCode = stream_selected['sFlvUrlSuffix'], stream_selected['sStreamName'], stream_selected['sFlvAntiCode']
                query = self.make_query(sStreamName, sFlvAntiCode)
                self.raw_stream_url = f'{stream_selected["sFlvUrl"]}/{sStreamName}.{sFlvUrlSuffix}?{query}'
                return True
            except Exception as e:
                logger.error(e)
                logger.warning(f"{Huya.__name__}: {self.url}: 解析错误")

        return False


    def close(self):
        pass
    
    def make_query(self, sStreamName, sFlvAntiCode):
        url_query = parse_qs(sFlvAntiCode)
        platform_id = 100
        uid = random.randint(12340000, 12349999)
        convert_uid = (uid << 8 | uid >> (32 - 8)) & 0xFFFFFFFF
        ws_time = url_query['wsTime'][0]
        seq_id = uid + int(time.time() * 1000)
        ws_secret_prefix = base64.b64decode(unquote(url_query['fm'][0]).encode()).decode().split('_')[0]
        ws_secret_hash = hashlib.md5(f"{seq_id}|{url_query['ctype'][0]}|{platform_id}".encode()).hexdigest()
        ws_secret = hashlib.md5(f'{ws_secret_prefix}_{convert_uid}_{sStreamName}_{ws_secret_hash}_{ws_time}'.encode()).hexdigest()
        # &codec=av1
        # &codec=264
        # &codec=265
        # dMod: wcs-25 浏览器解码信息
        # sdkPcdn: 1_1 第一个1连接次数 第二个1是因为什么连接
        # t: 100 平台信息 100 web
        # sv: 2401090219 版本
        # sdk_sid:  _sessionId sdkInRoomTs 当前毫秒时间
        return f"wsSecret={ws_secret}&wsTime={ws_time}&seqid={seq_id}&ctype={url_query['ctype'][0]}&ver=1&fs={url_query['fs'][0]}&u={convert_uid}&t={platform_id}&sv=2401090219&sdk_sid={int(time.time() * 1000)}&codec=264"