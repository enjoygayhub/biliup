import functools
import importlib
import pkgutil
import re

# 函数的作用是筛选出与正则表达式 pattern 匹配的字符串列表 urls 中的元素，并按照逆序排列。
def suit_url(pattern, urls):
    sorted_url = []
    for i in range(len(urls) - 1, -1, -1):
        if re.match(pattern, urls[i]):
            sorted_url.append(urls[i])
            urls.remove(urls[i])
    return sorted_url


class Plugin:
    download_plugins = []
    upload_plugins = {}

    def __init__(self, pkg):
        self.load_plugins(pkg)

    # download 负责装饰并添加下载插件，接收一个正则表达式参数 regexp ，将该正则表达式的匹配结果作为 VALID_URL_BASE 属性保存到装饰后的类中，
    @staticmethod
    def download(regexp):
        def decorator(cls):
            @functools.wraps(cls)
            def wrapper(*args, **kw):
                return cls(*args, **kw)
            wrapper.VALID_URL_BASE = regexp
            Plugin.download_plugins.append(wrapper)  # 将该类添加到 download_plugins 列表中
            return wrapper
        return decorator
    
   
    @staticmethod
    def upload(platform):
        def decorator(cls):
            Plugin.upload_plugins[platform] = cls
            return cls
        return decorator
    
    # 接收一组URL urls 并尝试将它们按插件排序。
    # 具体来说，遍历 download_plugins 列表中的每一个插件，找到能够匹配当前 urls 列表中URL的插件，
    # 将匹配的URL保存到 checker_plugins 字典中，键为插件名，值为插件类对象。
    # 如果发现某个插件没有URL可匹配，则跳过下一个插件；如果所有的URL都被匹配，则结束迭代。
    # 如果还有剩余未匹配的URL，则默认交给 general 插件处理。
    @classmethod
    def sorted_checker(cls, urls):
        from ..plugins import general
        curls = urls.copy()
        checker_plugins = {}
        for plugin in cls.download_plugins:
            url_list = suit_url(plugin.VALID_URL_BASE, curls)
            if not url_list:
                continue
            else:
                plugin.url_list = url_list
                checker_plugins[plugin.__name__] = plugin
            if not curls:
                return checker_plugins
        general.__plugin__.url_list = curls
        checker_plugins[general.__plugin__.__name__] = general.__plugin__
        return checker_plugins

    def load_plugins(self, pkg):
        """Attempt to load plugins from the path specified.
        engine.plugins.__path__[0]: full path to a directory where to look for plugins
        """

        plugins = []

        for loader, name, ispkg in pkgutil.iter_modules([pkg.__path__[0]]):
            # set the full plugin module name
            module_name = f"{pkg.__name__}.{name}"
            module = importlib.import_module(module_name)
            if ispkg:
                self.load_plugins(module)
                continue
            if module in plugins:
                continue
            plugins.append(module)
        return plugins
