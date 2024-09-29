import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json


from playem.restserver.endpoints.ep_personal_user_data_request_by_name import EPPersonalUserDataRequestByName
from playem.restserver.endpoints.ep_personal_user_data_update import EPPersonalUserDataUpdate
from playem.restserver.endpoints.ep_personal_history_request import EPPersonalHistoryRequest
from playem.restserver.endpoints.ep_personal_history_update import EPPersonalHistoryUpdate


# -----------------------------------
#
# Personal data
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/user_data/request/by/name/<user_name>
# curl  --header "Content-Type: application/json" --request PUT --data '{ "user_id": 1, "language_code": "hu"}' http://localhost:80/personal/user_data/update
#
# curl  --header "Content-Type: application/json" --request GET --data '{ "user_id": 1, "card_id": 1056064754705651379, "limit_days": 5, "limit_records": 5}' http://localhost:80/personal/history/request
#
# curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2", "start_epoch": 1725117021}' http://localhost:80/personal/history/update
# curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2"}' http://localhost:80/personal/history/update
#
#
# -----------------------------------
#
class PersonalView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epPersonalUserDataRequestByName = EPPersonalUserDataRequestByName(web_gadget)
        self.ePPersonalUserDataUpdate = EPPersonalUserDataUpdate(web_gadget)
        self.ePPersonalHistoryRequest = EPPersonalHistoryRequest(web_gadget)
        self.ePPersonalHistoryUpdate= EPPersonalHistoryUpdate(web_gadget)

    #
    # GET http://localhost:5000/personal/
    #
    def index(self):
        return {}


# === get user data by user name ===

    #
    # Gives back all user data of a user identified by the given name
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/user_data/request/by/name/<user_name>
    #
    # example:
    #    curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/user_data/request/by/name/admin
    # response: 
    #   {
    #       id: 1234
    #       language_code: "en"
    #       language_id: 2
    #       name: "admin"
    #       play_continuously: 1
    #       show_lyrics_anyway: 1
    #       show_original_title: 1
    #       show_storyline_anyway: 1
    #   }
    #
    #@route('/user_data/request/by/name<user_name>')
    @route(EPPersonalUserDataRequestByName.PATH_PAR_URL, methods=[EPPersonalUserDataRequestByName.METHOD])
    def personalUserdataByName(self, user_name):

        out = self.epPersonalUserDataRequestByName.executeByParameters(user_name)
        return out


#=== PUT user data by user name ===

    #
    # Update User data identified by the given user id
    #
    # curl  --header "Content-Type: application/json" --request PUT --data '{ "user_id": 1, "language_code": "hu"}' http://localhost:80/personal/user_data/update
    #
    # example:
    #    curl  --header "Content-Type: application/json" --request PUT --data '{ "user_id": 1, "language_code": "hu"}' http://localhost:80/personal/user_data/update
    # response:
    #     { 
    #        "user_id": 1,
    #        "language_code": "hu",
    #        "show_original_title": true,
    #        "show_lyrics_anyway": true,
    #        "show_storyline_anyway: true,
    #        "play_continuously: false
    #      }
    #
    #@route('/user_data/update', methods=['PUT'])
    @route(EPPersonalUserDataUpdate.PATH_PAR_PAYLOAD, methods=[EPPersonalUserDataUpdate.METHOD])
    def personalUserDataUpdateWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return "Not valid request", EP.CODE_BAD_REQUEST

        out = self.ePPersonalUserDataUpdate.executeByPayload(json_data)
        return out


# === get history of a user ===

    #
    # Gives back the history of a user filtered by the given data
    #
    # curl  --header "Content-Type: application/json" --request GET --data '{ "user_id": 1, "card_id": 1056064754705651379, "limit_days": 5, "limit_records": 5}' http://localhost:80/personal/history/request
    #
    # GET http://localhost:80/personal/history/request
    #      body: {
    #        "user_id": 1,
    #        "card_id": 1056064754705651379,
    #        "limit_days": 5,
    #        "limit_records": 5    
    #      }
    #
    # example:
    #    curl  --header "Content-Type: application/json" --request GET --data '{ "user_id": 1, "card_id": 1056064754705651379, "limit_days": 5, "limit_records": 5}' http://localhost:80/personal/history/request
    #    curl  --header "Content-Type: application/json" --request GET --data '{ "user_id": 1}' http://localhost:80/personal/history/request
    # response:
    #     [
    #       {"start_epoch": 1725117021, "last_epoch": 1725142600, "recent_position": "3.5125", "id_card": 1056064754705651379, "id_user": 1}, 
    #       {"start_epoch": 1725142641, "last_epoch": 1725142641, "recent_position": "43.253", "id_card": 1056064754705651379, "id_user": 1}
    #      ]
    #
    #@route('/history/request', methods=['GET'])
    @route(EPPersonalHistoryRequest.PATH_PAR_PAYLOAD, methods=[EPPersonalHistoryRequest.METHOD])
    def personalHistoryRequestWithPayload(self):

#        print("!!! Inside the personalHistoryRequestWithPayload() !!! {0}".format(request))
#        print("check args: {0}".format(request.args))
#        print("check is_json: {0}".format(request.is_json))
#        print("check form: {0}".format(request.form))

        # CURL
        if request.is_json:
            json_data = request.json
        
        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            user_id = request.args.get('user_id')
            card_id = request.args.get('card_id')
            limit_days = request.args.get('limit_days', None)
            limit_records = request.args.get('limit_records', None)

            json_data = {'user_id': user_id, 'card_id': card_id, 'limit_days': limit_days, 'limit_records': limit_records}

        out = self.ePPersonalHistoryRequest.executeByPayload(json_data)
        return out






# === Updates the media position ===

    #
    # Updates the position of a media
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": 1056064754705651379, "recent_position": 123.4, "start_epoch": 1725117021}' http://localhost:80/personal/history/update
    #
    # POST http://localhost:80/personal/history/update
    #      body: {
    #        "user_id": 1,
    #        "card_id": 1056064754705651379,
    #        "recent_position": 123.2,
    #        "start_epoch": 1725117021   
    #      }
    #
    # example:
    # curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2", "start_epoch": 1725117021}' http://localhost:80/personal/history/update
    # curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2"}' http://localhost:80/personal/history/update
    # response:
    #     1725117021
    #     1725142641
    #
    #@route('/history/update', methods=['POST'])
    @route(EPPersonalHistoryUpdate.PATH_PAR_PAYLOAD, methods=[EPPersonalHistoryUpdate.METHOD])
    def personalHistoryUpdateWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return "Not valid request", EP.CODE_BAD_REQUEST

        out = self.ePPersonalHistoryUpdate.executeByPayload(json_data)
        return out
