import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.representations import output_json

from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.endpoints.ep_personal_user_data_request import EPPersonalUserDataRequest
from homeflix.restserver.endpoints.ep_personal_user_data_update import EPPersonalUserDataUpdate
from homeflix.restserver.endpoints.ep_personal_history_request import EPPersonalHistoryRequest
from homeflix.restserver.endpoints.ep_personal_history_update import EPPersonalHistoryUpdate
from homeflix.restserver.endpoints.ep_personal_rating_update import EPPersonalRatingUpdate
from homeflix.restserver.endpoints.ep_personal_tag_insert import EPPersonalTagInsert
from homeflix.restserver.endpoints.ep_personal_tag_delete import EPPersonalTagDelete
from homeflix.restserver.endpoints.ep_personal_tag_get import EPPersonalTagGet
from homeflix.restserver.endpoints.ep_personal_card_menu_get import EPPersonalCardMenuGet

# -----------------------------------
#
# Personal data
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/user_data/request
# curl  --header "Content-Type: application/json" --request POST --data '{ "password": "****", "language_code": "hu"}' http://localhost:80/personal/user_data/update
#
# curl  --header "Content-Type: application/json" --request GET --data '{ "card_id": 1056064754705651379, "limit_days": 5, "limit_records": 5}' http://localhost:80/personal/history/request
#
# curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2", "start_epoch": 1725117021}' http://localhost:80/personal/history/update
# curl  --header "Content-Type: application/json" --request POST --data '{ "user_id": 1, "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2"}' http://localhost:80/personal/history/update
#
# curl  --header "Content-Type: application/json" --request POST --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "rate": 2, "skip_continuous_play": 0}' http://localhost:80/personal/rating/update
# curl  --header "Content-Type: application/json" --request POST --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "rate": 2}' http://localhost:80/personal/rating/update
# curl  --header "Content-Type: application/json" --request POST --data '{"skip_continuous_play": 0}' http://localhost:80/personal/rating/update
#
# curl  --header "Content-Type: application/json" --request POST --data '{"card_id": "5583062bccde422e47378450068cc5a2", "name": "my_tag"}' http://localhost:80/personal/tag/insert
# curl  --header "Content-Type: application/json" --request DELETE --data '{"card_id": "5583062bccde422e47378450068cc5a2", "name": "my_tag"}' http://localhost:80/personal/tag/delete
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/card_menu/get
# -----------------------------------
#
class PersonalView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epPersonalUserDataRequest = EPPersonalUserDataRequest(web_gadget)
        self.epPersonalUserDataUpdate = EPPersonalUserDataUpdate(web_gadget)
        self.ePPersonalHistoryRequest = EPPersonalHistoryRequest(web_gadget)
        self.ePPersonalHistoryUpdate = EPPersonalHistoryUpdate(web_gadget)
        self.ePPersonalRatingUpdate = EPPersonalRatingUpdate(web_gadget)
        self.ePPersonalTagInsert = EPPersonalTagInsert(web_gadget)
        self.ePPersonalTagDelete = EPPersonalTagDelete(web_gadget)
        self.ePPersonalTagGet = EPPersonalTagGet(web_gadget)
        self.ePPersonalCardMenuGet = EPPersonalCardMenuGet(web_gadget)
    #
    # GET http://localhost:5000/personal/
    #
    def index(self):
        return {}


# === GET data of the recent user ===

    #
    # Gives back all publishable user data of the logged in user
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/user_data/request
    #
    # example:
    #    curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/user_data/request
    # response:
    #   {
    #       language_code: "en"
    #       name: "admin"
    #       is_admin: 1,
    #       play_continuously: 1
    #       show_lyrics_anyway: 1
    #       show_original_title: 1
    #       show_storyline_anyway: 1
    #   }
    #
    #@route('/user_data/request')
    @route(EPPersonalUserDataRequest.PATH_PAR_URL, methods=[EPPersonalUserDataRequest.METHOD])
    def personalUserdata(self):

        out = self.epPersonalUserDataRequest.executeByParameters()
        return out


#=== POST update logged in user ===

    #
    # Update Logged In user data
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{"language_code": "hu"}' http://localhost:80/personal/user_data/update
    #
    # example:
    #    curl  --header "Content-Type: application/json" --request POST --data '{"language_code": "hu"}' http://localhost:80/personal/user_data/update
    # response:
    #     {
    #        "name": "admin",
    #        "language_code": "hu",
    #        "show_original_title": true,
    #        "show_lyrics_anyway": true,
    #        "show_storyline_anyway: true,
    #        "play_continuously: false
    #      }
    #
    #@route('/user_data/update', methods=['POST'])
    @route(EPPersonalUserDataUpdate.PATH_PAR_PAYLOAD, methods=[EPPersonalUserDataUpdate.METHOD])
    def personalUserDataUpdateWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return output_json({'result': False, 'data':{}, 'error': 'Not valid request'}, EP.CODE_BAD_REQUEST)

        out = self.epPersonalUserDataUpdate.executeByPayload(json_data)
        return out


# === get history of a user ===

    #
    # Gives back the history of a user filtered by the given data
    #
    # curl  --header "Content-Type: application/json" --request GET --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "limit_days": 5, "limit_records": 5}' http://localhost:80/personal/history/request
    #
    # GET http://localhost:80/personal/history/request
    #      body: {
    # TODO: remove user_id, repace it with user_name
    #        "card_id": "5583062bccde422e47378450068cc5a2",
    #        "limit_days": 5,
    #        "limit_records": 5
    #      }
    #
    # example:
    #    curl  --header "Content-Type: application/json" --request GET --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "limit_days": 5, "limit_records": 5}' http://localhost:80/personal/history/request
    #    curl  --header "Content-Type: application/json" --request GET --data '{}' http://localhost:80/personal/history/request
    # response:
    #     [
    #       {"start_epoch": 1725117021, "last_epoch": 1725142600, "recent_position": "3.5125", "id_card": "5583062bccde422e47378450068cc5a2", "id_user": 1},
    #       {"start_epoch": 1725142641, "last_epoch": 1725142641, "recent_position": "43.253", "id_card": "5583062bccde422e47378450068cc5a2", "id_user": 1}
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
            card_id = request.args.get('card_id')
            limit_days = request.args.get('limit_days', None)
            limit_records = request.args.get('limit_records', None)
            json_data = {'card_id': card_id, 'limit_days': limit_days, 'limit_records': limit_records}

        out = self.ePPersonalHistoryRequest.executeByPayload(json_data)
        return out






# === Updates the media position ===

    #
    # Updates the position of a media
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": 123.4, "start_epoch": 1725117021}' http://localhost:80/personal/history/update
    #
    # POST http://localhost:80/personal/history/update
    #      body: {
    #        "card_id": "5583062bccde422e47378450068cc5a2",
    #        "recent_position": 123.2,
    #        "start_epoch": 1725117021
    #      }
    #
    # example:
    # curl  --header "Content-Type: application/json" --request POST --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2", "start_epoch": 1725117021}' http://localhost:80/personal/history/update
    # curl  --header "Content-Type: application/json" --request POST --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "recent_position": "536.2"}' http://localhost:80/personal/history/update
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





# === Updates the rating ===

    #
    # Updates the ratings for a card by a user
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{ "card_id": "5583062bccde422e47378450068cc5a2", "rate": 2, "skip_continuous_play": 0}' http://localhost:80/personal/rating/update
    #
    # POST http://localhost:80/personal/rating/update
    #      body: {
    #           "card_id": "5583062bccde422e47378450068cc5a2",
    #           "rate": 2,
    #           "skip_continuous_play": 0
    #      }
    #
    #@route('/rating/update', methods=['POST'])
    @route(EPPersonalRatingUpdate.PATH_PAR_PAYLOAD, methods=[EPPersonalRatingUpdate.METHOD])
    def personalRatingUpdateWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return "Not valid request", EP.CODE_BAD_REQUEST

        out = self.ePPersonalRatingUpdate.executeByPayload(json_data)
        return out



# === Insert the tag ===

    #
    # Insert a tag into card by a user
    #
    # curl  --header "Content-Type: application/json" --request POST --data '{"card_id": "5583062bccde422e47378450068cc5a2", "name": "my_tag"}' http://localhost:80/personal/tag/insert
    #
    # POST http://localhost:80/personal/tag/insert
    #      body: {
    #           "card_id": "5583062bccde422e47378450068cc5a2",
    #           "name": 'my_tag'
    #      }
    #
    #@route('/tag/insert', methods=['POST'])
    @route(EPPersonalTagInsert.PATH_PAR_PAYLOAD, methods=[EPPersonalTagInsert.METHOD])
    def personalTagInsertWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return "Not valid request", EP.CODE_BAD_REQUEST

        out = self.ePPersonalTagInsert.executeByPayload(json_data)
        return out


# === Delete the tag ===

    #
    # Delete a tag from a card by a user
    #
    # curl  --header "Content-Type: application/json" --request DELETE --data '{"card_id": "5583062bccde422e47378450068cc5a2", "name": "my_tag"}' http://localhost:80/personal/tag/delete
    #
    # DELETE http://localhost:80/personal/tag/delete
    #        body: {
    #           "card_id": "5583062bccde422e47378450068cc5a2",
    #           "name": 'my_tag'
    #        }
    #
    #@route('/tag/delete', methods=['DELETE'])
    @route(EPPersonalTagDelete.PATH_PAR_PAYLOAD, methods=[EPPersonalTagDelete.METHOD])
    def personalTagDeleteWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return "Not valid request", EP.CODE_BAD_REQUEST

        out = self.ePPersonalTagDelete.executeByPayload(json_data)
        return out


# === Get tags ===

    #
    # Get tags
    #
    # curl  --header "Content-Type: application/json" --data '{"category":"movie"}' --request GET http://localhost:80/personal/tag/get
    #
    # GET http://localhost:80/personal/tag/get
    #      body: {
    #           category: "movie"
    #           title: "*"
    #           genres: "*"
    #           themes: "*"
    #           directors: "*"
    #           actors: "*"
    #           lecturers: "*"
    #           origins: "*"
    #           decade: "*"
    #           lang: "en"
    #      }
    #@route('/tag/get', methods=['GET'])
    @route(EPPersonalTagGet.PATH_PAR_PAYLOAD, methods=[EPPersonalTagGet.METHOD])
    def personalTagGetWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.ePPersonalTagGet.executeByPayload(json_data)
        return out

    #
    # Get tags
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/tag/get/category/movie/title/*/genres/*/themes/*/directors/*/actors/*/lecturers/*/origin/*/decade/*/lang/en
    #
    # GET http://localhost:80/personal/tag/get/category/movie/title/*/genres/*/themes/*/directors/*/actors/*/lecturers/*/origin/*/decade/*/lang/en
    #
    #@route('/tag/get/category/<category>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/origin/<origin>/decade/<decade>/lang/<lang>', methods=['GET'])
    @route(EPPersonalTagGet.PATH_PAR_URL, methods=[EPPersonalTagGet.METHOD])
    def personalTagGetWithParameters(self, category, title, genres, themes, directors, actors, lecturers, origins, decade, lang):
        out = self.ePPersonalTagGet.executeByParameters(category=category, title=title, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, origins=origins, decade=decade, lang=lang)
        return out



# === Get Card Menu ===

    #
    # Get tags
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/personal/card_menu/get
    #
    #@route('/card_menu/get', methods=['GET'])
    @route(EPPersonalCardMenuGet.PATH_PAR_URL, methods=[EPPersonalCardMenuGet.METHOD])
    def personalCardMenuGetWithParameters(self):
        out = self.ePPersonalCardMenuGet.executeByParameters()
        return out
