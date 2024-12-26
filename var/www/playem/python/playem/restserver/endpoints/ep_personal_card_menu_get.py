import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPPersonalCardMenuGet(EP):

    URL = '/personal/card_menu/get'

    PATH_PAR_PAYLOAD = '/card_menu/get'
    PATH_PAR_URL = '/card_menu/get'

    METHOD = 'GET'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self) -> dict:
        payload = {}

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request ({0}): {1} {2}".format(
                    remoteAddress, EPPersonalCardMenuGet.METHOD, EPPersonalCardMenuGet.URL
                )
        )

        output = self.web_gadget.card_menu.get_card_menu()

        return output_json(output, EP.CODE_OK)
