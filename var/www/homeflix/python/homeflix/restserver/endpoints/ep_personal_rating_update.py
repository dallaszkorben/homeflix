import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPPersonalRatingUpdate(EP):

    URL = '/personal/rating/update'

    PATH_PAR_PAYLOAD = '/rating/update'

    METHOD = 'POST'

    ATTR_CARD_ID = 'card_id'
    ATTR_RATE = 'rate'
    ATTR_SKIP_CONTINUOUS_PLAY = 'skip_continuous_play'
    
    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        card_id = payload[EPPersonalRatingUpdate.ATTR_CARD_ID]
        rate = payload.get(EPPersonalRatingUpdate.ATTR_RATE, None)
        skip_continuous_play = payload.get(EPPersonalRatingUpdate.ATTR_SKIP_CONTINUOUS_PLAY, None)
        #skip_continuous_play = payload.get(EPPersonalRatingUpdate.ATTR_SKIP_CONTINUOUS_PLAY, None)

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8})".format(
                    remoteAddress, EPPersonalRatingUpdate.METHOD, EPPersonalRatingUpdate.URL,
                    EPPersonalRatingUpdate.ATTR_CARD_ID, card_id,
                    EPPersonalRatingUpdate.ATTR_RATE, rate,
                    EPPersonalRatingUpdate.ATTR_SKIP_CONTINUOUS_PLAY, skip_continuous_play,
                )
        )

        output = self.web_gadget.db.update_rating(card_id=card_id, rate=rate, skip_continuous_play=skip_continuous_play)

        return output_json(output, EP.CODE_OK)
