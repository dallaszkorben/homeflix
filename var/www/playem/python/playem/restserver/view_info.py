import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

from playem.restserver.endpoints.ep_info_is_alive import EPInfoIsAlive

# -----------------------------------
#
# GET info
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:5000/info/isAlive
# -----------------------------------
#
# GET http://localhost:5000/info
class InfoView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

#        self.epInfoFunctions = EPInfoFunctions(web_gadget)
        self.epInfoIsAlive = EPInfoIsAlive(web_gadget)

    #
    # GET http://localhost:5000/info/
    #
    def index(self):
        return {}


    #
    # Gives back True
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:5000/info/isAlive
    #
    # GET http://localhost:5000/info/isAlive
    #
    #@route('/isAlive', methods=['GET'])
    @route(EPInfoIsAlive.PATH_PAR_PAYLOAD, methods=[EPInfoIsAlive.METHOD])
    def infoIsAlive(self):

        json_data = {}
        out = self.epInfoIsAlive.executeByPayload(json_data)
        return out
