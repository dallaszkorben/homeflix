import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectHighestMixed(EP):

    ID = 'collect_highest_mixed'
    URL = '/collect/highest/mixed'

    PATH_PAR_PAYLOAD = '/highest/mixed'
    PATH_PAR_URL = '/highest/mixed/category/<category>/view_state/<view_state>/tags/<tags>/level/<level>/filter_on/<filter_on>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/writers/<writers>/actors/<actors>/voices/<voices>/lecturers/<lecturers>/performers/<performers>/origins/<origins>/rate/<rate>/decade/<decade>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_VIEW_STATE = 'view_state'
    ATTR_TAG = 'tags'
    ATTR_LEVEL = 'level'
    ATTR_FILTER_ON = 'filter_on'
    ATTR_TITLE = 'title'
    ATTR_GENRE = 'genres'
    ATTR_THEME = 'themes'
    ATTR_DIRECTOR = 'directors'
    ATTR_WRITER = 'writers'
    ATTR_ACTOR = 'actors'
    ATTR_VOICE = 'voices'
    ATTR_LECTURER = 'lecturers'
    ATTR_PERFORMER = 'performers'
    ATTR_ORIGIN = 'origins'
    ATTR_RATE = 'rate'
    ATTR_DECADE = 'decade'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, view_state, tags, level, filter_on, title, genres, themes, directors, writers, actors, voices, lecturers, performers, origins, rate, decade, lang) -> dict:
        payload = {}

        payload[EPCollectHighestMixed.ATTR_CATEGORY] = category
        payload[EPCollectHighestMixed.ATTR_VIEW_STATE] = view_state
        payload[EPCollectHighestMixed.ATTR_TAG] = tags
        payload[EPCollectHighestMixed.ATTR_LEVEL] = level
        payload[EPCollectHighestMixed.ATTR_FILTER_ON] = filter_on
        payload[EPCollectHighestMixed.ATTR_TITLE] = title
        payload[EPCollectHighestMixed.ATTR_GENRE] = genres
        payload[EPCollectHighestMixed.ATTR_THEME] = themes
        payload[EPCollectHighestMixed.ATTR_DIRECTOR] = directors
        payload[EPCollectHighestMixed.ATTR_WRITER] = writers
        payload[EPCollectHighestMixed.ATTR_ACTOR] = actors
        payload[EPCollectHighestMixed.ATTR_VOICE] = voices
        payload[EPCollectHighestMixed.ATTR_LECTURER] = lecturers
        payload[EPCollectHighestMixed.ATTR_PERFORMER] = performers
        payload[EPCollectHighestMixed.ATTR_ORIGIN] = origins
        payload[EPCollectHighestMixed.ATTR_RATE] = rate
        payload[EPCollectHighestMixed.ATTR_DECADE] = decade
        payload[EPCollectHighestMixed.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category   = payload[EPCollectHighestMixed.ATTR_CATEGORY]
        view_state   = payload.get(EPCollectHighestMixed.ATTR_VIEW_STATE, '*')
        tags       = payload.get(EPCollectHighestMixed.ATTR_TAG, '*')
        level      = payload.get(EPCollectHighestMixed.ATTR_LEVEL, '*')
        filter_on  = payload.get(EPCollectHighestMixed.ATTR_FILTER_ON, '*')
        title      = payload.get(EPCollectHighestMixed.ATTR_TITLE, '*')
        genres     = payload.get(EPCollectHighestMixed.ATTR_GENRE, '*')
        themes     = payload.get(EPCollectHighestMixed.ATTR_THEME, '*')
        directors  = payload.get(EPCollectHighestMixed.ATTR_DIRECTOR, '*')
        writers    = payload.get(EPCollectHighestMixed.ATTR_WRITER, '*')
        actors     = payload.get(EPCollectHighestMixed.ATTR_ACTOR, '*')
        voices     = payload.get(EPCollectHighestMixed.ATTR_VOICE, '*')
        lecturers  = payload.get(EPCollectHighestMixed.ATTR_LECTURER, '*')
        performers = payload.get(EPCollectHighestMixed.ATTR_PERFORMER, '*')
        origins    = payload.get(EPCollectHighestMixed.ATTR_ORIGIN, '*')
        rate       = payload.get(EPCollectHighestMixed.ATTR_RATE, '*')
        decade     = payload.get(EPCollectHighestMixed.ATTR_DECADE, '*')
        lang       = payload.get(EPCollectHighestMixed.ATTR_LANG, 'en')

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14}, '{15}': {16}, '{17}': {18}, '{19}': {20}, '{21}': {22}, '{23}': {24}, '{25}': {26}, '{27}': {28}, '{29}': {30}, '{31}': {32}, '{33}': {34}, '{35}': {36}, '{37}': {38})".format(
                    remoteAddress, EPCollectHighestMixed.METHOD, EPCollectHighestMixed.URL,
                    EPCollectHighestMixed.ATTR_CATEGORY, category,
                    EPCollectHighestMixed.ATTR_TAG, tags,
                    EPCollectHighestMixed.ATTR_VIEW_STATE, view_state,
                    EPCollectHighestMixed.ATTR_LEVEL, level,
                    EPCollectHighestMixed.ATTR_FILTER_ON, filter_on,
                    EPCollectHighestMixed.ATTR_TITLE, title,
                    EPCollectHighestMixed.ATTR_GENRE, genres,
                    EPCollectHighestMixed.ATTR_THEME, themes,
                    EPCollectHighestMixed.ATTR_DIRECTOR, directors,
                    EPCollectHighestMixed.ATTR_WRITER, writers,
                    EPCollectHighestMixed.ATTR_ACTOR, actors,
                    EPCollectHighestMixed.ATTR_VOICE, voices,
                    EPCollectHighestMixed.ATTR_LECTURER, lecturers,
                    EPCollectHighestMixed.ATTR_PERFORMER, performers,
                    EPCollectHighestMixed.ATTR_ORIGIN, origins,
                    EPCollectHighestMixed.ATTR_RATE, rate,
                    EPCollectHighestMixed.ATTR_DECADE, decade,
                    EPCollectHighestMixed.ATTR_LANG, lang
                )
        )

        if view_state == '*':
            view_state = None
        if tags == '*':
            tags = None
        if level == '*':
            level = None
        if filter_on == '*':
            filter_on = None
        if title == '*':
            title = None
        if genres == '*':
            genres = None
        if themes == '*':
            themes = None
        if directors == '*':
            directors = None
        if writers == '*':
            writers = None
        if actors == '*':
            actors = None
        if voices == '*':
            voices = None
        if lecturers == '*':
            lecturers = None
        if performers == '*':
            performers = None
        if origins == '*':
            origins = None
        if rate == '*':
            rate = None
        if decade == '*':
            decade=None

        output = self.web_gadget.db.get_highest_level_cards(category=category, view_state=view_state, tags=tags, level=level, filter_on=filter_on, title=title, genres=genres, themes=themes, directors=directors, writers=writers, actors=actors, voices=voices, lecturers=lecturers, performers=performers, origins=origins, decade=decade, rate_value=rate, lang=lang, limit=100)

        return output_json(output, EP.CODE_OK)
