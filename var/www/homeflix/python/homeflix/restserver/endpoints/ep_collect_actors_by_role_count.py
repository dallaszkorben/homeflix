import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectActorsByRoleCount(EP):

    ID = 'collect_actors_by_role_count'
    URL = '/collect/actors/by/role/count'

    PATH_PAR_PAYLOAD = '/actors/by/role/count'
    PATH_PAR_URL = '/actors/by/role/count/category/<category>/minimum/<minimum>/limit/<limit>'

    METHOD = 'GET'

    ATTR_CATEGORY = 'category'
    ATTR_MINIMUM = 'minimum'
    ATTR_LIMIT = 'limit'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, category, minimum=3, limit=15) -> dict:
        payload = {}

        payload[EPCollectActorsByRoleCount.ATTR_CATEGORY] = category
        payload[EPCollectActorsByRoleCount.ATTR_MINIMUM] = minimum
        payload[EPCollectActorsByRoleCount.ATTR_LIMIT] = limit
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        category   = payload[EPCollectActorsByRoleCount.ATTR_CATEGORY]
        minimum   = int(payload.get(EPCollectActorsByRoleCount.ATTR_MINIMUM, 3))
        limit       = int(payload.get(EPCollectActorsByRoleCount.ATTR_LIMIT, 15))

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8})".format(
                remoteAddress, EPCollectActorsByRoleCount.METHOD, EPCollectActorsByRoleCount.URL,
                EPCollectActorsByRoleCount.ATTR_CATEGORY, category,
                EPCollectActorsByRoleCount.ATTR_MINIMUM, minimum,
                EPCollectActorsByRoleCount.ATTR_LIMIT, limit
            )
        )

        output = self.web_gadget.db.get_list_of_actors(category=category, minimum=minimum, limit=limit, json=True)

        return output_json(output, EP.CODE_OK)
