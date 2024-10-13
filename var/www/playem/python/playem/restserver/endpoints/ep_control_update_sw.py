import logging
import subprocess
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPControlUpdateSw(EP):

    ID = 'control_update_sw'
    URL = '/control/update/sw'

    PATH_PAR_PAYLOAD = '/update/sw'
    PATH_PAR_URL = '/update/sw'

    METHOD = 'POST'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget
        self.project_path = self.web_gadget.projectPath

    def executeByParameters(self) -> dict:
        payload = {}
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request {1} {0} {2})".format(
                    remoteAddress, EPControlUpdateSw.METHOD, EPControlUpdateSw.URL                    
                )
        )

        output = {}

        logging.debug("Update code started...")
        print("===========================")
        print("Update code started...")

        process = subprocess.run(["cd {0}; git pull --rebase".format(self.project_path)], capture_output=True,text=True, shell=True, check=False)
        if process.returncode == 0:
            logging.debug("Update finished successfully: {0}".format(process.stdout))
            print("Update code finished")
            output["result"] = "SUCCESS"
            output["message"] = process.stdout
            output["command"] = process.args
        else:
            logging.debug("Update failed: {0}. Command: {1}".format(process.stderr, process.args))
            print("Update code failed: {0}. Command: {1}".format(process.stderr, process.args))
            output["result"] = "EXCEPTION"
            output["message"] = process.stderr
            output["command"] = process.args

        return output_json(output, EP.CODE_OK)
