import os
import yaml

from pathlib import Path
import logging
from builtins import UnicodeDecodeError

class Property(object):

    def __init__(self, file_full_path):
        self.file_full_path = file_full_path

    # # I need this to preserve the behavior of python to understand "no" as boolean in the value, but I want to treat the "no" key as normal string
    # def bool_representer(self, dumper, data):
    #     if data == "no":
    #         return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    #     return dumper.represent_scalar('tag:yaml.org,2002:bool', data)

    def getDict(self):
        # yaml.SafeDumper.add_representer(str, self.bool_representer)
        with open(self.file_full_path,"r", encoding="utf-8") as file_object:
            data=yaml.load(file_object, Loader=yaml.SafeLoader)
            #data=yaml.safe_load(file_object)
            return data

    def writeDict(self, dataDict):
        os.makedirs(os.path.dirname(self.file_full_path), exist_ok=True)
        with open(self.file_full_path,"w", encoding="utf-8") as file_object:
            yaml.dump(dataDict, file_object)
