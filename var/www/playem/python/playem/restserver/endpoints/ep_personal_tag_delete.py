import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPPersonalTagDelete(EP):

    URL = '/personal/tag/insert'

    PATH_PAR_PAYLOAD = '/tag/delete'

    METHOD = 'DELETE'

    ATTR_CARD_ID = 'card_id'
    ATTR_NAME = 'name'
    
    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        card_id = payload[EPPersonalTagDelete.ATTR_CARD_ID]
        name = payload.get(EPPersonalTagDelete.ATTR_NAME, None)
        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6})".format(
                    remoteAddress, EPPersonalTagDelete.METHOD, EPPersonalTagDelete.URL,
                    EPPersonalTagDelete.ATTR_CARD_ID, card_id,
                    EPPersonalTagDelete.ATTR_NAME, name,
                )
        )

        output = self.web_gadget.db.delete_tag(card_id=card_id, name=name)

        return output_json(output, EP.CODE_OK)
