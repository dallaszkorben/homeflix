import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectTags(EP):

    ID = 'collect_tags'
    URL = '/collect/tags'

    PATH_PAR_PAYLOAD = '/tags'
    PATH_PAR_URL = '/tags/category/<category>/limit/<limit>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_LIMIT = 'limit'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, limit=15) -> dict:
        payload = {}

        payload[EPCollectTags.ATTR_CATEGORY] = category
        payload[EPCollectTags.ATTR_LIMIT] = limit

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category   = payload[EPCollectTags.ATTR_CATEGORY]
        limit       = int(payload.get(EPCollectTags.ATTR_LIMIT, 15))

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6})".format(
                remoteAddress, EPCollectTags.METHOD, EPCollectTags.URL,
                EPCollectTags.ATTR_CATEGORY, category,
                EPCollectTags.ATTR_LIMIT, limit
            )
        )

        output = self.web_gadget.db.get_list_of_tags(category=category, limit=limit, json=True)

        return output_json(output, EP.CODE_OK)
