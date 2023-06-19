import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

from playem.restserver.endpoints.ep_collect_all_series_movies import EPCollectAllSeriesMovies
from playem.restserver.endpoints.ep_collect_all_standalone_movies import EPCollectAllStandaloneMovies
from playem.restserver.endpoints.ep_collect_child_hierarchy_or_card import EPCollectChildHierarchyOrCard

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

        self.epCollectAllSeriesMovies = EPCollectAllSeriesMovies(web_gadget)
        self.epCollectAllStandaloneMovies = EPCollectAllStandaloneMovies(web_gadget)
        self.epCollectChildHierarchyOrCard = EPCollectChildHierarchyOrCard(web_gadget)


    #
    # GET http://localhost:5000/collect/
    #
    def index(self):
        return {}

    #
    # Gives back list of records of all series of movies with payload
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/all/series/movies
    #
    # GET http://localhost:80/collect/all/series/movies
    #
    #@route('/all/series/movies', methods=['GET'])
    @route(EPCollectAllSeriesMovies.PATH_PAR_PAYLOAD, methods=[EPCollectAllSeriesMovies.METHOD])
    def collectAllSeriesMoviesWithPayload(self):

        # WEB
        if request.form:
            json_data = request.form

        # CURL
        elif request.json:
            json_data = request.json

        else:
            return "Not valid request", EP.CODE_BAD_REQUEST

        out = self.epCollectAllSeriesMovies.executeByPayload(json_data)
        return out

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

# ===

    #
    # Gives back list of records of all standalone movies with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/collect/all/standalone/movies/lang/en
    #
    # GET http://localhost:80/collect/all/standalone/movies/lang/en
    #
    #@route('/all/standalone/movies/lang/<lang>')
    @route(EPCollectAllStandaloneMovies.PATH_PAR_URL, methods=[EPCollectAllStandaloneMovies.METHOD])
    def collectAllStandaloneMoviesWithParameter(self, lang):

        out = self.epCollectAllStandaloneMovies.executeByParameters(lang=lang)
        return out

# ===

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




