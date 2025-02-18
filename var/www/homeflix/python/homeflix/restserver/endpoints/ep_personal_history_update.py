import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPPersonalHistoryUpdate(EP):

    URL = '/personal/history/update'

    PATH_PAR_PAYLOAD = '/history/update'

    METHOD = 'POST'

    ATTR_CARD_ID = 'card_id'
    ATTR_RECENT_POSITION = 'recent_position'    
    ATTR_START_EPOCH = 'start_epoch'
    
    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        card_id = payload[EPPersonalHistoryUpdate.ATTR_CARD_ID]
        recent_position = payload[EPPersonalHistoryUpdate.ATTR_RECENT_POSITION]
        start_epoch = payload.get(EPPersonalHistoryUpdate.ATTR_START_EPOCH, None)

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8})".format(
                    remoteAddress, EPPersonalHistoryUpdate.METHOD, EPPersonalHistoryUpdate.URL,
                    EPPersonalHistoryUpdate.ATTR_CARD_ID, card_id,
                    EPPersonalHistoryUpdate.ATTR_RECENT_POSITION, recent_position,
                    EPPersonalHistoryUpdate.ATTR_START_EPOCH, start_epoch,
                )
        )

        output = self.web_gadget.db.update_play_position(card_id=card_id, recent_position=recent_position, start_epoch=start_epoch)

        return output_json(output, EP.CODE_OK)
