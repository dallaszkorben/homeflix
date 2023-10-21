import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectGeneralStandalone(EP):

    ID = 'collect_general_standalone'
    URL = '/collect/general/standalone'

    PATH_PAR_PAYLOAD = '/general/standalone'
    PATH_PAR_URL = '/general/standalone/category/<category>/genre/<genre>/theme/<theme>/origin/<origin>/not_origin/<not_origin>/decade/<decade>/lang/<lang>'
    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_GENRE = 'genre'
    ATTR_THEME = 'theme'
    ATTR_ORIGIN = 'origin'
    ATTR_NOT_ORIGIN = 'not_origin'
    ATTR_DECADE = 'decade'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, genre, theme, origin, not_origin, decade, lang) -> dict:
        payload = {}

        payload[EPCollectGeneralStandalone.ATTR_CATEGORY] = category
        payload[EPCollectGeneralStandalone.ATTR_GENRE] = genre
        payload[EPCollectGeneralStandalone.ATTR_THEME] = theme
        payload[EPCollectGeneralStandalone.ATTR_ORIGIN] = origin
        payload[EPCollectGeneralStandalone.ATTR_NOT_ORIGIN] = not_origin
        payload[EPCollectGeneralStandalone.ATTR_DECADE] = decade
        payload[EPCollectGeneralStandalone.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category = payload[EPCollectGeneralStandalone.ATTR_CATEGORY]
        genre = payload[EPCollectGeneralStandalone.ATTR_GENRE]
        theme = payload[EPCollectGeneralStandalone.ATTR_THEME]
        origin = payload[EPCollectGeneralStandalone.ATTR_ORIGIN]
        not_origin = payload[EPCollectGeneralStandalone.ATTR_NOT_ORIGIN]
        decade = payload[EPCollectGeneralStandalone.ATTR_DECADE]
        lang = payload[EPCollectGeneralStandalone.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14}, '{15}': {16})".format(
                    remoteAddress, EPCollectGeneralStandalone.METHOD, EPCollectGeneralStandalone.URL,
                    EPCollectGeneralStandalone.ATTR_CATEGORY, category,
                    EPCollectGeneralStandalone.ATTR_GENRE, genre,
                    EPCollectGeneralStandalone.ATTR_THEME, theme,
                    EPCollectGeneralStandalone.ATTR_ORIGIN, origin,
                    EPCollectGeneralStandalone.ATTR_NOT_ORIGIN, not_origin,
                    EPCollectGeneralStandalone.ATTR_DECADE, decade,
                    EPCollectGeneralStandalone.ATTR_LANG, lang
                )
        )

        if genre == '*':
            genre=None
        if theme == '*':
            theme=None
        if origin == '*':
            origin=None
        if not_origin == '*':
            not_origin=None
        if decade == '*':
            decade=None

        output = self.web_gadget.db.get_general_standalone(category, genre, theme, origin, not_origin, decade, lang, limit=100)

        return output_json(output, EP.CODE_OK)
