import logging

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPCollectChildHierarchyOrCard(EP):

    URL = '/collect/child_hierarchy_or_card'

    PATH_PAR_PAYLOAD = '/child_hierarchy_or_card'
    PATH_PAR_URL = '/child_hierarchy_or_card/id/<id>/lang/<lang>'

    METHOD = 'GET'

    ATTR_ID = 'id'
    ATTR_LANG = 'lang'    

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self, id, lang) -> dict:

        payload = {}
        payload[EPCollectChildHierarchyOrCard.ATTR_ID] = id
        payload[EPCollectChildHierarchyOrCard.ATTR_LANG] = lang
        
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:

        remoteAddress = request.remote_addr

        id = payload[EPCollectChildHierarchyOrCard.ATTR_ID]
        lang = payload[EPCollectChildHierarchyOrCard.ATTR_LANG]

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}) ('{5}': {6})".format(
                    remoteAddress, EPCollectChildHierarchyOrCard.METHOD, EPCollectChildHierarchyOrCard.URL,
                    EPCollectChildHierarchyOrCard.ATTR_ID, id,
                    EPCollectChildHierarchyOrCard.ATTR_LANG, lang
                )
        )

        output = self.web_gadget.db.get_child_hierarchy_or_card(higher_card_id=id, lang=lang)


        return output_json(output, EP.CODE_OK)
