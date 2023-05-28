#! /var/www/playem/python/env/bin/python

import sys,os

# This text goes to the logs/error.log
print()
print()
print("=======================================================================")
print("The playem app started: {0}".format(__file__))
print("Python version: {0}".format(sys.version))
print("Python path: {0})".format(sys.executable))
print("=======================================================================")

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))

from playem.restserver.ws_playem import app as application
