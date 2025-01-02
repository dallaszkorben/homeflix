import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectDirectorsByMovieCount(EP):

    ID = 'collect_directors_by_movie_count'
    URL = '/collect/directors/by/movie/count'

    PATH_PAR_PAYLOAD = '/directors/by/movie/count'
    PATH_PAR_URL = '/directors/by/movie/count/category/<category>/minimum/<minimum>/limit/<limit>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_MINIMUM = 'minimum'
    ATTR_LIMIT = 'limit'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, minimum=3, limit=15) -> dict:
        payload = {}

        payload[EPCollectDirectorsByMovieCount.ATTR_CATEGORY] = category
        payload[EPCollectDirectorsByMovieCount.ATTR_MINIMUM] = minimum
        payload[EPCollectDirectorsByMovieCount.ATTR_LIMIT] = limit
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category   = payload[EPCollectDirectorsByMovieCount.ATTR_CATEGORY]
        minimum   = int(payload.get(EPCollectDirectorsByMovieCount.ATTR_MINIMUM, 3))
        limit       = int(payload.get(EPCollectDirectorsByMovieCount.ATTR_LIMIT, 15))

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8})".format(
                remoteAddress, EPCollectDirectorsByMovieCount.METHOD, EPCollectDirectorsByMovieCount.URL,
                EPCollectDirectorsByMovieCount.ATTR_CATEGORY, category,
                EPCollectDirectorsByMovieCount.ATTR_MINIMUM, minimum,
                EPCollectDirectorsByMovieCount.ATTR_LIMIT, limit
            )
        )

        output = self.web_gadget.db.get_list_of_directors(category=category, minimum=minimum, limit=limit, json=True)

        return output_json(output, EP.CODE_OK)
