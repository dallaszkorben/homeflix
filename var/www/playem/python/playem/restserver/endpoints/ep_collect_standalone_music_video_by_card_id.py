import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectStandaloneMusicVideoByCardId(EP):

    ID = 'collect_standalone_music_video'
    URL = '/collect/standalone/music_video'

#    PATH_PAR_PAYLOAD = '/standalone/movie'
    PATH_PAR_URL = '/standalone/music_video/card_id/<card_id>/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'
    ATTR_CARD_ID = 'card_id'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, card_id, lang) -> dict:

        payload = {}
        payload[EPCollectStandaloneMusicVideoByCardId.ATTR_CARD_ID] = card_id
        payload[EPCollectStandaloneMusicVideoByCardId.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id = payload[EPCollectStandaloneMusicVideoByCardId.ATTR_CARD_ID]
        lang = payload[EPCollectStandaloneMusicVideoByCardId.ATTR_LANG]
        
        output = self.web_gadget.db.get_standalone_music_video_by_card_id(card_id=card_id, lang=lang, limit=100)

        return output_json(output, EP.CODE_OK)
