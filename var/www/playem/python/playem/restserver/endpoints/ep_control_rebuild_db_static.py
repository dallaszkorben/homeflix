import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPControlRebuildDbStatic(EP):

    ID = 'control_rebuild_db_static'
    URL = '/control/rebuild/db/static'

    PATH_PAR_PAYLOAD = '/rebuild/db/static'
    PATH_PAR_URL = '/rebuild/db/static'

    METHOD = 'POST'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self) -> dict:
        payload = {}
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request {1} {0} {2})".format(
                    remoteAddress, EPControlRebuildDbStatic.METHOD, EPControlRebuildDbStatic.URL
                )
        )

        output = {}

        logging.debug("Static Database Re-build started...")
        print("===========================")
        print("Static Database Re-build started...")

        self.web_gadget.db.drop_static_tables()
        start = time.time()
        self.web_gadget.db=DB(self.web_gadget)
        end = time.time()
        diff = end-start

        records = self.web_gadget.db.get_numbers_of_records_in_card()
        logging.debug("Collecting {0} pcs media took {1:.1f} seconds".format(records[0], diff))
        print("Collecting {0} pcs media took {1:.1f} seconds".format(records[0], diff))
        output["result"] = "SUCCESS"

        return output_json(output, EP.CODE_OK)
