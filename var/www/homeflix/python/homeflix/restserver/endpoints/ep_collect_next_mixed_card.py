import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectNextMixed(EP):

    ID = 'collect_next_mixed'
    URL = '/collect/next/mixed'

    PATH_PAR_PAYLOAD = '/next/mixed'
    PATH_PAR_URL = '/next/mixed/card_id/<card_id>/category/<category>/playlist/<playlist>/tags/<tags>/level/<level>/filter_on/<filter_on>/title/<title>/genres/<genres>/themes/<themes>/directors/<directors>/actors/<actors>/lecturers/<lecturers>/performers/<performers>/origins/<origins>/decade/<decade>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CARD_ID = 'card_id'
    ATTR_CATEGORY = 'category'
    ATTR_PLAYLIST = 'playlist'
    ATTR_TAG = 'tags'
    ATTR_LEVEL = 'level'
    ATTR_FILTER_ON = 'filter_on'
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

    def executeByParameters(self, card_id, category, playlist, tags, level, filter_on, title, genres, themes, directors, actors, lecturers, performers, origins, decade, lang) -> dict:
        payload = {}

        payload[EPCollectNextMixed.ATTR_CARD_ID] = card_id
        payload[EPCollectNextMixed.ATTR_CATEGORY] = category
        payload[EPCollectNextMixed.ATTR_PLAYLIST] = playlist
        payload[EPCollectNextMixed.ATTR_TAG] = tags
        payload[EPCollectNextMixed.ATTR_LEVEL] = level
        payload[EPCollectNextMixed.ATTR_FILTER_ON] = filter_on
        payload[EPCollectNextMixed.ATTR_TITLE] = title
        payload[EPCollectNextMixed.ATTR_GENRE] = genres
        payload[EPCollectNextMixed.ATTR_THEME] = themes
        payload[EPCollectNextMixed.ATTR_DIRECTOR] = directors
        payload[EPCollectNextMixed.ATTR_ACTOR] = actors
        payload[EPCollectNextMixed.ATTR_LECTURER] = lecturers        
        payload[EPCollectNextMixed.ATTR_PERFORMER] = performers
        payload[EPCollectNextMixed.ATTR_ORIGIN] = origins
        payload[EPCollectNextMixed.ATTR_DECADE] = decade
        payload[EPCollectNextMixed.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        card_id    = payload[EPCollectNextMixed.ATTR_CARD_ID]
        category   = payload[EPCollectNextMixed.ATTR_CATEGORY]
        playlist   = payload.get(EPCollectNextMixed.ATTR_PLAYLIST, '*')
        tags       = payload.get(EPCollectNextMixed.ATTR_TAG, '*')
        level      = payload.get(EPCollectNextMixed.ATTR_LEVEL, '*')
        filter_on  = payload.get(EPCollectNextMixed.ATTR_FILTER_ON, '*')      
        title      = payload.get(EPCollectNextMixed.ATTR_TITLE, '*')
        genres     = payload.get(EPCollectNextMixed.ATTR_GENRE, '*')
        themes     = payload.get(EPCollectNextMixed.ATTR_THEME, '*')
        directors  = payload.get(EPCollectNextMixed.ATTR_DIRECTOR, '*')
        actors     = payload.get(EPCollectNextMixed.ATTR_ACTOR, '*')
        lecturers  = payload.get(EPCollectNextMixed.ATTR_LECTURER, '*')
        performers = payload.get(EPCollectNextMixed.ATTR_PERFORMER, '*')
        origins    = payload.get(EPCollectNextMixed.ATTR_ORIGIN, '*')
        decade     = payload.get(EPCollectNextMixed.ATTR_DECADE, '*')
        lang       = payload.get(EPCollectNextMixed.ATTR_LANG, 'en')

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14}, '{15}': {16}, '{17}': {18}, '{19}': {20}, '{21}': {22}, '{23}': {24}, '{25}': {26}, '{27}': {28}, '{29}': {30}, '{31}': {32}, '{33}': {34})".format(
                remoteAddress, EPCollectNextMixed.METHOD, EPCollectNextMixed.URL,
                EPCollectNextMixed.ATTR_CARD_ID, card_id,
                EPCollectNextMixed.ATTR_CATEGORY, category,
                EPCollectNextMixed.ATTR_TAG, tags,
                EPCollectNextMixed.ATTR_PLAYLIST, playlist,
                EPCollectNextMixed.ATTR_LEVEL, level,
                EPCollectNextMixed.ATTR_FILTER_ON, filter_on,
                EPCollectNextMixed.ATTR_TITLE, title,
                EPCollectNextMixed.ATTR_GENRE, genres,
                EPCollectNextMixed.ATTR_THEME, themes,
                EPCollectNextMixed.ATTR_DIRECTOR, directors,
                EPCollectNextMixed.ATTR_ACTOR, actors,
                EPCollectNextMixed.ATTR_LECTURER, lecturers,
                EPCollectNextMixed.ATTR_PERFORMER, performers,
                EPCollectNextMixed.ATTR_ORIGIN, origins,
                EPCollectNextMixed.ATTR_DECADE, decade,
                EPCollectNextMixed.ATTR_LANG, lang 
            )
        )

        if playlist == '*':
            playlist = None  
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

        output = self.web_gadget.db.get_next_level_cards(card_id=card_id, category=category, playlist=playlist, tags=tags, level=level, filter_on=filter_on, title=title, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, performers=performers, origins=origins, decade=decade, lang=lang, limit=100)

        return output_json(output, EP.CODE_OK)
