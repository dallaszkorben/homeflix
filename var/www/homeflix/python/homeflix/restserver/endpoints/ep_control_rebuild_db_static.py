import logging
import time
import os

from homeflix.card.database import SqlDatabase as DB
from homeflix.cache.cache_warming import start_warming
from homeflix.config.config import getConfig

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

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

        card_records = self.web_gadget.db.get_numbers_of_records_in_card()
        media_records = self.web_gadget.db.get_numbers_of_media_in_card()
        logging.debug("Collecting {0} pcs cards, including {1} pcs media took {2:.1f} seconds".format(card_records[0], media_records[0], diff))
        print("Collecting {0} pcs cards, including {1} pcs media took {2:.1f} seconds".format(card_records[0], media_records[0], diff))
        output["result"] = "SUCCESS"

        # Start cache warming in background thread.
        # This pre-populates the file cache for all cacheable queries
        # so the first user visit after rebuild is instant.
        config = getConfig()
        card_menu_path = os.path.join(config["path"], config["card-menu-file-name"])
        start_warming(self.web_gadget.db, card_menu_path)

        return output_json(output, EP.CODE_OK)
