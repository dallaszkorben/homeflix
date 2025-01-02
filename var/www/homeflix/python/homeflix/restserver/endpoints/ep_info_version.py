import os
import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPInfoVersion(EP):

    ID = 'info_version'
    URL = '/info/version'

    PATH_PAR_PAYLOAD = '/version'
    PATH_PAR_URL = '/version'

    METHOD = 'GET'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, epocDate) -> dict:

        payload = {}
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        logging.debug( "WEB request ({0}): {1} {2}".format(
                    remoteAddress, EPInfoVersion.METHOD, EPInfoVersion.URL
                )
        )

        version = None
        version_path = os.path.join(self.web_gadget.projectPath, "version.txt")
        try:
            with open(version_path, "r") as f:
                version = f.read().strip()
        except:
            version = 'not known'

        output = {'version': version}

        return output_json( output, EP.CODE_OK)
