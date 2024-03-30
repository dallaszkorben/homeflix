import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectNextMixed(EP):

    ID = 'collect_next_mixed'
    URL = '/collect/next/mixed'

    PATH_PAR_PAYLOAD = '/next/mixed'
    PATH_PAR_URL = '/next/mixed/card_id/<card_id>/category/<category>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/origins/<origins>/decade/<decade>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CARD_ID = 'card_id'
    ATTR_CATEGORY = 'category'
    ATTR_GENRE = 'genres'
    ATTR_THEME = 'themes'
    ATTR_DIRECTOR = 'directors'    
    ATTR_ACTOR = 'actors'
    ATTR_LECTURER = 'lecturers'    
    ATTR_ORIGIN = 'origins'
    ATTR_DECADE = 'decade'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, card_id, category, genres, themes, directors, actors, lecturers, origins, decade, lang) -> dict:
        payload = {}

        payload[EPCollectNextMixed.ATTR_CARD_ID] = card_id
        payload[EPCollectNextMixed.ATTR_CATEGORY] = category
        payload[EPCollectNextMixed.ATTR_GENRE] = genres
        payload[EPCollectNextMixed.ATTR_THEME] = themes
        payload[EPCollectNextMixed.ATTR_DIRECTOR] = directors
        payload[EPCollectNextMixed.ATTR_ACTOR] = actors
        payload[EPCollectNextMixed.ATTR_LECTURER] = lecturers        
        payload[EPCollectNextMixed.ATTR_ORIGIN] = origins
        payload[EPCollectNextMixed.ATTR_DECADE] = decade
        payload[EPCollectNextMixed.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id = payload[EPCollectNextMixed.ATTR_CARD_ID]
        category = payload[EPCollectNextMixed.ATTR_CATEGORY]
        genres = payload[EPCollectNextMixed.ATTR_GENRE]
        themes = payload[EPCollectNextMixed.ATTR_THEME]
        directors = payload[EPCollectNextMixed.ATTR_DIRECTOR]
        actors = payload[EPCollectNextMixed.ATTR_ACTOR]
        lecturers = payload[EPCollectNextMixed.ATTR_LECTURER]
        origins = payload[EPCollectNextMixed.ATTR_ORIGIN]
        decade = payload[EPCollectNextMixed.ATTR_DECADE]
        lang = payload[EPCollectNextMixed.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14}, '{15}': {16}, '{17}': {18}, '{19}': {20}, '{21}': {22})".format(
                    remoteAddress, EPCollectNextMixed.METHOD, EPCollectNextMixed.URL,
                    EPCollectNextMixed.ATTR_CARD_ID, card_id,
                    EPCollectNextMixed.ATTR_CATEGORY, category,
                    EPCollectNextMixed.ATTR_GENRE, genres,
                    EPCollectNextMixed.ATTR_THEME, themes,
                    EPCollectNextMixed.ATTR_DIRECTOR, directors,
                    EPCollectNextMixed.ATTR_ACTOR, actors,
                    EPCollectNextMixed.ATTR_LECTURER, lecturers,
                    EPCollectNextMixed.ATTR_ORIGIN, origins,
                    EPCollectNextMixed.ATTR_DECADE, decade,
                    EPCollectNextMixed.ATTR_LANG, lang
                )
        )

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

        output = self.web_gadget.db.get_next_level_cards(card_id, category, genres, themes, directors, actors, lecturers, origins, decade, lang, limit=100)

        return output_json(output, EP.CODE_OK)
