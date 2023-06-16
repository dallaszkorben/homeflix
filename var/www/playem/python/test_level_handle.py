#!env/bin/python
from playem.card.database import SqlDatabase as DB
from playem.config.config import Config

from playem.card.card_handle import collectCardsFromFileSystem
import playem.card.card_handle as card_handle

import sqlite3
from sqlite3 import Error

config = Config()
media_path = config.getMediaAbsolutePath()
config_path = config.getConfigPath()


db=DB()

db.drop_tables()
db.create_tables()

collectCardsFromFileSystem(media_path, db )


lang='hu'

# --- fetch all standalone movies with the title on the requested language ---
records=db.get_all_standalone_movie(lang=lang, limit=100)
print("\nStandalone movies titles on '{0}' language and on original language".format(lang))
for record in records:
    if record["title_req"]:
        orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
        print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
    else:
        print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))
    print("              Source: {0}".format(record["source_path"]))


# --- fetch all movie series with the title on the requested language ---
records=db.get_series_of_movies(lang=lang, limit=100)
print("\nMovie Series titles on '{0}' language and on original language".format(lang))
for record in records:
    if record["title_req"]:
        orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
        print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
    else:
        print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))
    print("              Source: {0}".format(record["source_path"]))










