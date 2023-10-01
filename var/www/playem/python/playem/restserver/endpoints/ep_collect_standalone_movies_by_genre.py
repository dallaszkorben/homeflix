import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectStandaloneMoviesByGenre(EP):

    ID = 'collect_standalone_movies'
    URL = '/collect/standalone/movies'

#    PATH_PAR_PAYLOAD = '/standalone/movies'
    PATH_PAR_URL = '/standalone/movies/genre/<genre>/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'
    ATTR_GENRE = 'genre'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, genre, lang) -> dict:

        payload = {}
        payload[EPCollectStandaloneMoviesByGenre.ATTR_GENRE] = genre
        payload[EPCollectStandaloneMoviesByGenre.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        genre = payload[EPCollectStandaloneMoviesByGenre.ATTR_GENRE]
        lang = payload[EPCollectStandaloneMoviesByGenre.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}) ('{5}': {6})".format(
                    remoteAddress, EPCollectStandaloneMoviesByGenre.METHOD, EPCollectStandaloneMoviesByGenre.URL,
                    EPCollectStandaloneMoviesByGenre.ATTR_GENRE, genre,
                    EPCollectStandaloneMoviesByGenre.ATTR_LANG, lang
                )
        )

        output = self.web_gadget.db.get_standalone_movies_by_genre(genre=genre, lang=lang, limit=100)

        return output_json(output, EP.CODE_OK)
