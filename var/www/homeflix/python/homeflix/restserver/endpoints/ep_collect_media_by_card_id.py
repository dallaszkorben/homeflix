import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectMediaByCardId(EP):

    ID = 'collect_standalone_media'
    URL = '/collect/standalone/media'

#    PATH_PAR_PAYLOAD = '/media'
    PATH_PAR_URL = '/media/card_id/<card_id>/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'
    ATTR_CARD_ID = 'card_id'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, card_id, lang) -> dict:

        payload = {}
        payload[EPCollectMediaByCardId.ATTR_CARD_ID] = card_id
        payload[EPCollectMediaByCardId.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id = payload[EPCollectMediaByCardId.ATTR_CARD_ID]
        lang = payload[EPCollectMediaByCardId.ATTR_LANG]
        
        output = self.web_gadget.db.get_media_by_card_id(card_id=card_id, lang=lang, limit=100)

        return output_json(output, EP.CODE_OK)
