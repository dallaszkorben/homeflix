import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPPersonalTagGet(EP):

    URL = '/personal/tag/get'

    PATH_PAR_PAYLOAD = '/tag/get'
    PATH_PAR_URL = '/tag/get/category/<category>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/origins/<origins>/decade/<decade>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_TITLE = 'title'
    ATTR_GENRES = 'genres'
    ATTR_THEMES = 'themes'
    ATTR_DIRECTORS = 'directors'
    ATTR_ACTORS = 'actors'
    ATTR_LECTURERS = 'lecturers'
    ATTR_ORIGINS = 'origins'
    ATTR_DECADE = 'decade'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget


    def executeByParameters(self, category, title, genres, themes, directors, actors, lecturers, origins, decade, lang) -> dict:
        payload = {}

        payload[EPPersonalTagGet.ATTR_CATEGORY] = category
        payload[EPPersonalTagGet.ATTR_GENRES] = genres
        payload[EPPersonalTagGet.ATTR_TITLE] = title
        payload[EPPersonalTagGet.ATTR_THEMES] = themes
        payload[EPPersonalTagGet.ATTR_DIRECTORS] = directors
        payload[EPPersonalTagGet.ATTR_ACTORS] = actors
        payload[EPPersonalTagGet.ATTR_LECTURERS] = lecturers        
        payload[EPPersonalTagGet.ATTR_ORIGINS] = origins
        payload[EPPersonalTagGet.ATTR_DECADE] = decade
        payload[EPPersonalTagGet.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        category = payload[EPPersonalTagGet.ATTR_CATEGORY]
        title = payload.get(EPPersonalTagGet.ATTR_TITLE, '*')
        genres = payload.get(EPPersonalTagGet.ATTR_GENRES, '*')
        themes = payload.get(EPPersonalTagGet.ATTR_THEMES, '*')
        directors = payload.get(EPPersonalTagGet.ATTR_DIRECTORS, '*')
        actors = payload.get(EPPersonalTagGet.ATTR_ACTORS, '*')
        lecturers = payload.get(EPPersonalTagGet.ATTR_LECTURERS, '*')
        origins = payload.get(EPPersonalTagGet.ATTR_ORIGINS, '*')
        decade = payload.get(EPPersonalTagGet.ATTR_DECADE, '*')
        lang = payload.get(EPPersonalTagGet.ATTR_LANG, 'en')

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14}, '{15}': {16}, '{17}': {18}, '{19}': {20}, '{21}': {22})".format(
                    remoteAddress, EPPersonalTagGet.METHOD, EPPersonalTagGet.URL,
                    EPPersonalTagGet.ATTR_CATEGORY, category,
                    EPPersonalTagGet.ATTR_TITLE, title,
                    EPPersonalTagGet.ATTR_GENRES, genres,
                    EPPersonalTagGet.ATTR_THEMES, themes,
                    EPPersonalTagGet.ATTR_DIRECTORS, directors,
                    EPPersonalTagGet.ATTR_ACTORS, actors,
                    EPPersonalTagGet.ATTR_LECTURERS, lecturers,
                    EPPersonalTagGet.ATTR_ORIGINS, origins,
                    EPPersonalTagGet.ATTR_DECADE, decade,
                    EPPersonalTagGet.ATTR_LANG, lang
                )
        )
    
        if title == '*':
            title = None
        if genres == '*':
            genres = None
        if themes == '*':
            themes = None
        if directors == '*':
            directors = None
        if actors == '*':
            actors = None
        if lecturers == '*':
            lecturers = None
        if origins == '*':
            origins = None
        if decade == '*':
            decade=None
        output = self.web_gadget.db.get_tags(category=category, playlist=None, tags=None, title=title, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, origins=origins, decade=decade, lang=lang)

        return output_json(output, EP.CODE_OK)
