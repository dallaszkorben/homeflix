import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json
from playem.translator.translator import Translator

from flask import request

class EPTranslateGenre(EP):

    URL = '/translate/genre'

    PATH_PAR_PAYLOAD = '/genre'
    PATH_PAR_URL = '/genre/<genre>/category/<category>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_GENRE = 'genre'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, genre, lang) -> dict:

        payload = {}
        payload[EPTranslateGenre.ATTR_CATEGORY] = category
        payload[EPTranslateGenre.ATTR_GENRE] = genre
        payload[EPTranslateGenre.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category = payload[EPTranslateGenre.ATTR_CATEGORY]
        genre = payload[EPTranslateGenre.ATTR_GENRE]
        lang = payload[EPTranslateGenre.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}) ('{5}': {6}) ('{7}': {8})".format(
                    remoteAddress, EPTranslateGenre.METHOD, EPTranslateGenre.URL,
                    EPTranslateGenre.ATTR_CATEGORY, category,
                    EPTranslateGenre.ATTR_GENRE, genre,
                    EPTranslateGenre.ATTR_LANG, lang
                )
        )

        trans = Translator.getInstance(lang)
        output=trans.translate_genre(category=category, genre=genre)

        return output_json(output, EP.CODE_OK)
