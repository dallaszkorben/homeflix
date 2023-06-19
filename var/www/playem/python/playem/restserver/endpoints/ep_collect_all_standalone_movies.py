import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectAllStandaloneMovies(EP):

    ID = 'collect_all_standalone_movies'
    URL = '/collect/all/standalone/movies'

    PATH_PAR_PAYLOAD = '/all/standalone/movies'
    PATH_PAR_URL = '/all/standalone/movies/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, lang) -> dict:

        payload = {}
        payload[EPCollectAllStandaloneMovies.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        lang = payload[EPCollectAllStandaloneMovies.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPCollectAllStandaloneMovies.METHOD, EPCollectAllStandaloneMovies.URL,
                    EPCollectAllStandaloneMovies.ATTR_LANG, lang
                )
        )

        output = self.web_gadget.db.get_all_standalone_movies(lang=lang, limit=100)
        
#        for record in output:
#            print("DECODE: ".format(urlencode(record["title_req"])))

        return output_json(output, EP.CODE_OK)
