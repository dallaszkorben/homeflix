import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPPersonalSearchDelete(EP):

    URL = '/personal/search/delete'

    PATH_PAR_PAYLOAD = '/search/delete'

    METHOD = 'DELETE'

    ATTR_SEARCH_ID = 'search_id'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        search_id = payload[EPPersonalSearchDelete.ATTR_SEARCH_ID]
        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPPersonalSearchDelete.METHOD, EPPersonalSearchDelete.URL,
                    EPPersonalSearchDelete.ATTR_SEARCH_ID, search_id,
                )
        )

        output = self.web_gadget.db.delete_search(search_id=search_id)

        return output_json(output, EP.CODE_OK)
