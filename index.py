from biliup.downloader import download
from biliup.plugins import logger


if __name__ == '__main__':

    logger.info('This is a log info')
    
    download('test', 'https://www.huya.com/21372', suffix='flv')
    