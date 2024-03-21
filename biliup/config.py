import json
from pathlib import Path
# import shutil
from collections import UserDict
# import tomli as tomllib
import yaml
import os

class Config(UserDict):
    def load_cookies(self):
        self.data["user"] = {"cookies": {}}
        with open('cookies.json', encoding='utf-8') as stream:
            s = json.load(stream)
            for i in s["cookie_info"]["cookies"]:
                name = i["name"]
                self.data["user"]["cookies"][name] = i["value"]
            self.data["user"]["access_token"] = s["token_info"]["access_token"]

    def load(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        yamlPath = os.path.join(current_dir,"config.yaml")
        
        if os.path.isfile(yamlPath):
            file = open(yamlPath, 'rb')
        else:
            raise FileNotFoundError('未找到配置文件，请先创建配置文件')
        with file as stream:
            self.data = yaml.load(stream, Loader=yaml.FullLoader)



    # def save(self):
    #     if self.data.get('toml'):
    #         import tomli_w
    #         with open('config.toml', 'rb') as stream:
    #             old_data = tomllib.load(stream)
    #             old_data["lines"] = self.data["lines"]
    #             old_data["threads"] = self.data["threads"]
    #             old_data["streamers"] = self.data["streamers"]
    #         with open('config.toml', 'wb') as stream:
    #             tomli_w.dump(old_data, stream)
    #     else:
    #         import yaml
    #         with open('config.yaml', 'w+', encoding='utf-8') as stream:
    #             old_data = yaml.load(stream, Loader=yaml.FullLoader)
    #             old_data["user"]["cookies"] = self.data["user"]["cookies"]
    #             old_data["user"]["access_token"] = self.data["user"]["access_token"]
    #             old_data["lines"] = self.data["lines"]
    #             old_data["threads"] = self.data["threads"]
    #             old_data["streamers"] = self.data["streamers"]
    #             yaml.dump(old_data, stream, default_flow_style=False, allow_unicode=True)


config = Config()
