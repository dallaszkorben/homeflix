import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request, session

class EPAuthLogout(EP):

    URL = '/auth/logout'

    PATH_PAR_PAYLOAD = '/logout'

    METHOD = 'POST'
  
    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request ({0}): {1} {2} ()".format(
                    remoteAddress, EPAuthLogout.METHOD, EPAuthLogout.URL,
                )
        )

        output = self.web_gadget.db.logout()

#
        session.pop('logged_in_user', None)
#
#        return output_json({'result': True, 'data': {}, 'error': None}, EP.CODE_OK)

        return output_json(output, EP.CODE_OK)
