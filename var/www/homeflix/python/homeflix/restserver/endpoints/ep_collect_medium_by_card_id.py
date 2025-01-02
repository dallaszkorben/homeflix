import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectMediumByCardId(EP):

    ID = 'collect_medium'
    URL = '/collect/medium'

#    PATH_PAR_PAYLOAD = '/standalone/movies'
    PATH_PAR_URL = '/medium/card_id/<card_id>'

    METHOD = 'GET'

    ATTR_CARD_ID = 'card_id'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, card_id) -> dict:

        payload = {}
        payload[EPCollectMediumByCardId.ATTR_CARD_ID] = card_id
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id = payload[EPCollectMediumByCardId.ATTR_CARD_ID]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPCollectMediumByCardId.METHOD, EPCollectMediumByCardId.URL,
                    EPCollectMediumByCardId.ATTR_CARD_ID, card_id
                )
        )

        output = self.web_gadget.db.get_medium_by_card_id(card_id=card_id, limit=100)
        
        return output_json(output, EP.CODE_OK)
