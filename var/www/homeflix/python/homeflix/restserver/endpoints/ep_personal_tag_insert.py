import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPPersonalTagInsert(EP):

    URL = '/personal/tag/insert'

    PATH_PAR_PAYLOAD = '/tag/insert'

    METHOD = 'POST'

    ATTR_CARD_ID = 'card_id'
    ATTR_NAME = 'name'
    
    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        card_id = payload[EPPersonalTagInsert.ATTR_CARD_ID]
        name = payload.get(EPPersonalTagInsert.ATTR_NAME, None)
        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6})".format(
                    remoteAddress, EPPersonalTagInsert.METHOD, EPPersonalTagInsert.URL,
                    EPPersonalTagInsert.ATTR_CARD_ID, card_id,
                    EPPersonalTagInsert.ATTR_NAME, name,
                )
        )

        output = self.web_gadget.db.insert_tag(card_id=card_id, name=name)

        return output_json(output, EP.CODE_OK)
