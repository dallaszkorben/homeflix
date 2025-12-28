import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPPersonalSearchGet(EP):

    URL = '/personal/search/get'

    PATH_PAR_PAYLOAD = '/search/get'
    PATH_PAR_URL = '/search/get/thumbnail_id/<thumbnail_id>'

    METHOD = 'GET'

    ATTR_THUMBNAIL_ID = 'thumbnail_id'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, thumbnail_id) -> dict:
        payload = {}

        payload[EPPersonalSearchGet.ATTR_THUMBNAIL_ID] = thumbnail_id

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        thumbnail_id = payload[EPPersonalSearchGet.ATTR_THUMBNAIL_ID]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPPersonalSearchGet.METHOD, EPPersonalSearchGet.URL,
                    EPPersonalSearchGet.ATTR_THUMBNAIL_ID, thumbnail_id,
                )
        )

        output = self.web_gadget.db.get_search(thumbnail_id=thumbnail_id)

        return output_json(output, EP.CODE_OK)
