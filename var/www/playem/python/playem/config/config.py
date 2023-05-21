import os
import configparser
from pathlib import Path
import logging

from playem.config.property import Property

class Config( Property ):
    HOME = str(Path.home())
    FOLDER = ".playem"
    CONFIG_FILE_NAME = "config.yaml"
    
    DEFAULT_LOG_LEVEL = "DEBUG"
    DEFAULT_LOG_FILE_NAME = "playem.log"

    DEFAULT_WEB_RELATIVE_PATH = "/playem"
    DEFAULT_WEB_ABSOLUTE_PATH = "/var/www/playem"

    DEFAULT_MEDIA_ABSOLUTE_PATH = "/media/pi/01.Movie"

    __instance = None

    def __new__(cls):
        if cls.__instance == None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def getInstance(cls):
        inst = cls.__new__(cls)
        cls.__init__(cls.__instance)
        return inst

    def __init__(self):
        file_full_path = os.path.join(Config.HOME, Config.FOLDER, Config.CONFIG_FILE_NAME)
        path = os.path.join(Config.HOME, Config.FOLDER)
        super().__init__( file_full_path,  path)
        try:
            self.confDict = self.getDict()
        except FileNotFoundError:
            self.confDict = self.buildConfDict()

    def buildConfDict(self):
        confDict = {}
        confDict['log'] = {}
        confDict['log']['level'] = Config.DEFAULT_LOG_LEVEL
        confDict['log']['file-name'] = Config.DEFAULT_LOG_FILE_NAME
        
        confDict['web'] = {}
        confDict['web']['relative-path'] = Config.DEFAULT_WEB_RELATIVE_PATH
        confDict['web']['absolute-path'] = Config.DEFAULT_WEB_ABSOLUTE_PATH

        confDict['media'] = {}
        confDict['media']['absolute-path'] = Config.DEFAULT_MEDIA_ABSOLUTE_PATH

        self.writeDict(confDict)
        return confDict

    def getLogLevel(self):
        return self.confDict['log']['level']

    def getLogFileName(self):
        return self.confDict['log']['file-name']

    def getWebRelativePath(self):
        return self.confDict['web']['relative-path']

    def getWebAbsolutePath(self):
        return self.confDict['web']['absolute-path']

    def getMediaAbsolutePath(self):
        return self.confDict['media']['absolute-path']
