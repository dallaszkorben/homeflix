import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPPersonalHistoryUpdate(EP):

    URL = '/personal/history/update/by'

    PATH_PAR_PAYLOAD = '/history/update'
    PATH_PAR_URL = '/history/update/by/user_id/<user_id>/card_id/<card_id>/last_position/<last_position>/start_epoch/<start_epoch>'

    METHOD = 'POST'

    ATTR_USER_ID = 'user_id'
    ATTR_CARD_ID = 'card_id'
    ATTR_LAST_POSITION = 'last_position'
    ATTR_START_EPOCH = 'start_epoch'
    

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, user_id, card_id, last_position, start_epoch=None) -> dict:
        payload = {}
        payload[EPPersonalHistoryUpdate.ATTR_USER_ID] = user_id
        payload[EPPersonalHistoryUpdate.ATTR_CARD_ID] = card_id
        payload[EPPersonalHistoryUpdate.ATTR_LAST_POSITION] = last_position
        payload[EPPersonalHistoryUpdate.ATTR_START_EPOCH] = start_epoch
                
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        user_id = payload[EPPersonalHistoryUpdate.ATTR_USER_ID]
        card_id = payload[EPPersonalHistoryUpdate.ATTR_CARD_ID]
        last_position = payload[EPPersonalHistoryUpdate.ATTR_LAST_POSITION]
        start_epoch = payload.get(EPPersonalHistoryUpdate.ATTR_START_EPOCH, None)

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10})".format(
                    remoteAddress, EPPersonalHistoryUpdate.METHOD, EPPersonalHistoryUpdate.URL,
                    EPPersonalHistoryUpdate.ATTR_USER_ID, user_id,
                    EPPersonalHistoryUpdate.ATTR_CARD_ID, card_id,
                    EPPersonalHistoryUpdate.ATTR_LAST_POSITION, last_position,
                    EPPersonalHistoryUpdate.ATTR_START_EPOCH, start_epoch,
                )
        )

        output = self.web_gadget.db.update_play_position(user_id, card_id, last_position, start_epoch)

        return output_json(output, EP.CODE_OK)
