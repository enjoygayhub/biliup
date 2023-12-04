import logging
import os
import re
import subprocess
import sys
import time
from typing import Generator, List
from urllib.parse import urlparse

import requests
import stream_gears
from PIL import Image

from biliup.config import config
from biliup.database import DB as db
from biliup.plugins import logger



class DownloadBase:
    def __init__(self, name, url, suffix="flv", opt_args=[]):
       
        self.name = name
        self.url = url
        self.suffix = suffix

        self.downloader = config.get('downloader', 'stream-gears')
        # ffmpeg.exe -i  http://vfile1.grtn.cn/2018/1542/0254/3368/154202543368.ssm/154202543368.m3u8
        # -c copy -bsf:a aac_adtstoasc -movflags +faststart output.mp4
        self.raw_stream_url = None
       
        self.opt_args = opt_args
      
        self.fake_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        }

        self.default_output_args = [
            '-bsf:a', 'aac_adtstoasc',
        ]
        if config.get('segment_time'):
            self.default_output_args += \
                ['-to', f"{config.get('segment_time', '00:50:00')}"]
        else:
            self.default_output_args += \
                ['-fs', f"{config.get('file_size', '2621440000')}"]

    def check_stream(self, is_check=False):
        # is_check 是否是检测可以避免在检测是否可以录制的时候忽略一些耗时的操作
        logger.debug(self.name, is_check)
        raise NotImplementedError()


    # def get_filename(self, is_fmt=False):
        
    #     filename = f'{self.fname}%Y-%m-%dT%H_%M_%S'
    #     filename = get_valid_filename(filename)
    #     if is_fmt:
    #         return time.strftime(filename.encode("unicode-escape").decode()).encode().decode("unicode-escape")
    #     else:
    #         return filename

    def download(self, filename):
        # filename = self.get_filename()
        fmtname = time.strftime(filename.encode("unicode-escape").decode()).encode().decode("unicode-escape")

        parsed_url_path = urlparse(self.raw_stream_url).path
        if self.downloader == 'streamlink':
            if '.flv' in parsed_url_path:  # streamlink无法处理flv,所以回退到ffmpeg
                return self.ffmpeg_download(fmtname)
            else:
                return self.streamlink_download(fmtname)
        elif self.downloader == 'ffmpeg':
            return self.ffmpeg_download(fmtname)

        if not self.suffix in ['flv', 'ts']:
            self.suffix = 'flv' if '.flv' in parsed_url_path else 'ts'
            logger.warning(f'stream-gears 不支持除 flv 和 ts 以外的格式，已按流自动修正为 {self.suffix} 格式')

        
        return stream_gears_download(self.raw_stream_url, self.fake_headers, filename)

    def streamlink_download(self, filename):  # streamlink+ffmpeg混合下载模式，适用于下载hls流
        streamlink_input_args = ['--stream-segment-threads', '3', '--hls-playlist-reload-attempts', '1']
        streamlink_cmd = ['streamlink', *streamlink_input_args, self.raw_stream_url, 'best', '-O']
        ffmpeg_input_args = ['-rw_timeout', '20000000']
        ffmpeg_cmd = ['ffmpeg', '-re', '-i', 'pipe:0', '-y', *ffmpeg_input_args, *self.default_output_args,
                      *self.opt_args, '-c', 'copy', '-f', self.suffix]
        # if config.get('segment_time'):
        #     ffmpeg_cmd += ['-f', 'segment',
        #              f'{filename} part-%03d.{self.suffix}']
        # else:
        #     ffmpeg_cmd += [
        #         f'{filename}.{self.suffix}.part']
        ffmpeg_cmd += [f'{filename}.{self.suffix}.part']
        streamlink_proc = subprocess.Popen(streamlink_cmd, stdout=subprocess.PIPE)
        ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=streamlink_proc.stdout, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
        try:
            with ffmpeg_proc.stdout as stdout:
                for line in iter(stdout.readline, b''):
                    decode_line = line.decode(errors='ignore')
                    print(decode_line, end='', file=sys.stderr)
                    logger.debug(decode_line.rstrip())
            retval = ffmpeg_proc.wait()
            streamlink_proc.terminate()
            streamlink_proc.wait()
        except KeyboardInterrupt:
            if sys.platform != 'win32':
                ffmpeg_proc.communicate(b'q')
            raise
        if retval != 0:
            return False
        return True

    def ffmpeg_download(self, filename):
        default_input_args = ['-headers', ''.join('%s: %s\r\n' % x for x in self.fake_headers.items()), '-rw_timeout',
                              '20000000']
        parsed_url = urlparse(self.raw_stream_url)
        path = parsed_url.path
        if '.m3u8' in path:
            default_input_args += ['-max_reload', '1000']
        args = ['ffmpeg', '-y', *default_input_args,
                '-i', self.raw_stream_url, *self.default_output_args, *self.opt_args,
                '-c', 'copy', '-f', self.suffix]
        # if config.get('segment_time'):
        #     args += ['-f', 'segment',
        #              f'{filename} part-%03d.{self.suffix}']
        # else:
        #     args += [
        #         f'{filename}.{self.suffix}.part']
        args += [f'{filename}.{self.suffix}.part']

        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            with proc.stdout as stdout:
                for line in iter(stdout.readline, b''):  # b'\n'-separated lines
                    decode_line = line.decode(errors='ignore')
                    print(decode_line, end='', file=sys.stderr)
                    logger.debug(decode_line.rstrip())
            retval = proc.wait()
        except KeyboardInterrupt:
            if sys.platform != 'win32':
                proc.communicate(b'q')
            raise
        if retval != 0:
            return False
        return True


    def run(self):
        hasStreamUrl = True
        if not self.raw_stream_url:
            hasStreamUrl = self.check_stream()
        if hasStreamUrl:
            file_name = self.file_name
            # 选择下载器，开始下载
            retval = self.download(file_name)
            # 重名为加后缀
            # newName = f'{file_name}.{self.suffix}'
            # retval = self.rename(newName)
            return retval
        else:
            return False
        
    def start(self):
        
        logger.info(f'开始下载：{self.__class__.__name__} - {self.name}')
        date = time.localtime()

        try:
            ret = self.run()
        except:
            logger.exception('Uncaught exception: download error')
            ret = False
        finally:
            self.close()

        
        resultInfo = {
            'name': self.name,
            'url': self.url,
            'success':ret,
            'flvName':self.file_name
        }
        return resultInfo
    
    @staticmethod
    def rename(file_name):
        try:
            os.rename(file_name + '.part', file_name)
            logger.info(f'更名 {file_name + ".part"} 为 {file_name}')
            return True
        except FileNotFoundError:
            logger.debug(f'文件不存在: {file_name}')
            return False
        except FileExistsError:
            os.rename(file_name + '.part', file_name)
            logger.info(f'更名 {file_name + ".part"} 为 {file_name} 失败, {file_name} 已存在')
            return False

    @property
    def file_name(self):
        
        filename = f'{self.name}%Y-%m-%dT%H_%M_%S'
        filename = get_valid_filename(filename)
        return time.strftime(filename.encode("unicode-escape").decode()).encode().decode("unicode-escape")

    def close(self):
        pass


def stream_gears_download(url, headers, file_name, file_size=None):
    class Segment:
        pass

    segment = Segment()
    segment.size = 8 * 1024 * 1024 * 1024
    if file_size:
        segment.size = file_size
        
    stream_gears.download(
        url,
        headers,
        file_name,
        segment
    )


def get_valid_filename(name):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    # >>> get_valid_filename("john's portrait in 2004.jpg")
    >>> get_valid_filename("{self.fname}%Y-%m-%dT%H_%M_%S")
    '{self.fname}%Y-%m-%dT%H_%M_%S'
    """
    # s = str(name).strip().replace(" ", "_") #因为有些人会在主播名中间加入空格，为了避免和录播完毕自动改名冲突，所以注释掉
    s = re.sub(r"(?u)[^-\w.%{}\[\]【】「」\s]", "", str(name))
    if s in {"", ".", ".."}:
        raise RuntimeError("Could not derive file name from '%s'" % name)
    return s
