from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

class EPTranslateSelectableLanguages(EP):

    URL = '/translate/selectable_languages'
    PATH_PAR_PAYLOAD = '/selectable_languages'
    METHOD = 'GET'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        output = self.web_gadget.db.get_selectable_languages()
        return output_json(output, EP.CODE_OK)
