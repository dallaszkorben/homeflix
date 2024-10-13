import logging
# import subprocess
# import os
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPControlRebuildDbPersonal(EP):

    ID = 'control_rebuild_db_personal'
    URL = '/control/rebuild/db/personal'

    PATH_PAR_PAYLOAD = '/rebuild/db/personal'
    PATH_PAR_URL = '/rebuild/db/personal'

    METHOD = 'POST'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self) -> dict:
        payload = {}
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request {1} {0} {2})".format(
                    remoteAddress, EPControlRebuildDbPersonal.METHOD, EPControlRebuildDbPersonal.URL
                )
        )

        output = {}

        logging.debug("Personal Database Re-build started...")
        print("===========================")
        print("Personal Database Re-build started...")

        start = time.time()
        self.web_gadget.db.recreate_personal_dbs()
        end = time.time()
        diff = end-start

        logging.debug("Personal Database Re-build took {0:.1f} seconds".format(diff))
        print("Personal Database Re-build {0:.1f} seconds".format(diff))
        output["result"] = "SUCCESS"

        return output_json(output, EP.CODE_OK)
