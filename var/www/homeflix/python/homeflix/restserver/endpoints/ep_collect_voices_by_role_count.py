import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectVoicesByRoleCount(EP):

    ID = 'collect_voices_by_role_count'
    URL = '/collect/voices/by/role/count'

    PATH_PAR_PAYLOAD = '/voices/by/role/count'
    PATH_PAR_URL = '/voices/by/role/count/category/<category>/minimum/<minimum>/limit/<limit>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_MINIMUM = 'minimum'
    ATTR_LIMIT = 'limit'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, minimum=3, limit=15) -> dict:
        payload = {}

        payload[EPCollectVoicesByRoleCount.ATTR_CATEGORY] = category
        payload[EPCollectVoicesByRoleCount.ATTR_MINIMUM] = minimum
        payload[EPCollectVoicesByRoleCount.ATTR_LIMIT] = limit

        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category   = payload[EPCollectVoicesByRoleCount.ATTR_CATEGORY]
        minimum   = int(payload.get(EPCollectVoicesByRoleCount.ATTR_MINIMUM, 3))
        limit       = int(payload.get(EPCollectVoicesByRoleCount.ATTR_LIMIT, 15))

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8})".format(
                remoteAddress, EPCollectVoicesByRoleCount.METHOD, EPCollectVoicesByRoleCount.URL,
                EPCollectVoicesByRoleCount.ATTR_CATEGORY, category,
                EPCollectVoicesByRoleCount.ATTR_MINIMUM, minimum,
                EPCollectVoicesByRoleCount.ATTR_LIMIT, limit
            )
        )

        output = self.web_gadget.db.get_list_of_voices_by_role_count(category=category, minimum=minimum, limit=limit, json=True)

        return output_json(output, EP.CODE_OK)
