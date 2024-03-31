import json

from flask import Flask
from flask import jsonify
from flask import session
from flask_classful import FlaskView, route, request

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.representations import output_json

from playem.restserver.endpoints.ep_translate_genre import EPTranslateGenre
from playem.restserver.endpoints.ep_translate_genres import EPTranslateGenres
from playem.restserver.endpoints.ep_translate_titles import EPTranslateTitles
from playem.restserver.endpoints.ep_translate_categories import EPTranslateCategories
from playem.restserver.endpoints.ep_translate_themes import EPTranslateThemes
from playem.restserver.endpoints.ep_translate_levels import EPTranslateLevels


# -----------------------------------
#
# GET Translate
#
# -----------------------------------
#
class TranslateView(FlaskView):
    inspect_args = False

    def __init__(self, web_gadget):

        self.web_gadget = web_gadget

        self.epTranslateGenre = EPTranslateGenre(web_gadget)
        self.epTranslateGenres = EPTranslateGenres(web_gadget)
        self.epTranslateTitles = EPTranslateTitles(web_gadget)
        self.epTranslateCategories = EPTranslateCategories(web_gadget)
        self.epTranslateThemes = EPTranslateThemes(web_gadget)
        self.epTranslateLevels = EPTranslateLevels(web_gadget)

    #
    # GET http://localhost:5000/translate/
    #
    def index(self):
        return {}

    #
    # Gives back translation of a genre with payload
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/translate/genre
    #
    # GET http://localhost:80/translate/genre/drama/lang/en
    #
    #@route('/translate/genre', methods=['GET'])


    # @route(EPTranslateGenre.PATH_PAR_PAYLOAD, methods=[EPTranslateGenre.METHOD])
    # def translateGenreWithPayload(self):

    #     # WEB
    #     if request.form:
    #         json_data = request.form

    #     # CURL
    #     elif request.json:
    #         json_data = request.json

    #     else:
    #         return "Not valid request", EP.CODE_BAD_REQUEST

    #     out = self.epTranslateGenre.executeByPayload(json_data)
    #     return out



    #
    # Gives back translation of a genre with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/translate/genre/drama/category/movie/lang/en
    #
    # GET http://localhost:80/translate/genre/drama/category/movie/lang/en
    #
    #@route('/genre/<genre>/category/<movie>/lang/<lang>')
    @route(EPTranslateGenre.PATH_PAR_URL, methods=[EPTranslateGenre.METHOD])
    def translateGenreWithParameter(self, genre, category, lang):        
        out = self.epTranslateGenre.executeByParameters(category=category, genre=genre, lang=lang)
        return out

    #
    # Gives back translation of all genre with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/translate/genres/category/movie/lang/en
    #
    # GET http://localhost:80/translate/genres/category/movie/lang/en
    #
    #@route('/genres/category/<movie>/lang/<lang>')
    @route(EPTranslateGenres.PATH_PAR_URL, methods=[EPTranslateGenres.METHOD])
    def translateGenresWithParameter(self, category, lang):        
        out = self.epTranslateGenres.executeByParameters(category=category, lang=lang)
        return out


    #
    # Gives back translation of all themes
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/translate/themes/lang/en
    #
    # GET http://localhost:80/translate/themes/movie/lang/en
    #
    #@route('/themes/lang/<lang>')
    @route(EPTranslateThemes.PATH_PAR_URL, methods=[EPTranslateThemes.METHOD])
    def translateThemesWithParameter(self, lang):        
        out = self.epTranslateThemes.executeByParameters(lang=lang)
        return out
    

    #
    # Gives back translation of all titles with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/translate/titles/lang/en
    #
    # GET http://localhost:80/translate/titles/lang/en
    #
    #@route('/titles/lang/<lang>')
    @route(EPTranslateTitles.PATH_PAR_URL, methods=[EPTranslateTitles.METHOD])
    def translateTitlesWithParameter(self, lang):        
        out = self.epTranslateTitles.executeByParameters(lang=lang)
        return out

    #
    # Gives back translation of all categories with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/translate/categories/lang/en
    #
    # GET http://localhost:80/translate/categories/lang/en
    #
    #@route('/categories/lang/<lang>')
    @route(EPTranslateCategories.PATH_PAR_URL, methods=[EPTranslateCategories.METHOD])
    def translateCategoriesWithParameter(self, lang):        
        out = self.epTranslateCategories.executeByParameters(lang=lang)
        return out

    #
    # Gives back translation of all levels with parameters
    #
    # curl  --header "Content-Type: application/json" --request GET http://localhost:80/translate/levels/lang/en
    #
    # GET http://localhost:80/translate/levels/lang/en
    #
    #@route('/levels/lang/<lang>')
    @route(EPTranslateLevels.PATH_PAR_URL, methods=[EPTranslateLevels.METHOD])
    def translateLevelsWithParameter(self, lang):        
        out = self.epTranslateLevels.executeByParameters(lang=lang)
        return out

# ===


