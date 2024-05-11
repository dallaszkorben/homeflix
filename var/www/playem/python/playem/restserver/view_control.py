import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

from playem.restserver.endpoints.ep_control_rebuild import EPControlRebuild
from playem.restserver.endpoints.ep_control_update import EPControlUpdate

# -----------------------------------
#
# POST control
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:5000/control
# -----------------------------------
#
# GET http://localhost:5000/info
class ControlView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epControlRebuild = EPControlRebuild(web_gadget)
        self.epControlUpdate = EPControlUpdate(web_gadget)

    #
    # POST http://localhost:5000/rebuild/
    #
    def index(self):
        return {}


    #
    # Rebuild the database
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:5000/control/rebuild
    #
    # POST http://localhost:5000/control/rebuild
    #
    #@route('/rebuild', methods=['POST'])
    @route(EPControlRebuild.PATH_PAR_PAYLOAD, methods=[EPControlRebuild.METHOD])
    def controlRebuild(self):

        json_data = {}
        out = self.epControlRebuild.executeByPayload(json_data)
        return out

   #
    # Update software
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:5000/control/update
    #
    # POST http://localhost:5000/control/update
    #
    #@route('/update', methods=['POST'])
    @route(EPControlUpdate.PATH_PAR_PAYLOAD, methods=[EPControlUpdate.METHOD])
    def controlUpdate(self):

        json_data = {}
        out = self.epControlUpdate.executeByPayload(json_data)
        return out