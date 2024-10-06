import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request, session

class EPPersonalUserDataRequest(EP):

    URL = '/personal/user_data/request'

    PATH_PAR_PAYLOAD = '/user_data/request'
    PATH_PAR_URL = '/user_data/request'

    METHOD = 'GET'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self) -> dict:
        payload = {}
               
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request ({0}): {1} {2} ()".format(
            remoteAddress, EPPersonalUserDataRequest.METHOD, EPPersonalUserDataRequest.URL,
            )
        )

        output = self.web_gadget.db.get_logged_in_user_data()

        return output_json(output, EP.CODE_OK)
