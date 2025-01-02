#! /var/www/homeflix/python/env/bin/python

import sys,os

# This text goes to the logs/error.log
print()
print()
print("=======================================================================")
print("The HOMEFLIX app started: {0}".format(__file__))
print("Python version: {0}".format(sys.version))
print("Python path: {0})".format(sys.executable))
print("=======================================================================")

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))

from homeflix.restserver.ws_homeflix import app as application
