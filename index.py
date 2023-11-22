from biliup.downloader import download
from biliup.plugins import logger
from biliup.plugins.huya import huya

if __name__ == '__main__':

    logger.info('This is a log info')
    
    pg =  huya('test', 'https://www.huya.com/21372', suffix='flv')
    pg.start()