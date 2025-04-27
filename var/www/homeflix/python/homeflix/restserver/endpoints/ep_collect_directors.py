import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectDirectors(EP):

    ID = 'collect_directors'
    URL = '/collect/directors'

    PATH_PAR_PAYLOAD = '/directors'
    PATH_PAR_URL = '/directors/by/movie/count/category/<category>/limit/<limit>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_LIMIT = 'limit'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, limit=15) -> dict:
        payload = {}

        payload[EPCollectDirectors.ATTR_CATEGORY] = category
        payload[EPCollectDirectors.ATTR_LIMIT] = limit

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category   = payload[EPCollectDirectors.ATTR_CATEGORY]
        limit       = int(payload.get(EPCollectDirectors.ATTR_LIMIT, 15))

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6})".format(
                remoteAddress, EPCollectDirectors.METHOD, EPCollectDirectors.URL,
                EPCollectDirectors.ATTR_CATEGORY, category,
                EPCollectDirectors.ATTR_LIMIT, limit
            )
        )

        output = self.web_gadget.db.get_list_of_directors(category=category, limit=limit, json=True)

        return output_json(output, EP.CODE_OK)
