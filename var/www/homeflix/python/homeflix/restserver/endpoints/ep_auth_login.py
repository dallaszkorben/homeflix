import logging
import time

from homeflix.card.database import SqlDatabase as DB

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request, session

class EPAuthLogin(EP):

    URL = '/auth/login'

    PATH_PAR_PAYLOAD = '/login'

    METHOD = 'POST'

    ATTR_USERNAME = 'username'
    ATTR_PASSWORD = 'password'
  
    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        username = payload[EPAuthLogin.ATTR_USERNAME]
        password = payload[EPAuthLogin.ATTR_PASSWORD]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6})".format(
            remoteAddress, EPAuthLogin.METHOD, EPAuthLogin.URL,
            EPAuthLogin.ATTR_USERNAME, username,
            EPAuthLogin.ATTR_PASSWORD, "************",
            )
        )

        output = self.web_gadget.db.login(username=username, password=password)

        return output_json(output, EP.CODE_OK)
