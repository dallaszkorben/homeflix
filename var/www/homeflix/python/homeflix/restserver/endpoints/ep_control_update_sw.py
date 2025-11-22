import logging
import subprocess
import time
import os
import shutil
from pathlib import Path

from homeflix.card.database import SqlDatabase as DB
from homeflix.config.config import getConfig
from homeflix.config.card_menu import CardMenu

from homeflix.exceptions.invalid_api_usage import InvalidAPIUsage
from homeflix.restserver.endpoints.ep import EP
from homeflix.restserver.representations import output_json

from flask import request

class EPControlUpdateSw(EP):

    ID = 'control_update_sw'
    URL = '/control/update/sw'

    PATH_PAR_PAYLOAD = '/update/sw'
    PATH_PAR_URL = '/update/sw'

    METHOD = 'POST'

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget
        self.project_path = self.web_gadget.projectPath

    def executeByParameters(self) -> dict:
        payload = {}
        return self.executeByPayload(payload)

    def executeByPayload(self, payload) -> dict:
        """
        Executes software update process in three phases:
        1. Git pull --rebase to update code
        2. Copy card_menu.yaml if it was modified
        3. Reload Apache server if both previous steps succeeded
        """
        remoteAddress = request.remote_addr

        logging.debug( "WEB request {1} {0} {2})".format(
                    remoteAddress, EPControlUpdateSw.METHOD, EPControlUpdateSw.URL
                )
        )

        # Initialize output structure for all three phases
        output = {'update':{}, 'reload':{}}

        # ===== PHASE 1: GIT PULL --REBASE =====
        # Update the codebase from remote repository
        logging.debug("Update code started...")
        print("===========================")
        print("Update code started...")

        # Execute git pull --rebase command in project directory
        process = subprocess.run(["cd {0}; git pull --rebase".format(self.project_path)], capture_output=True, text=True, shell=True, check=False)
        if process.returncode == 0:
            logging.debug("Update finished successfully: {0}".format(process.stdout))
            print("Update code finished")
            print(f"  result of pull: {process.stdout}")
            output["update"]["result"] = "SUCCESS"
            output["update"]["message"] = process.stdout
            output["update"]["command"] = process.args
        else:
            logging.debug("Update failed: {0}. Command: {1}".format(process.stderr, process.args))
            print("Update code failed: {0}. Command: {1}".format(process.stderr, process.args))
            output["update"]["result"] = "EXCEPTION"
            output["update"]["message"] = process.stderr
            output["update"]["command"] = process.args

        # ===== PHASE 2: COPY CARD_MENU.YAML =====
        # Copy configuration file only if git pull succeeded AND card_menu.yaml was modified

        copy_process_returncode = 0
        config = getConfig()

        # Check if git pull succeeded
        if process.returncode == 0:

            logging.debug("Copy card_menu.yaml started...")
            print("===========================")
            print("Copy card_menu.yaml started...")

            # If card_menu.yaml was NOT updated
            if config["card-menu-file-name"] not in output["update"]["message"]:
                logging.debug("Copy card_menu.yaml was skipped: {0}".format(output["update"]["message"]))
                print("Copy card_menu.yaml was skipped: {0}".format(output["update"]["message"]))

            # card_menu.yaml was updated - copy needed
            else:

                print("Copy card_menu.yaml started...")
                output['copy'] = {}

                # Source: card_menu.yaml from project repository
                source_file = os.path.join(config["project-path"], "home", "pi", ".homeflix", config["card-menu-file-name"])
                # Destination: user's .homeflix directory
                dest_file = os.path.join(config["path"], config["card-menu-file-name"])

                try:
                    if os.path.exists(source_file):
                        # Copy file preserving metadata (timestamps, permissions)
                        shutil.copy2(source_file, dest_file)
                        logging.debug(f"Copy card_menu.yaml finished successfully: {source_file} to {dest_file}")
                        print("Copy card_meny.yaml finished successfully")
                        output['copy']['result'] = "SUCCESS"
                        output['copy']['message'] = f"Successfully copied {CardMenu.CARD_MENU_FILE_NAME}"
                    else:
                        logging.warning(f"Copy card_menu.yaml failed, source file not found: {source_file}")
                        print("Copy card_menu.yaml failed: Source file not found.")
                        output['copy']['result'] = "EXCEPTION"
                        output['copy']['message'] = f"Source file not found: {source_file}"
                        copy_process_returncode = 1
                except Exception as e:
                    logging.error(f"Copy card_menu.yaml failed: {e}")
                    print(f"Copy card_menu.yaml failed: {e}")
                    output['copy']['result'] = "EXCEPTION"
                    output['copy']['message'] = str(e)
                    copy_process_returncode = 1

        # ===== PHASE 3: RELOAD APACHE SERVER =====
        # Reload server only if both git pull and copy operations succeeded
        if process.returncode == 0 and copy_process_returncode == 0:
            logging.debug("Reload server started...")
            print("===========================")
            print("Reload server started...")

            # Use systemctl to reload Apache2 (shell=False prevents shell injection)
            process = subprocess.run(["sudo", "/usr/bin/systemctl", "reload", "apache2"], capture_output=True, text=True, shell=False, check=False)

            if process.returncode == 0:
                logging.debug("Server reload finished successfully".format(process.stdout))
                print("Server reload finished")
                output["reload"]["result"] = "SUCCESS"
                output["reload"]["message"] = process.stdout
                output["reload"]["command"] = process.args
            else:
                logging.debug("Server reload failed: {0}. Command: {1}".format(process.stderr, process.args))
                print("Server reload failed: {0}. Command: {1}".format(process.stderr, process.args))
                output["reload"]["result"] = "EXCEPTION"
                output["reload"]["message"] = process.stderr
                output["reload"]["command"] = process.args

        # Return structured response with results from all phases
        return output_json(output, EP.CODE_OK)
