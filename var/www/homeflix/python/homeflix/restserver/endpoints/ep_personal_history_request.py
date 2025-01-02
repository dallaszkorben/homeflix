import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPPersonalHistoryRequest(EP):

    URL = '/personal/history/request/'

    PATH_PAR_PAYLOAD = '/history/request'
#    PATH_PAR_URL = '/history/request/by/user_id/<user_id>/card_id/<card_id>/limit_days/<limit_days>/limit_records/<limit_records>'

    METHOD = 'GET'

#    ATTR_USER_ID = 'user_id'
    ATTR_CARD_ID = 'card_id'
    ATTR_LIMIT_DAYS = 'limit_days'
    ATTR_LIMIT_RECORDS = 'limit_records'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

#        user_id = payload[EPPersonalHistoryRequest.ATTR_USER_ID]
        card_id = payload.get(EPPersonalHistoryRequest.ATTR_CARD_ID, None)
        limit_days = payload.get(EPPersonalHistoryRequest.ATTR_LIMIT_DAYS, None)
        limit_records = payload.get(EPPersonalHistoryRequest.ATTR_LIMIT_RECORDS, None)

#        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10})".format(
        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8})".format(
                    remoteAddress, EPPersonalHistoryRequest.METHOD, EPPersonalHistoryRequest.URL,
#                    EPPersonalHistoryRequest.ATTR_USER_ID, user_id,
                    EPPersonalHistoryRequest.ATTR_CARD_ID, card_id,
                    EPPersonalHistoryRequest.ATTR_LIMIT_DAYS, limit_days,
                    EPPersonalHistoryRequest.ATTR_LIMIT_RECORDS, limit_records
                )
        )

        limit_days = int(limit_days) if limit_days else limit_days
        limit_records = int(limit_records) if limit_records else limit_records
#        output = self.web_gadget.db.get_history(user_id, card_id=card_id, limit_days=limit_days, limit_records=limit_records)
        output = self.web_gadget.db.get_history(card_id=card_id, limit_days=limit_days, limit_records=limit_records)

        return output_json(output, EP.CODE_OK)
