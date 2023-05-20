import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

#from playem.restserver.endpoints.ep_info_functions import EPInfoFunctions
from playem.restserver.endpoints.ep_info_is_alive import EPInfoIsAlive

# -----------------------------------
#
# GET info
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:5000/info/request
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

# === GET /info/timeStamp ===

    #
    # Get actual timestamp by the epoc - with payload
    #
    # curl  --header "Content-Type: application/json" --request GET --data '{"epocDate":"2000.00.00T00:00:00"}' http://localhost:5000/info/timeStamp
    #
    # GET http://localhost:5000/info/timeStamp
    #      body: {
    #            "epocDate":"2000.00.00T00:00:00"
    #           }
    #
#    #@route('/timeStamp', methods=['GET'])
#    @route(EPInfoTimeStamp.PATH_PAR_PAYLOAD, methods=[EPInfoTimeStamp.METHOD])
#    def infoTimeStampWithPayload(self):
#
#        # WEB
#        if request.form:
#            json_data = request.form
#
#        # CURL
#        elif request.json:
#            json_data = request.json
#
#        else:
#            return "Not valid request", EP.CODE_BAD_REQUEST
#
#        out = self.epInfoTimeStamp.executeByPayload(json_data)
#        return out

    #
    # Get actual timestamp by the epoc - with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:5000/info/timeStamp/epocDate/2000.00.00T00:00:00
    #
    # READ http://localhost:5000/info/timeStamp/epocDate/2000.00.00T00:00:00
    #
#    #@route('/timeStamp/epocDate/<epocDate>', methods=['GET'])
#    @route(EPInfoTimeStamp.PATH_PAR_URL, methods=[EPInfoTimeStamp.METHOD])
#    def infoTimeStampWithParameter(self, epocDate):
#
#        out = self.epInfoTimeStamp.executeByParameters(epocDate)
#        return out






# === GET /info/isAlive ===

    #
    # Get actual timestamp by the epoc - with payload
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:5000/info/ready
    #
    # GET http://localhost:5000/info/ready
    #
    #@route('/isAlive', methods=['GET'])
    @route(EPInfoIsAlive.PATH_PAR_PAYLOAD, methods=[EPInfoIsAlive.METHOD])
    def infoIsAlive(self):

        json_data = {}
        out = self.epInfoIsAlive.executeByPayload(json_data)
        return out
