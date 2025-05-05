import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json
from homeflix.translator.translator import Translator

from flask import request

class EPTranslateInteractionLabels(EP):

    URL = '/translate/interaction_labels'

    PATH_PAR_PAYLOAD = '/interaction_labels'
    PATH_PAR_URL = '/interaction_labels/lang/<lang>'

    METHOD = 'GET'

    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, lang) -> dict:

        payload = {}
        payload[EPTranslateInteractionLabels.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        lang = payload[EPTranslateInteractionLabels.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPTranslateInteractionLabels.METHOD, EPTranslateInteractionLabels.URL,
                    EPTranslateInteractionLabels.ATTR_LANG, lang
                )
        )

        trans = Translator.getInstance(lang)
        output=trans.translate_interaction_labels()

        return output_json({"result": True, "data": output, "error": None}, EP.CODE_OK)
#        return output_json(output, EP.CODE_OK)
