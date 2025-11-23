import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectHighestMixedAbc(EP):

    ID = 'collect_abc'
    URL = '/collect/highest/mixed/abc'

    PATH_PAR_PAYLOAD = '/highest/mixed/abc'

    METHOD = 'GET'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        logging.debug("WEB request ({0}): {1} {2} - payload: {3}".format(
                remoteAddress, EPCollectHighestMixedAbc.METHOD, EPCollectHighestMixedAbc.URL, payload
            )
        )

        output = self.web_gadget.db.get_highest_level_abc(**payload)

        return output_json(output, EP.CODE_OK)
