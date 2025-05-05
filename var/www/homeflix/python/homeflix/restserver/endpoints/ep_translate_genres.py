import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json
from homeflix.translator.translator import Translator

from flask import request

class EPTranslateGenres(EP):

    URL = '/translate/genres'

    PATH_PAR_PAYLOAD = '/genres'
    PATH_PAR_URL = '/genres/category/<category>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, lang) -> dict:

        payload = {}
        payload[EPTranslateGenres.ATTR_CATEGORY] = category
        payload[EPTranslateGenres.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category = payload[EPTranslateGenres.ATTR_CATEGORY]
        lang = payload[EPTranslateGenres.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}) ('{5}': {6})".format(
                    remoteAddress, EPTranslateGenres.METHOD, EPTranslateGenres.URL,
                    EPTranslateGenres.ATTR_CATEGORY, category,
                    EPTranslateGenres.ATTR_LANG, lang
                )
        )

        trans = Translator.getInstance(lang)
        output=trans.translate_genres(category=category)

        return output_json({"result": True, "data": output, "error": None}, EP.CODE_OK)
#        return output_json(output, EP.CODE_OK)
