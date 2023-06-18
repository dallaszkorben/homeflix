import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectAllSeriesMovies(EP):

    ID = 'collect_all_series_movies'
    URL = '/collect/all/series/movies'

    PATH_PAR_PAYLOAD = '/all/series/movies'
    PATH_PAR_URL = '/all/series/movies/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, lang) -> dict:

        payload = {}
        payload[EPCollectAllSeriesMovies.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        lang = payload[EPCollectAllSeriesMovies.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPCollectAllSeriesMovies.METHOD, EPCollectAllSeriesMovies.URL,
                    EPCollectAllSeriesMovies.ATTR_LANG, lang
                )
        )

        output = self.web_gadget.db.get_series_of_movies(lang=lang, limit=100)
        
#        for record in output:
#            print("DECODE: ".format(urlencode(record["title_req"])))

        return output_json(output, EP.CODE_OK)
