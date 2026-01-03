import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.representations import output_json

from homeflix.restserver.endpoints.ep import EP

from homeflix.restserver.endpoints.ep_stream_media_get import EPStreamMediaGet
from homeflix.restserver.endpoints.ep_stream_subtitle_get import EPStreamSubtitleGet

# -----------------------------------
#
# Personal data
#
# curl  --header "Content-Type: application/json" --data '{"card_id": "123", "audio_track": "0", subtitle_track": "0"}' --request GET http://localhost:80/stream/media/get
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/stream/media/get/card_id/123/audio_track/0/subtitle_track/0
#
# curl  --header "Content-Type: application/json" --data '{"card_id": "123", "subtitle_track": "0"}' --request GET http://localhost:80/stream/subtitle/get
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/stream/subtitle/get/card_id/123/subtitle_track/0
#
# -----------------------------------
#
class StreamView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.ePStreamMediaGet = EPStreamMediaGet(web_gadget)
        self.ePStreamSubtitleGet = EPStreamSubtitleGet(web_gadget)

    #
    # GET http://localhost:5000/personal/
    #
    def index(self):
        return {}




# === Get Stream media ===

    #
    # Get stream media
    #
    # curl  --header "Content-Type: application/json" --data '{"card_id": "123", "audio_track": "0"}' --request GET http://localhost:80/stream/media/get
    #
    # GET http://localhost:80/stream/media/get
    #      body: {
    #           "card_id": "123",
    #           "audio_track": "0"
    #      }
    #@route('/media/get', methods=['GET'])
    @route(EPStreamMediaGet.PATH_PAR_PAYLOAD, methods=[EPStreamMediaGet.METHOD])
    def streamMediaGetWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.ePStreamMediaGet.executeByPayload(json_data)
        return out

    #
    # Get stream media
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/stream/media/get/card_id/123/audio_track/0
    #
    # GET http://localhost:80/stream/media/get/card_id/123/audio_track/0
    #
    #@route('/media/get/card_id/<card_id>/audio_track/<audio_track>)
    @route(EPStreamMediaGet.PATH_PAR_URL, methods=[EPStreamMediaGet.METHOD])
    def streamMediaGetWithParameters(self, card_id, audio_track):
        out = self.ePStreamMediaGet.executeByParameters(card_id=card_id, audio_track=audio_track)
        return out


# === Get Stream subtitle ===

    #
    # Get stream subtitle
    #
    # curl  --header "Content-Type: application/json" --data '{"card_id": "123", "subtitle_track": "0"}' --request GET http://localhost:80/stream/subtitle/get
    #
    # GET http://localhost:80/stream/subtitle/get
    #      body: {
    #           "card_id": "123",
    #           "subtitle_track": "0"
    #      }
    #@route('/subtitle/get', methods=['GET'])
    @route(EPStreamSubtitleGet.PATH_PAR_PAYLOAD, methods=[EPStreamSubtitleGet.METHOD])
    def streamSubtitleGetWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.ePStreamSubtitleGet.executeByPayload(json_data)
        return out

    #
    # Get stream media
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/stream/subtitle/get/card_id/123/subtitle_track/0
    #
    # GET http://localhost:80/stream/subtitle/get/card_id/123/subtitle_track/0
    #
    #@route('/media/get/card_id/<card_id>/subtitle_track/<subtitle_track)
    @route(EPStreamSubtitleGet.PATH_PAR_URL, methods=[EPStreamSubtitleGet.METHOD])
    def streamSubtitleGetWithParameters(self, card_id, subtitle_track):
        out = self.ePStreamSubtitleGet.executeByParameters(card_id=card_id, subtitle_track=subtitle_track)
        return out




