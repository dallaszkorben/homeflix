import os
import configparser
from pathlib import Path
import logging

from playem.property.property import Property

class Config( Property ):
    HOME = str(Path.home())
    FOLDER = ".playem"
    CONFIG_FILE_NAME = "config.yaml"
    
    DEFAULT_LOG_LEVEL = "DEBUG"
    DEFAULT_LOG_FILE_NAME = "playem.log"

    DEFAULT_WEB_RELATIVE_PATH = "/playem"
    DEFAULT_WEB_ABSOLUTE_PATH = "/var/www/playem"

    DEFAULT_MEDIA_ABSOLUTE_PATH = "/var/www/playem/MEDIA"
    DEFAULT_MEDIA_RELATIVE_PATH = "MEDIA"

    DEFAULT_CARD_DB_NAME = "playem.db"

    DEFAULT_PROJECT_PATH = "/home/pi/Projects/python/playem"

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
        self.config_path = os.path.join(Config.HOME, Config.FOLDER)
        file_full_path = os.path.join(self.config_path, Config.CONFIG_FILE_NAME)
        super().__init__( file_full_path)
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
        confDict['media']['relative-path'] = Config.DEFAULT_MEDIA_RELATIVE_PATH

        confDict['card'] = {}
        confDict['card']['db-name'] = Config.DEFAULT_CARD_DB_NAME

        confDict['project'] = {}
        confDict['project']['path'] = Config.DEFAULT_PROJECT_PATH

        self.writeDict(confDict)
        return confDict

    def getConfigPath(self):
        return self.config_path

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

    def getMediaRelativePath(self):
        return self.confDict['media']['relative-path']

    def getCardDBName(self):
        return self.confDict['card']['db-name']

    def getProjectPath(self):
        return self.confDict['project']['path']

def getConfig():
    cb = Config.getInstance()
    config = {}

    config["path"] = cb.getConfigPath()

    config["log-level"] = cb.getLogLevel()
    config["log-file-name"] = cb.getLogFileName()
        
    config["web-relative-path"] = cb.getWebRelativePath()
    config["web-absolute-path"] = cb.getWebAbsolutePath()

    config["media-absolute-path"] = cb.getMediaAbsolutePath()
    config["media-relative-path"] = cb.getMediaRelativePath()

    config["card-db-name"] = cb.getCardDBName()

    config["project-path"] = cb.getProjectPath()

    return config
