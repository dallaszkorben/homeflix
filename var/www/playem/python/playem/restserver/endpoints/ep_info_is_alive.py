import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPInfoIsAlive(EP):

    ID = 'info_is_alive'
    URL = '/info/isAlive'

    PATH_PAR_PAYLOAD = '/isAlive'
    PATH_PAR_URL = '/isAlive'

    METHOD = 'GET'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    @staticmethod
    def getRequestDescriptionWithPayloadParameters():

        ret = {}
        ret['id'] = EPInfoIsAlive.ID
        ret['method'] = EPInfoIsAlive.METHOD
        ret['path-parameter-in-payload'] = EPInfoIsAlive.PATH_PAR_PAYLOAD
        ret['path-parameter-in-url'] = EPInfoIsAlive.PATH_PAR_URL

        ret['parameters'] = [{}]

        return ret

    def executeByParameters(self, epocDate) -> dict:

        payload = {}
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        logging.debug( "WEB request ({0}): {1} {2}".format(
                    remoteAddress, EPInfoIsAlive.METHOD, EPInfoIsAlive.URL
                )
        )

        return output_json( {'result': True}, EP.CODE_OK)
