import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json
from homeflix.translator.translator import Translator

from flask import request

class EPTranslateThemes(EP):

    URL = '/translate/themes'

    PATH_PAR_PAYLOAD = '/themes'
    PATH_PAR_URL = '/themes/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, lang) -> dict:

        payload = {}
        payload[EPTranslateThemes.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        lang = payload[EPTranslateThemes.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPTranslateThemes.METHOD, EPTranslateThemes.URL,
                    EPTranslateThemes.ATTR_LANG, lang
                )
        )

        trans = Translator.getInstance(lang)
        output=trans.translate_themes()

        return output_json(output, EP.CODE_OK)
