import logging
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPPersonalUserDataUpdate(EP):

    URL = '/personal/user_data/update'

    PATH_PAR_PAYLOAD = '/user_data/update'
#    PATH_PAR_URL = ''

    METHOD = 'PUT'

    ATTR_USER_ID               = 'user_id'
    ATTR_LANGUAGE_CODE         = 'language_code'
    ATTR_SHOW_ORIGINAL_TITLE   = 'show_original_title'
    ATTR_SHOW_LYRICS_ANYWAY    = 'show_lyrics_anyway'
    ATTR_SHOW_STORYLINE_ANYWAY = 'show_storyline_anyway'
    ATTR_PLAY_CONTINUOUSLY     = 'play_continuously'


    

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

#    def executeByParameters(self, user_id, card_id, last_position, start_epoch=None) -> dict:
#        payload = {}
#        payload[EPPersonalUserDataUpdate.ATTR_USER_ID] = user_id
#        payload[EPPersonalUserDataUpdate.ATTR_CARD_ID] = card_id
#        payload[EPPersonalUserDataUpdate.ATTR_LAST_POSITION] = last_position
#        payload[EPPersonalUserDataUpdate.ATTR_START_EPOCH] = start_epoch
#                
#        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        user_id               = payload.get(EPPersonalUserDataUpdate.ATTR_USER_ID, None)
        language_code         = payload.get(EPPersonalUserDataUpdate.ATTR_LANGUAGE_CODE, None) 
        show_original_title   = payload.get(EPPersonalUserDataUpdate.ATTR_SHOW_ORIGINAL_TITLE, None)
        show_lyrics_anyway    = payload.get(EPPersonalUserDataUpdate.ATTR_SHOW_LYRICS_ANYWAY, None)
        show_storyline_anyway = payload.get(EPPersonalUserDataUpdate.ATTR_SHOW_STORYLINE_ANYWAY, None)
        play_continuously     = payload.get(EPPersonalUserDataUpdate.ATTR_PLAY_CONTINUOUSLY, None)

        logging.debug( "WEB request ({0}): {1} {2} ('{3}': {4}, '{5}': {6}, '{7}': {8}, '{9}': {10}, '{11}': {12}, '{13}': {14})".format(
                    remoteAddress, EPPersonalUserDataUpdate.METHOD, EPPersonalUserDataUpdate.URL,
                    EPPersonalUserDataUpdate.ATTR_USER_ID,               user_id,
                    EPPersonalUserDataUpdate.ATTR_LANGUAGE_CODE,         language_code, 
                    EPPersonalUserDataUpdate.ATTR_SHOW_ORIGINAL_TITLE,   show_original_title,  
                    EPPersonalUserDataUpdate.ATTR_SHOW_LYRICS_ANYWAY,    show_lyrics_anyway,  
                    EPPersonalUserDataUpdate.ATTR_SHOW_STORYLINE_ANYWAY, show_storyline_anyway,  
                    EPPersonalUserDataUpdate.ATTR_PLAY_CONTINUOUSLY,     play_continuously
                )
        )

        output = self.web_gadget.db.update_user_data(user_id, language_code=language_code, show_original_title=show_original_title, show_lyrics_anyway=show_lyrics_anyway, show_storyline_anyway=show_storyline_anyway, play_continuously=play_continuously)

        return output_json(output, EP.CODE_OK)
