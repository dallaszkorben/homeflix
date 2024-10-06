import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

from playem.restserver.endpoints.ep_auth_login import EPAuthLogin
from playem.restserver.endpoints.ep_auth_logout import EPAuthLogout

# -----------------------------------
#
# Authentication
#
# curl  --header "Content-Type: application/json" --request POST --data '{ "username": "admin", "password": "secretPassw0rd"}' http://localhost:80/auth/login
#
#
# -----------------------------------
#
class AuthView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epAuthLogin = EPAuthLogin(web_gadget)
        self.epAuthLogout = EPAuthLogout(web_gadget)

    #
    # GET http://localhost:5000/auth/
    #
    def index(self):
        return {}


# === Login ===

    #
    # Tries to login. If it is successfu, returns the user settings, if it is not successful, returns empty dict
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{ "username": "admin", "password": "secretPassw0rd"}' http://localhost:80/auth/login
    #
    # POST   http://localhost:80/auth/login
    #       body {
    #           "username": "admin",
    #           "password": "secretPassw0rd"
    #       }
    #
    #       response{
    #           'result': True,
    #           'data': {        
    #               language_code: "en"
    #               name: "admin"
    #               play_continuously: 1
    #               show_lyrics_anyway: 1
    #               show_original_title: 1
    #               show_storyline_anyway: 1
    #           },
    #           'error': None
    #       }
    #
    #@route('/auth/login', method=["POST"])
    @route(EPAuthLogin.PATH_PAR_PAYLOAD, methods=[EPAuthLogin.METHOD])
    def authLoginWithPayload(self):


        


        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return output_json({'result': False, 'data':{}, 'error': 'Not valid request'}, EP.CODE_BAD_REQUEST)

        out = self.epAuthLogin.executeByPayload(json_data)
        return out


# === Logout ===

    #
    # Logout
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{}' http://localhost:80/auth/logout
    #
    # POST   http://localhost:80/auth/logout
    #       body {}
    #
    #       response{
    #           'result': True,
    #           'data': {},
    #           'error': None
    #       }
    #
    #@route('/auth/logout', method=["POST"])
    @route(EPAuthLogout.PATH_PAR_PAYLOAD, methods=[EPAuthLogout.METHOD])
    def authLogoutWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return output_json({'result': False, 'data':{}, 'error': 'Not valid request'}, EP.CODE_BAD_REQUEST)

        out = self.epAuthLogout.executeByPayload(json_data)
        return out
