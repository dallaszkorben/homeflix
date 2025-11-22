import os
import configparser
from pathlib import Path
import logging

from homeflix.property.property import Property

class Config( Property ):
    HOME = str(Path.home())
    FOLDER = ".homeflix"
    CONFIG_FILE_NAME = "config.yaml"

    DEFAULT_LOG_LEVEL = "DEBUG"
    DEFAULT_LOG_FILE_NAME = "homeflix.log"

    DEFAULT_WEB_RELATIVE_PATH = "/homeflix"
    DEFAULT_WEB_ABSOLUTE_PATH = "/var/www/homeflix"

    DEFAULT_MEDIA_ABSOLUTE_PATH = "/var/www/homeflix/MEDIA"
    DEFAULT_MEDIA_RELATIVE_PATH = "MEDIA"

    DEFAULT_CARD_DB_NAME = "homeflix.db"
    DEFAULT_CARD_MENU_FILE_NAME = "card_menu.yaml"

    DEFAULT_PROJECT_PATH = "/home/pi/Projects/python/homeflix"

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
        confDict['card']['menu-file-name'] = Config.DEFAULT_CARD_MENU_FILE_NAME

        confDict['project'] = {}
        confDict['project']['path'] = Config.DEFAULT_PROJECT_PATH

        self.writeDict(confDict)
        return confDict

    def getConfigPath(self):
        return self.config_path

    def getLogLevel(self):
        if 'log' not in self.confDict:
            self.confDict['log'] = {}
        if 'level' not in self.confDict['log']:
            self.confDict['log']['level'] = Config.DEFAULT_LOG_LEVEL
            self.writeDict(self.confDict)
        return self.confDict['log']['level']

    def getLogFileName(self):
        if 'log' not in self.confDict:
            self.confDict['log'] = {}
        if 'file-name' not in self.confDict['log']:
            self.confDict['log']['file-name'] = Config.DEFAULT_LOG_FILE_NAME
            self.writeDict(self.confDict)
        return self.confDict['log']['file-name']

    def getWebRelativePath(self):
        if 'web' not in self.confDict:
            self.confDict['web'] = {}
        if 'relative-path' not in self.confDict['web']:
            self.confDict['web']['relative-path'] = Config.DEFAULT_WEB_RELATIVE_PATH
            self.writeDict(self.confDict)
        return self.confDict['web']['relative-path']

    def getWebAbsolutePath(self):
        if 'web' not in self.confDict:
            self.confDict['web'] = {}
        if 'absolute-path' not in self.confDict['web']:
            self.confDict['web']['absolute-path'] = Config.DEFAULT_WEB_ABSOLUTE_PATH
            self.writeDict(self.confDict)
        return self.confDict['web']['absolute-path']

    def getMediaAbsolutePath(self):
        if 'media' not in self.confDict:
            self.confDict['media'] = {}
        if 'absolute-path' not in self.confDict['media']:
            self.confDict['media']['absolute-path'] = Config.DEFAULT_MEDIA_ABSOLUTE_PATH
            self.writeDict(self.confDict)
        return self.confDict['media']['absolute-path']

    def getMediaRelativePath(self):
        if 'media' not in self.confDict:
            self.confDict['media'] = {}
        if 'relative-path' not in self.confDict['media']:
            self.confDict['media']['relative-path'] = Config.DEFAULT_MEDIA_RELATIVE_PATH
            self.writeDict(self.confDict)
        return self.confDict['media']['relative-path']

    def getCardDBName(self):
        if 'card' not in self.confDict:
            self.confDict['card'] = {}
        if 'db-name' not in self.confDict['card']:
            self.confDict['card']['db-name'] = Config.DEFAULT_CARD_DB_NAME
            self.writeDict(self.confDict)
        return self.confDict['card']['db-name']

    def getCardMenuFileName(self):
        if 'card' not in self.confDict:
            self.confDict['card'] = {}
        if 'menu-file-name' not in self.confDict['card']:
            self.confDict['card']['menu-file-name'] = Config.DEFAULT_CARD_MENU_FILE_NAME
            self.writeDict(self.confDict)
        return self.confDict['card']['menu-file-name']

    def getProjectPath(self):
        if 'project' not in self.confDict:
            self.confDict['project'] = {}
        if 'path' not in self.confDict['project']:
            self.confDict['project']['path'] = Config.DEFAULT_PROJECT_PATH
            self.writeDict(self.confDict)
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
    config["card-menu-file-name"] = cb.getCardMenuFileName()

    config["project-path"] = cb.getProjectPath()

    return config
