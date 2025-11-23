import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectAbc(EP):

    ID = 'collect_abc'
    URL = '/collect/abc'

    PATH_PAR_PAYLOAD = '/abc'
    PATH_PAR_URL = '/abc/category/<category>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_MAXIMUM = 'maximum'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, lang='en') -> dict:
        payload = {}

        payload[EPCollectAbc.ATTR_CATEGORY] = category
        payload[EPCollectAbc.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category = payload[EPCollectAbc.ATTR_CATEGORY]
        lang = payload.get(EPCollectAbc.ATTR_LANG, "en")

        logging.debug("WEB request ({0}): {1} {2} - payload: {3}".format(
                remoteAddress, EPCollectAbc.METHOD, EPCollectAbc.URL, payload
            )
        )

        output = self.web_gadget.db.get_abc(**payload)

        return output_json(output, EP.CODE_OK)
