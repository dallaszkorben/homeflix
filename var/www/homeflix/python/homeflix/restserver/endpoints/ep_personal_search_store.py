import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPPersonalSearchStore(EP):

    URL = '/personal/search/store'

    PATH_PAR_PAYLOAD = '/search/store'

    METHOD = 'POST'

    ATTR_THUMBNAIL_ID = 'thumbnail_id'
    ATTR_THUMBNAIL_DICT = 'dynamic_hard_coded'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        thumbnail_id = payload[EPPersonalSearchStore.ATTR_THUMBNAIL_ID]
        thumbnail_dict = payload.get(EPPersonalSearchStore.ATTR_THUMBNAIL_DICT, {})

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6})".format(
                    remoteAddress, EPPersonalSearchStore.METHOD, EPPersonalSearchStore.URL,
                    EPPersonalSearchStore.ATTR_THUMBNAIL_ID, thumbnail_id,
                    EPPersonalSearchStore.ATTR_THUMBNAIL_DICT, thumbnail_dict,
                )
        )

        output = self.web_gadget.db.store_search(thumbnail_id=thumbnail_id, thumbnail_dict=thumbnail_dict)

        return output_json(output, EP.CODE_OK)
