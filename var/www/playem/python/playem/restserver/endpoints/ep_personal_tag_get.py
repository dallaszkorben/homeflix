import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPPersonalTagGet(EP):

    URL = '/personal/tag/get'

    PATH_PAR_PAYLOAD = '/tag/get'
    PATH_PAR_URL = '/tag/get'

    METHOD = 'GET'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request ({0}): {1} {2} ()".format(
                    remoteAddress, EPPersonalTagGet.METHOD, EPPersonalTagGet.URL
                )
        )

        output = self.web_gadget.db.get_tags()
        return output_json(output, EP.CODE_OK)
