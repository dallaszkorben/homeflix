import os
import logging
from logging.handlers import RotatingFileHandler

from datetime import datetime
import time
import distlib

import json
from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request
from flask_cors import CORS

from playem.card.database import SqlDatabase as DB
from playem.card.card_handle import CardHandle

from playem.config.config import getConfig

from playem.restserver.view_info import InfoView
from playem.restserver.view_collect import CollectView
from playem.restserver.view_translate import TranslateView
from playem.restserver.view_control import ControlView
from playem.restserver.view_personal import PersonalView

class WSPlayem(Flask):

    def __init__(self, import_name):

        super().__init__(import_name)

        self.app = self

        # Fetch Confiuration variables
        self.cg = getConfig()        # defined in config.py
        self.configPath = self.cg["path"]
        logLevel = self.cg["log-level"]
        self.logFileName = self.cg["log-file-name"]
        self.webRelativePath = self.cg["web-relative-path"]
        self.webAbsolutePath = self.cg["web-absolute-path"]
        self.mediaAbsolutePath = self.cg["media-absolute-path"]
        self.mediaRelativePath = self.cg["media-relative-path"]
        self.projectPath = self.cg["project-path"]

        # LOG 
        self.logPath = os.path.join(self.configPath, self.logFileName)
        logging.basicConfig(
            handlers=[RotatingFileHandler(self.logPath, maxBytes=5*1024*1024, backupCount=5)],
            format='%(asctime)s %(levelname)8s - %(message)s' , 
            level = logging.ERROR if logLevel == 'ERROR' else logging.WARNING if logLevel == 'WARNING' else logging.INFO if logLevel == 'INFO' else logging.DEBUG if logLevel == 'DEBUG' else 'CRITICAL' )

        # This will enable CORS for all routes
        CORS(self.app)

        # register the end-points
        InfoView.register(self.app, init_argument=self)
        CollectView.register(self.app, init_argument=self)
        TranslateView.register(self.app, init_argument=self)
        ControlView.register(self.app, init_argument=self)
        PersonalView.register(self.app, init_argument=self)

        self.cardHandle = CardHandle(self)

        # Create database if it is corrupted
        start = time.time()
        self.db=DB(self)
        end = time.time()
        diff = end-start

        records = self.db.get_numbers_of_records_in_card()
        print("Collecting {0} pcs media took {1:.1f} seconds".format(records[0], diff))
        print("The FQDN of the main file: %s" % (__name__))
        print("Web access: http://localhost{0}".format(self.webRelativePath))


    def getThreadControllerStatus(self):
        return self.gradualThreadController.getStatus()

    def unconfigure(self):
        pass
#        self.egLight.unconfigure()

    def __del__(self):
        self.unconfigure()

#    print("The FQDN of the main file: %s" % (__name__))

# because of WSGI
app = WSPlayem(__name__)
