import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json
from playem.translator.translator import Translator

from flask import request

class EPTranslateTitles(EP):

    URL = '/translate/titles'

    PATH_PAR_PAYLOAD = '/titles'
    PATH_PAR_URL = '/titles/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, lang) -> dict:

        payload = {}
        payload[EPTranslateTitles.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        lang = payload[EPTranslateTitles.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPTranslateTitles.METHOD, EPTranslateTitles.URL,
                    EPTranslateTitles.ATTR_LANG, lang
                )
        )

        trans = Translator.getInstance(lang)
        output=trans.translate_titles()

        return output_json(output, EP.CODE_OK)
