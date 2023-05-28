import os
import logging
from logging.handlers import RotatingFileHandler

#from dateutil import parser

from datetime import datetime
import time

import distlib

import json
from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request
from flask_cors import CORS

from playem.config.config import getConfig
#from greenwall.config.ini_location import IniLocation

#from greenwall.controlbox.controlbox import Controlbox
#from greenwall.lamp.lamp import Lamp
#from greenwall.pump.pump import Pump
#from greenwall.cam.cam import Cam
#from greenwall.sensor.sensor import Sensor


from playem.restserver.view_info import InfoView
#from greenwall.restserver.view_sensor import SensorView
#from greenwall.restserver.view_cam import CamView
#from greenwall.restserver.view_lamp import LampView
#from greenwall.restserver.view_pump import PumpView
#
#from greenwall.utilities.report_sensor import ReportSensor
#
#from greenwall.utilities.register_sensor import RegisterSensor
#from greenwall.utilities.register_lamp import RegisterLamp
#from greenwall.utilities.register_pump import RegisterPump
#from greenwall.utilities.register_cam import RegisterCam

class WSPlayem(Flask):

    def __init__(self, import_name):

        super().__init__(import_name)

        self.app = self

        # Fetch Confiuration variables
        cg = getConfig()        # defined in config.py
        self.configPath = cg["path"]
        logLevel = cg["log-level"]
        self.logFileName = cg["log-file-name"]
        self.webRelativePath = cg["web-relative-path"]
        self.webAbsolutePath = cg["web-absolute-path"]
        self.mediaAbsolutePath = cg["media-absolute-path"]

        # LOG 
        logPath = os.path.join(self.configPath, logFileName)
        logging.basicConfig(
            handlers=[RotatingFileHandler(self.logPath, maxBytes=5*1024*1024, backupCount=5)],
            format='%(asctime)s %(levelname)8s - %(message)s' , 
            level = logging.ERROR if logLevel == 'ERROR' else logging.WARNING if logLevel == 'WARNING' else logging.INFO if logLevel == 'INFO' else logging.DEBUG if logLevel == 'DEBUG' else 'CRITICAL' )

        # This will enable CORS for all routes
        CORS(self.app)

        # register the end-points
        InfoView.register(self.app, init_argument=self)

#        SensorView.register(self.app, init_argument=self)
#        CamView.register(self.app, init_argument=self)
#        LampView.register(self.app, init_argument=self)
#        PumpView.register(self.app, init_argument=self)

        mediaDict = self.collectCardsFromFileSystem(self.mediaAbsolutePath)

        print("The FQDN of the main file: %s" % (__name__))
        print("Web access: http://localhost{0}".format(webRelativePath))

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
