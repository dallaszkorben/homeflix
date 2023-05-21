import os
import yaml

from pathlib import Path
import logging
from builtins import UnicodeDecodeError

class Property(object):
 
    def __init__(self, file_full_path, folder=None):
        self.file_full_path = file_full_path
        self.folder = folder

    def getDict(self):
        with open(self.file_full_path,"r") as file_object:
            data=yaml.load(file_object,Loader=yaml.SafeLoader)
            return data

    def writeDict(self, dataDict):
        with open(self.file_full_path,"w") as file_object:
            yaml.dump(dataDict,file_object)
