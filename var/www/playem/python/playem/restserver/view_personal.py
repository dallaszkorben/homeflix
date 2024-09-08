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
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/history/request/by/user_id/<user_id>/card_id/<card_id>/limit_days/<limit_days>/limit_records/<limit_records>
# curl  --header "Content-Type: application/json" --request GET --data '{ "user_id": 1, "card_id": 1056064754705651379, "limit_days": 5, "limit_records": 5}' http://localhost:80/personal/history/request
#
# curl  --header "Content-Type: application/json" --request POST http://localhost:80/personal/history/update/by/user_id/<user_id>/card_id/<card_id>/last_position/<last_position>/start_epoch/<start_epoch>
# curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": 1056064754705651379, "last_position": "1:48:12", "start_epoch": 1725117021}' http://localhost:80/personal/history/update
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
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/history/request/by/user_id/<user_id>/card_id/<card_id>/limit_days/<limit_days>/limit_records/<limit_records>
    #
    # example:
    #     curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/history/request/by/user_id/1/card_id/1056064754705651379/limit_days/1/limit_records/1
    # response:
    #     [
    #       {"start_epoch": 1725117021, "last_epoch": 1725142600, "last_position": "1:48:12", "id_card": 1056064754705651379, "id_user": 1}, 
    #       {"start_epoch": 1725142641, "last_epoch": 1725142641, "last_position": "0:01:31", "id_card": 1056064754705651379, "id_user": 1}
    #      ]
    #
    #@route('/history/request/by/user_id/<user_id>/card_id/<card_id>/limit_days/<limit_days>/limit_records/<limit_records>')
    @route(EPPersonalHistoryRequest.PATH_PAR_URL, methods=[EPPersonalHistoryRequest.METHOD])
    def personalHistoryRequestByWithParameter(self, user_id, card_id, limit_days, limit_records):

        out = self.ePPersonalHistoryRequest.executeByParameters(user_id, card_id=card_id, limit_days=limit_days, limit_records=limit_records)
        return out

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
    #       {"start_epoch": 1725117021, "last_epoch": 1725142600, "last_position": "1:48:12", "id_card": 1056064754705651379, "id_user": 1}, 
    #       {"start_epoch": 1725142641, "last_epoch": 1725142641, "last_position": "0:01:31", "id_card": 1056064754705651379, "id_user": 1}
    #      ]
    #
    #@route('/history/request', methods=['POST'])
    @route(EPPersonalHistoryRequest.PATH_PAR_PAYLOAD, methods=[EPPersonalHistoryRequest.METHOD])
    def personalHistoryRequestWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return "Not valid request", EP.CODE_BAD_REQUEST

        out = self.ePPersonalHistoryRequest.executeByPayload(json_data)
        return out


# === Updates the media position ===

    #
    # Updates the position of a media
    #
    # curl  --header "Content-Type: application/json" --request POST http://localhost:80/personal/history/update/by/user_id/<user_id>/card_id/<card_id>/last_position/<last_position>/start_epoch/<start_epoch>
    #
    # example:
    #     curl  --header "Content-Type: application/json" --request POST http://localhost:80/personal/history/update/by/user_id/1/card_id/1056064754705651379/last_position/1:23:52/start_epoch/1725117021
    # response:
    #     1725117021
    #
    #@route('/history/update/by/user_id/<user_id>/card_id/<card_id>/last_position/<last_position>/start_epoch/<start_epoch>')
    @route(EPPersonalHistoryUpdate.PATH_PAR_URL, methods=[EPPersonalHistoryUpdate.METHOD])
    def personalHistoryUpdateByWithParameter(self, user_id, card_id, last_position, start_epoch):

        out = self.ePPersonalHistoryUpdate.executeByParameters(user_id, card_id=card_id, last_position=last_position, start_epoch=start_epoch)
        return out


    #
    # Updates the position of a media
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": 1056064754705651379, "last_position": "1:48:12", "start_epoch": 1725117021}' http://localhost:80/personal/history/update
    #
    # GET http://localhost:80/personal/history/update
    #      body: {
    #        "user_id": 1,
    #        "card_id": 1056064754705651379,
    #        "last_position": "1:48:12",
    #        "start_epoch": 1725117021   
    #      }
    #
    # example:
    #    curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": 1056064754705651379, "last_position": "1:48:12", "start_epoch": 1725117021}' http://localhost:80/personal/history/update
    #    curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": 1056064754705651379, "last_position": "0:01:31"}' http://localhost:80/personal/history/update
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
