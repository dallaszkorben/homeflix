import logging
# import subprocess
# import os
import time

from playem.card.database import SqlDatabase as DB

from playem.exceptions.invalid_api_usage import InvalidAPIUsage
from playem.restserver.endpoints.ep import EP
from playem.restserver.representations import output_json

from flask import request

class EPControlRebuild(EP):

    ID = 'control_rebuild'
    URL = '/control/rebuild'

    PATH_PAR_PAYLOAD = '/rebuild'
    PATH_PAR_URL = '/rebuild'

    METHOD = 'POST'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

    def executeByParameters(self) -> dict:
        payload = {}
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        remoteAddress = request.remote_addr

        logging.debug( "WEB request {1} {0} {2})".format(
                    remoteAddress, EPControlRebuild.METHOD, EPControlRebuild.URL
                )
        )

        output = {}

        logging.debug("Database rebuild started...")
        print("===========================")
        print("Database rebuild started...")
        self.web_gadget.db.drop_static_tables()
        start = time.time()
        self.web_gadget.db=DB(self.web_gadget)
        end = time.time()
        diff = end-start

        records = self.web_gadget.db.get_numbers_of_records_in_card()
        logging.debug("Collecting {0} pcs media took {1:.1f} seconds".format(records[0], diff))
        print("Collecting {0} pcs media took {1:.1f} seconds".format(records[0], diff))
        output["result"] = "SUCCESS"

#        self.web_gadget.db.drop_all_existing_tables()

#        c = "sudo /usr/bin/systemctl restart apache2"
#        try:
#            logging.error("Now I start to restart apache")
#            os.system(c)
#            logging.debug("Apache restarted successfully: {0}".format(""))
#            output["result"] = "SUCCESS"
#
#        except Exception as e:
#            logging.debug("Error restarting Apache: {0}".format(str(e)))
#            output["result"] = "EXCEPTION"
#            output["error"] = str(e)



#        try:
#            # Use subprocess to execute the command to restart Apache
#            # process = subprocess.run(["sudo /usr/bin/systemctl restart apache2"], capture_output=True,text=True, shell=True, check=True)
#            process = subprocess.run(['sudo /usr/sbin/service apache2 restart'], capture_output=True,text=True, shell=True, check=False)
#            # process = subprocess.run(["sudo /usr/bin/pwd"], capture_output=True,text=True, shell=True, check=True)
#            #process = subprocess.run(["whoami"], capture_output=True,text=True, shell=True, check=True)
#
#            logging.debug("Apache restarted successfully: {0}".format(str(process)))
#            output["result"] = "SUCCESS"
#            # print("Apache restarted successfully")
#        except subprocess.CalledProcessError as e:
#            logging.debug("Error restarting Apache: {0}".format(str(e)))
#            # print("Error restarting Apache: {0}".format(str(e)))
#            output["result"] = "EXCEPTION"
#            output["error"] = str(e)
#        # except Exception as f:
#        #     logging.debug("Other error. Error restarting Apache: {0}".format(str(f)))
#        #     print("Error restarting Apache: {0}".format(str(f)))
#        #     output["result"] = "EXCEPTION"
#        #     output["error"] = str(f)


        return output_json(output, EP.CODE_OK)
