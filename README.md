
**文档地址**：<https://biliup.github.io/biliup>


## Docker使用 🔨
### 方式一 拉取镜像
 > 请注意替换 /host/path 为宿主机下载目录
* 从自定义的配置文件启动
```bash
# 在下载目录创建配置文件
vim /host/path/config.toml
# 启动biliup的docker容器
docker run -P --name biliup -v /host/path:/opt -d ghcr.io/biliup/caution:master
```
* 从自定义的配置文件启动，并启动Web-UI
```bash
# 在下载目录创建配置文件
vim /host/path/config.toml
# 启动biliup的docker容器，并启用用户验证。请注意替换 yourpassword 为你的密码。
docker run -P --name biliup -v /host/path:/opt -p 19159:19159 -d --restart always ghcr.io/biliup/caution:latest --http --password yourpassword
```
 > Web-UI 默认用户名为 biliup。
* 从默认配置文件启动，并启动Web-UI
```bash
docker run -P --name biliup -v /host/path:/opt -p 19159:19159 -d --restart always ghcr.io/biliup/caution:latest --http --password yourpassword
```
### 方式二 手动构建镜像
```bash
# 进入biliup目录
cd biliup
# 构建镜像
sudo docker build . -t biliup
# 启动镜像
sudo docker run -P -d biliup
```
### 进入容器 📦
1. 查看容器列表，找到你要进入的容器的imageId
```bash
sudo docker ps
```
2. 进入容器
```bash
sudo docker exec -it imageId /bin/bash
```


## 从源码运行biliup
* 下载源码: `git clone https://github.com/ForgQi/bilibiliupload.git`
* 安装: `pip3 install -e .`
* 启动: `python3 -m biliup`
* 构建:
  ```shell
  $ npm install
  $ npm run build
  $ python3 -m build
  ```




### 下载
```python
from biliup.downloader import download

download('文件名', 'https://www.panda.tv/1150595', suffix='flv')
```


## 使用建议

## 自定义插件
下载整合了ykdl、youtube-dl、streamlink，不支持或者支持的不够好的网站可自行拓展。
下载和上传模块插件化，如果有上传或下载目前不支持平台的需求便于拓展。

下载基类在`engine/plugins/base_adapter.py`中，拓展其他网站，需要继承下载模块的基类，加装饰器`@Plugin.download`。

拓展上传平台，继承`engine/plugins/upload/__init__.py`文件中上传基类，加装饰器`@Plugin.upload`。

实现了一套基于装饰器的事件驱动框架。增加其他功能监听对应事件即可，比如下载后转码：
```python
# e.p.给函数注册事件
# 如果操作耗时请指定block=True, 否则会卡住事件循环
@event_manager.register("download_finish", block=True)
def transcoding(data):
    pass



