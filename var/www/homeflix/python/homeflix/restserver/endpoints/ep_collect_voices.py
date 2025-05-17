import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectVoices(EP):

    ID = 'collect_voices'
    URL = '/collect/voices'

    PATH_PAR_PAYLOAD = '/voices'
    PATH_PAR_URL = '/voices/category/<category>/limit/<limit>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_LIMIT = 'limit'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, limit=15) -> dict:
        payload = {}

        payload[EPCollectVoices.ATTR_CATEGORY] = category
        payload[EPCollectVoices.ATTR_LIMIT] = limit

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category   = payload[EPCollectVoices.ATTR_CATEGORY]
        limit       = int(payload.get(EPCollectVoices.ATTR_LIMIT, 15))

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6})".format(
                remoteAddress, EPCollectVoices.METHOD, EPCollectVoices.URL,
                EPCollectVoices.ATTR_CATEGORY, category,
                EPCollectVoices.ATTR_LIMIT, limit
            )
        )

        output = self.web_gadget.db.get_list_of_voices(category=category, limit=limit, json=True)

        return output_json(output, EP.CODE_OK)
