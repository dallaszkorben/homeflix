import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

from playem.restserver.endpoints.ep_control_rebuild_db_static import EPControlRebuildDbStatic
from playem.restserver.endpoints.ep_control_rebuild_db_personal import EPControlRebuildDbPersonal

from playem.restserver.endpoints.ep_control_update_sw import EPControlUpdateSw

# -----------------------------------
#
# POST control
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:5000/control
# -----------------------------------
#
class ControlView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epControlRebuildDbStatic = EPControlRebuildDbStatic(web_gadget)
        self.epControlRebuildDbPersonal = EPControlRebuildDbPersonal(web_gadget)
        self.epControlUpdateSw = EPControlUpdateSw(web_gadget)

    #
    # POST http://localhost:5000/rebuild/
    #
    def index(self):
        return {}


    #
    # Rebuild the Static Database
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:5000/control/rebuild/db/static
    #
    # POST http://localhost:5000/control/rebuild/db/static
    #
    #@route('/rebuild', methods=['POST'])
    @route(EPControlRebuildDbStatic.PATH_PAR_PAYLOAD, methods=[EPControlRebuildDbStatic.METHOD])
    def controlRebuild(self):

        json_data = {}
        out = self.epControlRebuildDbStatic.executeByPayload(json_data)
        return out

    #
    # Rebuild the Personal Database
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:5000/control/rebuild/db/personal
    #
    # POST http://localhost:5000/control/rebuild/db/personal
    #
    #@route('/rebuild', methods=['POST'])
    @route(EPControlRebuildDbPersonal.PATH_PAR_PAYLOAD, methods=[EPControlRebuildDbPersonal.METHOD])
    def controlRebuild(self):

        json_data = {}
        out = self.epControlRebuildDbPersonal.executeByPayload(json_data)
        return out

   #
    # Update software
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:5000/control/update/sw
    #
    # POST http://localhost:5000/control/update/sw
    #
    #@route('/update', methods=['POST'])
    @route(EPControlUpdateSw.PATH_PAR_PAYLOAD, methods=[EPControlUpdateSw.METHOD])
    def controlUpdate(self):

        json_data = {}
        out = self.EPControlUpdateSw.executeByPayload(json_data)
        return out