import logging

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPCollectAbcByMovieTitleCount(EP):

    ID = 'collect_abc_by_movie_title_count'
    URL = '/collect/abc/by/moveie_title/count'

    PATH_PAR_PAYLOAD = '/abc/by/movie_title/count'
    PATH_PAR_URL = '/abc/by/movie_title/count/category/<category>/maximum/<maximum>/lang/<lang>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_MAXIMUM = 'maximum'
    ATTR_LANG = 'lang'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, maximum=25, lang='en') -> dict:
        payload = {}

        payload[EPCollectAbcByMovieTitleCount.ATTR_CATEGORY] = category
        payload[EPCollectAbcByMovieTitleCount.ATTR_MAXIMUM] = maximum
        payload[EPCollectAbcByMovieTitleCount.ATTR_LANG] = lang

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category = payload[EPCollectAbcByMovieTitleCount.ATTR_CATEGORY]
        maximum  = int(payload.get(EPCollectAbcByMovieTitleCount.ATTR_MAXIMUM, 25))
        lang     = payload.get(EPCollectAbcByMovieTitleCount.ATTR_LANG, "en")

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8})".format(
                remoteAddress, EPCollectAbcByMovieTitleCount.METHOD, EPCollectAbcByMovieTitleCount.URL,
                EPCollectAbcByMovieTitleCount.ATTR_CATEGORY, category,
                EPCollectAbcByMovieTitleCount.ATTR_MAXIMUM, maximum,
                EPCollectAbcByMovieTitleCount.ATTR_LANG, lang
            )
        )

        output = self.web_gadget.db.get_abc_of_movie_title(category=category, maximum=maximum, lang=lang)

        return output_json(output, EP.CODE_OK)
