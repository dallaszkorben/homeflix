import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.representations import output_json

from homeflix.restserver.endpoints.ep_control_rebuild_db_static import EPControlRebuildDbStatic
from homeflix.restserver.endpoints.ep_control_rebuild_db_personal import EPControlRebuildDbPersonal

from homeflix.restserver.endpoints.ep_control_update_sw import EPControlUpdateSw

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
    # curl  --header "Content-Type: application/json" --request POST http://localhost:80/control/rebuild/db/static
    #
    # POST http://localhost:80/control/rebuild/db/static
    #
    #@route('/rebuild/db/static', methods=['POST'])
    @route(EPControlRebuildDbStatic.PATH_PAR_PAYLOAD, methods=[EPControlRebuildDbStatic.METHOD])
    def controlRebuildDbStatic(self):

        json_data = {}
        out = self.epControlRebuildDbStatic.executeByPayload(json_data)
        return out

    #
    # Rebuild the Personal Database
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:80/control/rebuild/db/personal
    #
    # POST http://localhost:80/control/rebuild/db/personal
    #
    #@route('/rebuild/db/personal', methods=['POST'])
    @route(EPControlRebuildDbPersonal.PATH_PAR_PAYLOAD, methods=[EPControlRebuildDbPersonal.METHOD])
    def controlRebuildDbPersonal(self):

        json_data = {}
        out = self.epControlRebuildDbPersonal.executeByPayload(json_data)
        return out

    #
    # Update software
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:80/control/update/sw
    #
    # POST http://localhost:80/control/update/sw
    #
    #@route('/update/sw', methods=['POST'])
    @route(EPControlUpdateSw.PATH_PAR_PAYLOAD, methods=[EPControlUpdateSw.METHOD])
    def controlUpdateSw(self):

        json_data = {}
        out = self.epControlUpdateSw.executeByPayload(json_data)
        return out