import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectLowest(EP):

    ID = 'collect_lowest'
    URL = '/collect/lowest'

    PATH_PAR_PAYLOAD = '/lowest'
    PATH_PAR_URL = '/lowest/category/<category>/view_state/<view_state>/tags/<tags>/level/<level>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/performers/<performers>/origins/<origins>/decade/<decade>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_VIEW_STATE = 'view_state'
    ATTR_TAG = 'tags'
    ATTR_LEVEL = 'level'
    ATTR_TITLE = 'title'
    ATTR_GENRE = 'genres'
    ATTR_THEME = 'themes'
    ATTR_DIRECTOR = 'directors'
    ATTR_ACTOR = 'actors'
    ATTR_LECTURER = 'lecturers'
    ATTR_PERFORMER = 'performers'
    ATTR_ORIGIN = 'origins'
    ATTR_DECADE = 'decade'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, view_state, tags, level, title, genres, themes, directors, actors, lecturers, performers, origins, decade, lang) -> dict:
        payload = {}

        payload[EPCollectLowest.ATTR_CATEGORY] = category
        payload[EPCollectLowest.ATTR_VIEW_STATE] = view_state
        payload[EPCollectLowest.ATTR_TAG] = tags
        payload[EPCollectLowest.ATTR_LEVEL] = level
        payload[EPCollectLowest.ATTR_TITLE] = title
        payload[EPCollectLowest.ATTR_GENRE] = genres
        payload[EPCollectLowest.ATTR_THEME] = themes
        payload[EPCollectLowest.ATTR_DIRECTOR] = directors
        payload[EPCollectLowest.ATTR_ACTOR] = actors
        payload[EPCollectLowest.ATTR_LECTURER] = lecturers
        payload[EPCollectLowest.ATTR_PERFORMER] = performers
        payload[EPCollectLowest.ATTR_ORIGIN] = origins
        payload[EPCollectLowest.ATTR_DECADE] = decade
        payload[EPCollectLowest.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category = payload[EPCollectLowest.ATTR_CATEGORY]
        view_state = payload.get(EPCollectLowest.ATTR_VIEW_STATE, '*')
        tags = payload.get(EPCollectLowest.ATTR_TAG, '*')
        level = payload.get(EPCollectLowest.ATTR_LEVEL, '*')
        title = payload.get(EPCollectLowest.ATTR_TITLE, '*')
        genres = payload.get(EPCollectLowest.ATTR_GENRE, '*')
        themes = payload.get(EPCollectLowest.ATTR_THEME, '*')
        directors = payload.get(EPCollectLowest.ATTR_DIRECTOR, '*')
        actors = payload.get(EPCollectLowest.ATTR_ACTOR, '*')
        lecturers = payload.get(EPCollectLowest.ATTR_LECTURER, '*')
        performers = payload.get(EPCollectLowest.ATTR_PERFORMER, '*')
        origins = payload.get(EPCollectLowest.ATTR_ORIGIN, '*')
        decade = payload.get(EPCollectLowest.ATTR_DECADE, '*')
        lang = payload.get(EPCollectLowest.ATTR_LANG, 'en')

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14}, '{15}': {16}, '{17}': {18}, '{19}': {20}, '{21}': {22}, '{23}': {24}, '{25}': {26}, '{27}': {28}, '{29}': {30})".format(
                    remoteAddress, EPCollectLowest.METHOD, EPCollectLowest.URL,
                    EPCollectLowest.ATTR_CATEGORY, category,
                    EPCollectLowest.ATTR_TAG, tags,
                    EPCollectLowest.ATTR_VIEW_STATE, view_state,
                    EPCollectLowest.ATTR_LEVEL, level,
                    EPCollectLowest.ATTR_TITLE, title,
                    EPCollectLowest.ATTR_GENRE, genres,
                    EPCollectLowest.ATTR_THEME, themes,
                    EPCollectLowest.ATTR_DIRECTOR, directors,
                    EPCollectLowest.ATTR_ACTOR, actors,
                    EPCollectLowest.ATTR_LECTURER, lecturers,
                    EPCollectLowest.ATTR_PERFORMER, performers,
                    EPCollectLowest.ATTR_ORIGIN, origins,
                    EPCollectLowest.ATTR_DECADE, decade,
                    EPCollectLowest.ATTR_LANG, lang
                )
        )

        if view_state == '*':
            view_state = None
        if tags == '*':
            tags = None
        if level == '*':
            level = None
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
        if performers == '*':
            performers = None
        if origins == '*':
            origins = None
        if decade == '*':
            decade=None

        output = self.web_gadget.db.get_lowest_level_cards(category=category, view_state=view_state, tags=tags, level=level, title=title, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, performers=performers, origins=origins, decade=decade, lang=lang, limit=100)

        return output_json(output, EP.CODE_OK)
