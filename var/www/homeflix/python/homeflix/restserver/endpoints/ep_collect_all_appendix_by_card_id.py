import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectAllAppendixByCardId(EP):

    ID = 'collect_all_appendix'
    URL = '/collect/all/appendix'

#    PATH_PAR_PAYLOAD = '/standalone/movie'
    PATH_PAR_URL = '/all/appendix/card_id/<card_id>/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'
    ATTR_CARD_ID = 'card_id'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, card_id, lang) -> dict:

        payload = {}
        payload[EPCollectAllAppendixByCardId.ATTR_CARD_ID] = card_id
        payload[EPCollectAllAppendixByCardId.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id = payload[EPCollectAllAppendixByCardId.ATTR_CARD_ID]
        lang = payload[EPCollectAllAppendixByCardId.ATTR_LANG]
        
        output = self.web_gadget.db.get_all_appendix(card_id=card_id, lang=lang, limit=100)

        return output_json(output, EP.CODE_OK)
