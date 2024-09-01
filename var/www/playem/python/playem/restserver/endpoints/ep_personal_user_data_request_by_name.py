import logging
# import subprocess
# import os
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPPersonalUserDataRequestByName(EP):

    URL = '/personal/user_data/request/by/name'

    PATH_PAR_PAYLOAD = '/user_data/request/by/name'
    PATH_PAR_URL = '/user_data/request/by/name/<user_name>'

    METHOD = 'GET'

    ATTR_USER_NAME = 'user_name'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, user_name) -> dict:
        payload = {}
        payload[EPPersonalUserDataRequestByName.ATTR_USER_NAME] = user_name
                
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        user_name = payload[EPPersonalUserDataRequestByName.ATTR_USER_NAME]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4})".format(
                    remoteAddress, EPPersonalUserDataRequestByName.METHOD, EPPersonalUserDataRequestByName.URL,
                    EPPersonalUserDataRequestByName.ATTR_USER_NAME, user_name
                )
        )

        output = self.web_gadget.db.get_user(user_name)

        return output_json(output, EP.CODE_OK)
