import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.representations import output_json


from homeflix.restserver.endpoints.ep_collect_highest_mixed_card import EPCollectHighestMixed
from homeflix.restserver.endpoints.ep_collect_next_mixed_card import EPCollectNextMixed
from homeflix.restserver.endpoints.ep_collect_lowest_card import EPCollectLowest

# ---

from homeflix.restserver.endpoints.ep_collect_media_by_card_id import EPCollectMediaByCardId

#from homeflix.restserver.endpoints.ep_collect_standalone_movies_by_genre import EPCollectStandaloneMoviesByGenre
from homeflix.restserver.endpoints.ep_collect_medium_by_card_id import EPCollectMediumByCardId

from homeflix.restserver.endpoints.ep_collect_child_hierarchy_or_card import EPCollectChildHierarchyOrCard

from homeflix.restserver.endpoints.ep_collect_general_level import EPCollectGeneralLevel
from homeflix.restserver.endpoints.ep_collect_general_standalone import EPCollectGeneralStandalone

from homeflix.restserver.endpoints.ep_collect_all_appendix_by_card_id import EPCollectAllAppendixByCardId
from homeflix.restserver.endpoints.ep_collect_actors_by_role_count import EPCollectActorsByRoleCount
from homeflix.restserver.endpoints.ep_collect_directors_by_movie_count import EPCollectDirectorsByMovieCount
from homeflix.restserver.endpoints.ep_collect_abc_by_movie_title_count import EPCollectAbcByMovieTitleCount



# -----------------------------------
#
# GET info
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/highest/mixed/category/<category>/level/<level>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/origins/<origins>/decade/<decade>/lang/<lang>
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/next/mixed/card_id/<card_id>/category/<category>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/origins/<origins>/decade/<decade>/lang/<lang>
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/lowest/category/<category>/playlist/<playlist>/tags{tags}/level/<level>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/origins/<origins>/decade/<decade>/lang/<lang>
#
#
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/level/band/category/music_video/genre/new_wave/theme/*/origin/*/decade/80s/lang/en
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/standalone/category/movie/genre/drama/theme/*/director/*/actor/*/origin/*/decade/80s/lang/en
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/child_hierarchy_or_card/id/123/lang/en
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/standalone/movies/genre/drama/lang/en
#
# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/all/appendix/card_id/123/lang/en

# curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/media/card_id/123/lang/en
#

# -----------------------------------
#
class CollectView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epCollectMediumByCardId = EPCollectMediumByCardId(web_gadget)

# ---

        self.epCollectGeneralLevel = EPCollectGeneralLevel(web_gadget)
        self.epCollectGeneralStandalone = EPCollectGeneralStandalone(web_gadget)
        self.epCollectChildHierarchyOrCard = EPCollectChildHierarchyOrCard(web_gadget)
        self.epCollectMediaByCardId = EPCollectMediaByCardId(web_gadget)
        self.epCollectAllAppendixByCardId = EPCollectAllAppendixByCardId(web_gadget)
        self.epCollectActorsByRoleCount = EPCollectActorsByRoleCount(web_gadget)
        self.epCollectDirectorsByMovieCount = EPCollectDirectorsByMovieCount(web_gadget)
        self.epCollectAbcByMovieTitleCount = EPCollectAbcByMovieTitleCount(web_gadget)

# ---

        self.epCollectHighestMixed = EPCollectHighestMixed(web_gadget)
        self.epCollectNextMixed = EPCollectNextMixed(web_gadget)
        self.epCollectLowest = EPCollectLowest(web_gadget)


    #
    # GET http://localhost:5000/collect/
    #
    def index(self):
        return {}


# === collect with general filter on the highest level ===

    #
    # Gives back filtered list of mixed records of the highest levels
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/highest/mixed/category/<category>/playlist/<playlist>/tags{tags}/level/<level>/filter_on/<filter_on>/title/<title>/genre/<genre>/theme/<theme>/director/<director>/actor/<actor>/lecturer/<lecturer>/performers/<performers>/origin/<origin>/decade/<decade>/lang/<lang>
    #
    # playlist:
    #   - *
    #   - interrupted
    #   - last_watched
    #   - least_watched
    #   - most_watched
    #
    # level:
    #   - *:        highest level to show
    #   - ^:        highest level to show
    #   - level:    given level to show
    #
    # filter_on:
    #   - *:        filter on the lowest level
    #   - v:        filter on the lowest level
    #   - -:        filter on the given level
    #
    #@route('/highest/mixed/category/<category>/playlist/<playlist>/tags{tags}/level/<level>/filter_on/<filter_on>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/performers/<performers>/origins/<origins>/decade/<decade>/lang/<lang>')
    @route(EPCollectHighestMixed.PATH_PAR_URL, methods=[EPCollectHighestMixed.METHOD])
    def collectHighestMixedWithParameter(self, category, playlist, tags, level, filter_on, title, genres, themes, directors, actors, lecturers, performers, origins, decade, lang):

        out = self.epCollectHighestMixed.executeByParameters(category, playlist=playlist, tags=tags, level=level, filter_on=filter_on, title=title, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, performers=performers, origins=origins, decade=decade, lang=lang)
        return out

    #
    # Gives back filtered list of mixed records of the highest levels
    #
    # curl -b cookies.txt --header "Content-Type: application/json" --request GET --data '{"category":"music_video", "performers": "A%"}' http://localhost:80/collect/highest/mixed
    #
    # GET http://localhost:80/collect/highest/mixed
    #      body: {
    #       "category": "movei",
    #       "playlist": "*",
    #       "tags": "*",
    #       "level": "*",
    #       "filter_on": "*"
    #       "title": "*",
    #       "genres": "*",
    #       "themes": "*",
    #       "directors": "*",
    #       "actors": "*",
    #       "lecturers": "*",
    #       "performers": "*",
    #       "origins": "*",
    #       "decade": "*",
    #       "lang": "en"
    #      }
    #
    # playlist:
    #   - *
    #   - interrupted
    #   - last_watched
    #   - least_watched
    #   - most_watched
    #
    # level:
    #   - *:        highest level to show
    #   - ^:        highest level to show
    #   - level:    given level to show
    #
    # filter_on:
    #   - *:        filter on the lowest level
    #   - v:        filter on the lowest level
    #   - -:        filter on the given level
    #

    #@route('/highest/mixed', methods=['GET'])
    @route(EPCollectHighestMixed.PATH_PAR_PAYLOAD, methods=[EPCollectHighestMixed.METHOD])
    def collectHighestWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.epCollectHighestMixed.executeByPayload(json_data)
        return out









# === collect with general filter on the next level ===

    #
    # Gives back filtered list of mixed records of the next levels
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/next/mixed/card_id/<card_id>/category/<category>/playlist/<playlist>/tags{tags}/level/<level>/filter_on/<filter_on>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/performers/<performers>/origin/<origin>/decade/<decade>/lang/<lang>
    #
    #@route('/highest/mixed/card_id/<card_id>/category/<category>/playlist/<playlist>/tags{tags}/level/<level>/filter_on/<filter_on>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/performers/<performers>/origins/<origins>/decade/<decade>/lang/<lang>')
    @route(EPCollectNextMixed.PATH_PAR_URL, methods=[EPCollectNextMixed.METHOD])
    def collectNextMixedWithParameter(self, card_id, category, playlist, tags, level, filter_on, title, genres, themes, directors, actors, lecturers, performers, origins, decade, lang):

        out = self.epCollectNextMixed.executeByParameters(card_id, category, playlist=playlist, tags=tags, level=level, filter_on=filter_on, title=title, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, performers=performers, origins=origins, decade=decade, lang=lang)
        return out

    #
    # Gives back filtered list of mixed records of the next levels
    #
    # curl -b cookies.txt --header "Content-Type: application/json" --request GET --data '{"category":"movie", "performers": "A%"}' http://localhost:80/collect/next/mixed
    #
    # GET http://localhost:80/collect/next/mixed
    #      body: {
    #       "card_id": "38cf4c285e64e737ec58b39c610d842a"
    #       "category": "movei",
    #       "playlist": "*",
    #       "tags": "*",
    #       "level": "*",
    #       "filter_on": "*",
    #       "title": "*",
    #       "genres": "*",
    #       "themes": "*",
    #       "directors": "*",
    #       "actors": "*",
    #       "lecturers": "*",
    #       "performers": "*",
    #       "origins": "*",
    #       "decade": "*",
    #       "lang": "en"
    #      }
    #
    # playlist:
    #   - *
    #   - interrupted
    #   - last_watched
    #   - least_watched
    #   - most_watched

    #@route('/next/mixed', methods=['GET'])
    @route(EPCollectNextMixed.PATH_PAR_PAYLOAD, methods=[EPCollectNextMixed.METHOD])
    def collectNextWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.epCollectNextMixed.executeByPayload(json_data)
        return out













# === collect with general filter on the lowest level ===

    #
    # Gives back filtered list of the lowest levels
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/lowest/category/<category>/playlist/<playlist>/tags{tags}/level/<level>/genre/<genre>/theme/<theme>/director/<director>/actor/<actor>/lecturer/<lecturer>/performers/<performers>/origin/<origin>/decade/<decade>/lang/<lang>
    #
    # playlist:
    #   - *
    #   - interrupted
    #   - last_watched
    #   - least_watched
    #   - most_watched
    #@route('/lowest/category/<category>/playlist/<playlist>/tags{tags}/level/<level>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/performers/<performers>/origins/<origins>/decade/<decade>/lang/<lang>')
    @route(EPCollectLowest.PATH_PAR_URL, methods=[EPCollectLowest.METHOD])
    def collectLowestWithParameter(self, category, playlist, tags, level, title, genres, themes, directors, actors, lecturers, performers, origins, decade, lang):
        out = self.epCollectLowest.executeByParameters(category, playlist=playlist, tags=tags, level=level, title=title, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, performers=performers, origins=origins, decade=decade, lang=lang)
        return out

    #
    # Gives back filtered list of the lowest levels
    #
    # curl  --header "Content-Type: application/json" --request GET --data '{"category": "movie", "playlist": "*", "tags": "*", "level": "*", "title": "*", "genres": "*", "themes": "*", "directors": "*", "actors": "*", "lecturers": "*", "performers": "*", "origins": "*", "decade": "*", "lang": "en"}' http://localhost:80/collect/lowest
    #
    # GET http://localhost:80/collect/lowest
    #      body: {
    #       "category": "movei",
    #       "playlist": "*",
    #       "tags": "*",
    #       "level": "*",
    #       "title": "*",
    #       "genres": "*",
    #       "themes": "*",
    #       "directors": "*",
    #       "actors": "*",
    #       "lecturers": "*",
    #       "origins": "*",
    #       "decade": "*",
    #       "lang": "en"
    #      }
    #
    # playlist:
    #   - *
    #   - interrupted
    #   - last_watched
    #   - least_watched
    #   - most_watched

    #@route('/lowest', methods=['GET'])
    @route(EPCollectLowest.PATH_PAR_PAYLOAD, methods=[EPCollectLowest.METHOD])
    def collectLowestWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.epCollectLowest.executeByPayload(json_data)
        return out



# === series movies filtered by genre             ===

# === series movies filtered by theme             ===

# === series movies filtered by origin            ===



# === collect with general filter ===

    #
    # Gives back list of records of all levels with the given parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/level/band/category/music_video/genre/new_wave/theme/*/origin/*/decade/80s/lang/en
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/level/series/category/movie/genre/drama/theme/life/origin/*/hu/decade/*/lang/en
    #
    # GET http://localhost:80/collect/all/series/movies
    #
    #@route('/general/level/<level>/category/<category>/genre/<genre>/theme/<theme>/origin/<origin>/decade/<decade>/lang/<lang>)
    @route(EPCollectGeneralLevel.PATH_PAR_URL, methods=[EPCollectGeneralLevel.METHOD])
    def collectGeneralLevelWithParameter(self, level, category, genre, theme, origin, decade, lang):

        out = self.epCollectGeneralLevel.executeByParameters(level, category, genre=genre, theme=theme, origin=origin, decade=decade, lang=lang)
        return out


    #
    # Gives back list of standalones of all levels with the given parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/general/standalone/category/movie/genre/drama/theme/*/director/*/actor/*/origin/*/decade/80s/lang/en
    #
    # GET http://localhost:80/collect/all/series/movies
    #
    #@route('/general/standalone/category/<category>/genre/<genre>/theme/<theme>/director/<director>/actor/<actor>/origin/<origin>/decade/<decade>/lang/<lang>)
    @route(EPCollectGeneralStandalone.PATH_PAR_URL, methods=[EPCollectGeneralStandalone.METHOD])
    def collectGeneralStandaloneWithParameter(self, category, genre, theme, director, actor, origin, decade, lang):
        out = self.epCollectGeneralStandalone.executeByParameters(category=category, genre=genre, theme=theme, director=director, actor=actor, origin=origin, decade=decade, lang=lang)
        return out


# === all child card of a specific hirarchy card ===

    #
    # Gives back the next lower level of the specific card
    # It could be a media-card or level-card as well, we do not know that before we search for it
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


## === standalone movies filtered by genre ===
#
#    #
#    # Gives back list of records of standalone movies with genre with parameters
#    #
#    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/standalone/movies/genre/drama/lang/en
#    #
#    # GET http://localhost:80/collect/standalone/movies/genre/drama/lang/en
#    #
#    #@route('/standalone/movies/genre/<genre>/lang/<lang>')
#    @route(EPCollectStandaloneMoviesByGenre.PATH_PAR_URL, methods=[EPCollectStandaloneMoviesByGenre.METHOD])
#    def collectStandaloneMoviesByGenreWithParameter(self, genre, lang):
#
#        out = self.epCollectStandaloneMoviesByGenre.executeByParameters(genre=genre, lang=lang)
#        return out


# === appendix filtered by card_id ===

    #
    # Gives back all appendix of a specific card id
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/all/appendix/card_id/123/lang/en
    #
    # GET http://localhost:80/collect/all/appendix/card_id/123/lang/en
    #
    #@route('/all/appendix/card_id/<card_id>/lang/<lang>')
    @route(EPCollectAllAppendixByCardId.PATH_PAR_URL, methods=[EPCollectAllAppendixByCardId.METHOD])
    def collectAllAppendixByCardIdWithParameter(self, card_id, lang):

        out = self.epCollectAllAppendixByCardId.executeByParameters(card_id=card_id, lang=lang)
        return out


# === one card with a specific card_id ===

    #
    # Gives back any media with a specific card id
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/media/card_id/123/lang/en
    #
    # GET http://localhost:80/collect/media/card_id/123/lang/en
    #
    #@route('/media/card_id/<card_id>/lang/<lang>')
    @route(EPCollectMediaByCardId.PATH_PAR_URL, methods=[EPCollectMediaByCardId.METHOD])
    def collectStandaloneMediaByCardIdWithParameter(self, card_id, lang):

        out = self.epCollectMediaByCardId.executeByParameters(card_id=card_id, lang=lang)
        return out






# === collect actors by role count descending ===

    #
    # Gives back list of the highest role count of actors
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/actors/by/role/count/category/<category>/minimum/<minimum>/limit/<limit>
    #
    #@route('/actors/by/role/count/category/<category>/minimum/<minimum>/limit/<limit>')
    @route(EPCollectActorsByRoleCount.PATH_PAR_URL, methods=[EPCollectActorsByRoleCount.METHOD])
    def collectActorsWithParameter(self, category, minimum, limit):
        out = self.epCollectActorsByRoleCount.executeByParameters(category, minimum=minimum, limit=limit)
        return out

    #
    # Gives back list of the highest role count of actors
    #
    # curl  --header "Content-Type: application/json" --request GET --data '{"category": "movie", "minimum": 3, "limit": 15}' http://localhost:80/collect/actors/by/role/count
    #
    # GET http://localhost:80/collect/actors/by/role/count
    #      body: {
    #       "category": "movei",
    #       "minimum": 3,
    #       "limit": 15,
    #      }
    #
    #@route('/actors/by/role/count', methods=['GET'])
    @route(EPCollectActorsByRoleCount.PATH_PAR_PAYLOAD, methods=[EPCollectActorsByRoleCount.METHOD])
    def collectActorsWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.epCollectActorsByRoleCount.executeByPayload(json_data)
        return out


# === collect directors by movie count descending ===

    #
    # Gives back list of the highest movie count of directors
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/directors/by/movie/count/category/<category>/minimum/<minimum>/limit/<limit>
    #
    #@route('/directors/by/movie/count/category/<category>/minimum/<minimum>/limit/<limit>')
    @route(EPCollectDirectorsByMovieCount.PATH_PAR_URL, methods=[EPCollectDirectorsByMovieCount.METHOD])
    def collectDirectorsWithParameter(self, category, minimum, limit):
        out = self.EPCollectDirectorsByMovieCount.executeByParameters(category, minimum=minimum, limit=limit)
        return out

    #
    # Gives back list of the highest movie count of directors
    #
    # curl  --header "Content-Type: application/json" --request GET --data '{"category": "movie", "minimum": 3, "limit": 15}' http://localhost:80/collect/directors/by/movie/count
    #
    # GET http://localhost:80/collect/directors/by/movie/count
    #      body: {
    #       "category": "movie",
    #       "minimum": 3,
    #       "limit": 15,
    #      }
    #
    #@route('/directors/by/movie/count', methods=['GET'])
    @route(EPCollectDirectorsByMovieCount.PATH_PAR_PAYLOAD, methods=[EPCollectDirectorsByMovieCount.METHOD])
    def collectDirectorsWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.epCollectDirectorsByMovieCount.executeByPayload(json_data)
        return out


# === collect ABC by movie title count ===

    #
    # Gives back abc of the highest movie title count
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/abc/by/movie_title/count/category/<category>/maximum/<aximum>/lang/<lang>
    #
    #@route('/abc/by/movie_title/count/category/<category>/maximum/<maximum>/lang/<lang>')
    @route(EPCollectAbcByMovieTitleCount.PATH_PAR_URL, methods=[EPCollectAbcByMovieTitleCount.METHOD])
    def collectAbcByMovieTitleWithParameter(self, category, maximum, lang):
        out = self.EPCollectAbcByMovieTitleCount.executeByParameters(category, maximum=maximum)
        return out

    #
    # Gives back list of the highest movie title count
    #
    # curl  --header "Content-Type: application/json" --request GET --data '{"category": "movie", "minimum": 3, "limit": 15}' http://localhost:80/collect/abc/by/movie_title/count
    #
    # GET http://localhost:80/collect/abc/by/movie_title/count
    #      body: {
    #       "category": "movie",
    #       "maximum": 15,
    #       "lang": "en"
    #      }
    #
    #@route('/abc/by/movie_title/count', methods=['GET'])
    @route(EPCollectAbcByMovieTitleCount.PATH_PAR_PAYLOAD, methods=[EPCollectAbcByMovieTitleCount.METHOD])
    def collectAbcByMovieTitleWithPayload(self):
        # CURL
        if request.is_json:
            json_data = request.json

        # WEB
        elif request.form:
            json_data = request.form

        # ajax
        else:
            json_data = request.args

        out = self.epCollectAbcByMovieTitleCount.executeByPayload(json_data)
        return out