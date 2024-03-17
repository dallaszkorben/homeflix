import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectGeneralLevel(EP):

    ID = 'collect_general_level'
    URL = '/collect/general/level'

    PATH_PAR_PAYLOAD = '/general/level'
    PATH_PAR_URL = '/general/level/<level>/category/<category>/genre/<genre>/theme/<theme>/origin/<origin>/decade/<decade>/lang/<lang>'
    METHOD = 'GET'

    ATTR_LEVEL = 'level'
    ATTR_CATEGORY = 'category'
    ATTR_GENRE = 'genre'
    ATTR_THEME = 'theme'
    ATTR_ORIGIN = 'origin'
    ATTR_DECADE = 'decade'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, level, category, genre, theme, origin, decade, lang) -> dict:
        payload = {}

        payload[EPCollectGeneralLevel.ATTR_LEVEL] = level
        payload[EPCollectGeneralLevel.ATTR_CATEGORY] = category
        payload[EPCollectGeneralLevel.ATTR_GENRE] = genre
        payload[EPCollectGeneralLevel.ATTR_THEME] = theme
        payload[EPCollectGeneralLevel.ATTR_ORIGIN] = origin
        payload[EPCollectGeneralLevel.ATTR_DECADE] = decade
        payload[EPCollectGeneralLevel.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        level = payload[EPCollectGeneralLevel.ATTR_LEVEL]
        category = payload[EPCollectGeneralLevel.ATTR_CATEGORY]
        genre = payload[EPCollectGeneralLevel.ATTR_GENRE]
        theme = payload[EPCollectGeneralLevel.ATTR_THEME]
        origin = payload[EPCollectGeneralLevel.ATTR_ORIGIN]
        decade = payload[EPCollectGeneralLevel.ATTR_DECADE]
        lang = payload[EPCollectGeneralLevel.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14}, '{15}': {16})".format(
                    remoteAddress, EPCollectGeneralLevel.METHOD, EPCollectGeneralLevel.URL,
                    EPCollectGeneralLevel.ATTR_LEVEL, level,
                    EPCollectGeneralLevel.ATTR_CATEGORY, category,
                    EPCollectGeneralLevel.ATTR_GENRE, genre,
                    EPCollectGeneralLevel.ATTR_THEME, theme,
                    EPCollectGeneralLevel.ATTR_ORIGIN, origin,
                    EPCollectGeneralLevel.ATTR_DECADE, decade,
                    EPCollectGeneralLevel.ATTR_LANG, lang
                )
        )

        if genre == '*':
            genre=None
        if theme == '*':
            theme=None
        if origin == '*':
            origin=None
        if decade == '*':
            decade=None

        output = self.web_gadget.db.get_general_level(level, category, genre, theme, origin, decade, lang, limit=100)

        return output_json(output, EP.CODE_OK)
