import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

from playem.restserver.endpoints.ep_collect_all_series_movies import EPCollectAllSeriesMovies
from playem.restserver.endpoints.ep_collect_standalone_movies_all import EPCollectStandaloneMoviesAll
from playem.restserver.endpoints.ep_collect_standalone_movies_by_genre import EPCollectStandaloneMoviesByGenre
from playem.restserver.endpoints.ep_collect_standalone_movie_by_card_id import EPCollectStandaloneMovieByCardId
from playem.restserver.endpoints.ep_collect_child_hierarchy_or_card import EPCollectChildHierarchyOrCard
from playem.restserver.endpoints.ep_collect_medium_by_card_id import EPCollectMediumByCardId

from playem.restserver.endpoints.ep_collect_general_level import EPCollectGeneralLevel
from playem.restserver.endpoints.ep_collect_general_standalone import EPCollectGeneralStandalone

from playem.restserver.endpoints.ep_collect_standalone_music_audio_by_card_id import EPCollectStandaloneMusicAudioByCardId
from playem.restserver.endpoints.ep_collect_standalone_music_video_by_card_id import EPCollectStandaloneMusicVideoByCardId


# -----------------------------------
#
# GET info
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/all/series/movies
# -----------------------------------
#
# GET http://localhost:80/collect/all/series/movie
class CollectView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epCollectStandaloneMoviesByGenre = EPCollectStandaloneMoviesByGenre(web_gadget)
        self.epCollectMediumByCardId = EPCollectMediumByCardId(web_gadget)

        self.epCollectGeneralLevel = EPCollectGeneralLevel(web_gadget)
        self.epCollectGeneralStandalone = EPCollectGeneralStandalone(web_gadget)

        self.epCollectStandaloneMovieByCardId = EPCollectStandaloneMovieByCardId(web_gadget)
        self.epCollectStandaloneMusicVideoByCardId = EPCollectStandaloneMusicVideoByCardId(web_gadget)
        self.epCollectStandaloneMusicAudioByCardId = EPCollectStandaloneMusicAudioByCardId(web_gadget)

        # --- to delete ---
        self.epCollectChildHierarchyOrCard = EPCollectChildHierarchyOrCard(web_gadget)   #ep_collect_child_hierarchy_or_card.py / view_collection.py
        self.epCollectAllSeriesMovies = EPCollectAllSeriesMovies(web_gadget)             #ep_collect_all_series_movies.py / view_collection
        self.epCollectStandaloneMoviesAll = EPCollectStandaloneMoviesAll(web_gadget)     #pe_collect_standalone_movies_all.py  

    #
    # GET http://localhost:5000/collect/
    #
    def index(self):
        return {}

    # #
    # # Gives back list of records of all series of movies with payload
    # #
    # # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/all/series/movies
    # #
    # # GET http://localhost:80/collect/all/series/movies
    # #
    # #@route('/all/series/movies', methods=['GET'])
    # @route(EPCollectAllSeriesMovies.PATH_PAR_PAYLOAD, methods=[EPCollectAllSeriesMovies.METHOD])
    # def collectAllSeriesMoviesWithPayload(self):

    #     # WEB
    #     if request.form:
    #         json_data = request.form

    #     # CURL
    #     elif request.json:
    #         json_data = request.json

    #     else:
    #         return "Not valid request", EP.CODE_BAD_REQUEST

    #     out = self.epCollectAllSeriesMovies.executeByPayload(json_data)
    #     return out


# === all series of movies ===

    #
    # Gives back list of records of all series of movies with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/all/series/movies/lang/en
    #
    # GET http://localhost:80/collect/all/series/movies
    #
    #@route('/all/series/movies/lang/<lang>')
    @route(EPCollectAllSeriesMovies.PATH_PAR_URL, methods=[EPCollectAllSeriesMovies.METHOD])
    def collectAllSeriesMoviesWithParameter(self, lang):

        out = self.epCollectAllSeriesMovies.executeByParameters(lang=lang)
        return out

# === all series of movies filtered by not_origin ===

# === series movies filtered by genre             ===

# === series movies filtered by theme             ===

# === series movies filtered by origin            ===



# === collect with general filter ===

    #
    # Gives back list of records of all levels with the given parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/level/band/category/music_video/genre/new_wave/theme/*/origin/*/not_origin/*/decade/80s/lang/en
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/level/series/category/movie/genre/drama/theme/life/origin/*/not_origin/hu/decade/*/lang/en
    #
    # GET http://localhost:80/collect/all/series/movies
    #
    #@route('/general/level/<level>/category/<category>/genre/<genre>/theme/<theme>/origin/<origin>/not_origin/<not_origin>/decade/<decade>/lang/<lang>)
    @route(EPCollectGeneralLevel.PATH_PAR_URL, methods=[EPCollectGeneralLevel.METHOD])
    def collectGeneralLevelWithParameter(self, level, category, genre, theme, origin, not_origin, decade, lang):

        out = self.epCollectGeneralLevel.executeByParameters(level, category, genre=genre, theme=theme, origin=origin, not_origin=not_origin, decade=decade, lang=lang)
        return out


    #
    # Gives back list of standalones of all levels with the given parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/standalone/category/movie/genre/drama/theme/*/origin/*/not_origin/*/decade/80s/lang/en
    #
    # GET http://localhost:80/collect/all/series/movies
    #
    #@route('/general/standalone/category/<category>/genre/<genre>/theme/<theme>/origin/<origin>/not_origin/<not_origin>/decade/<decade>/lang/<lang>)
    @route(EPCollectGeneralStandalone.PATH_PAR_URL, methods=[EPCollectGeneralStandalone.METHOD])
    def collectGeneralStandaloneWithParameter(self, category, genre, theme, origin, not_origin, decade, lang):

        out = self.epCollectGeneralStandalone.executeByParameters(category=category, genre=genre, theme=theme, origin=origin, not_origin=not_origin, decade=decade, lang=lang)
        return out














# # === all standalone movies ===

#     #
#     # Gives back list of records of all standalone movies with parameters
#     #
#     # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/standalone/movies/lang/en
#     #
#     # GET http://localhost:80/collect/standalone/movies/lang/en
#     #
#     #@route('/all/standalone/movies/lang/<lang>')
#     @route(EPCollectStandaloneMoviesAll.PATH_PAR_URL, methods=[EPCollectStandaloneMoviesAll.METHOD])
#     def collectStandaloneMoviesAllWithParameter(self, lang):

#         out = self.epCollectStandaloneMoviesAll.executeByParameters(lang=lang)
#         return out


# === standalone movies filtered by genre ===

    #
    # Gives back list of records of standalone movies with genre with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/standalone/movies/genre/drama/lang/en
    #
    # GET http://localhost:80/collect/standalone/movies/genre/drama/lang/en
    #
    #@route('/standalone/movies/genre/<genre>/lang/<lang>')
    @route(EPCollectStandaloneMoviesByGenre.PATH_PAR_URL, methods=[EPCollectStandaloneMoviesByGenre.METHOD])
    def collectStandaloneMoviesByGenreWithParameter(self, genre, lang):

        out = self.epCollectStandaloneMoviesByGenre.executeByParameters(genre=genre, lang=lang)
        return out


# === standalone movie filtered by theme ===
# ????????????














# === standalone media with a specific id ===

    #
    # Gives back a standalone movie with a specific card id
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/standalone/movie/card_id/123/lang/en
    #
    # GET http://localhost:80/collect/standalone/movie/card_id/123/lang/en
    #
    #@route('/standalone/movie/card_id/<card_id>/lang/<lang>')
    @route(EPCollectStandaloneMovieByCardId.PATH_PAR_URL, methods=[EPCollectStandaloneMovieByCardId.METHOD])
    def collectStandaloneMovieByCardIdWithParameter(self, card_id, lang):

        out = self.epCollectStandaloneMovieByCardId.executeByParameters(card_id=card_id, lang=lang)
        return out


    #
    # Gives back a video music with a specific card id
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/standalone/music_video/card_id/123/lang/en
    #
    # GET http://localhost:80/collect/standalone/music_video/card_id/123/lang/en
    #
    #@route('/standalone/music_video/card_id/<card_id>/lang/<lang>')
    @route(EPCollectStandaloneMusicVideoByCardId.PATH_PAR_URL, methods=[EPCollectStandaloneMusicVideoByCardId.METHOD])
    def collectStandaloneMusicVideoByCardIdWithParameter(self, card_id, lang):

        out = self.epCollectStandaloneMusicVideoByCardId.executeByParameters(card_id=card_id, lang=lang)
        return out

    #
    # Gives back a audio music with a specific card id
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/standalone/music_audio/card_id/123/lang/en
    #
    # GET http://localhost:80/collect/standalone/music_audio/card_id/123/lang/en
    #
    #@route('/standalone/music_audio/card_id/<card_id>/lang/<lang>')
    @route(EPCollectStandaloneMusicAudioByCardId.PATH_PAR_URL, methods=[EPCollectStandaloneMusicAudioByCardId.METHOD])
    def collectStandaloneMusicAudioByCardIdWithParameter(self, card_id, lang):

        out = self.epCollectStandaloneMusicAudioByCardId.executeByParameters(card_id=card_id, lang=lang)
        return out








# === all child card of a specific hirarchy card ===

    #
    # Gives back child Hiearchy of the given hierarchy id. If the child hierarchy is Card
    # then it gives back the child Cards
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/child_hierarchy_or_card/id/123/lang/en
    #
    # GET http://localhost:80/collect/child_hierarchy_or_card/id/123/lang/en
    #
    #@route('//id/<id>/lang/<lang>')
    @route(EPCollectChildHierarchyOrCard.PATH_PAR_URL, methods=[EPCollectChildHierarchyOrCard.METHOD])
    def collectChildHierarchyOrCardWithParameter(self, id, lang):

        out = self.epCollectChildHierarchyOrCard.executeByParameters(id=id, lang=lang)
        return out


# === medium list of a specific card ===

    #
    # Gives back the medium list of the given Card.
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/medium/card_id/33
    #
    # GET http://localhost:80/collect/medium/card_id/33
    #@route('/medium/card_id/<card_id>')
    @route(EPCollectMediumByCardId.PATH_PAR_URL, methods=[EPCollectMediumByCardId.METHOD])
    def collectMediumByCardId(self, card_id):

        out = self.epCollectMediumByCardId.executeByParameters(card_id=card_id)
        return out


