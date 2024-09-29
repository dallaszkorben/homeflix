#!env/bin/python
from playem.card.database import SqlDatabase as DB
from playem.config.config import Config

from playem.card.card_handle import CardHandle
#import playem.card.card_handle as card_handle

import sqlite3
#from sqlite3 import Error

config = Config()
media_path = config.getMediaAbsolutePath()
config_path = config.getConfigPath()


db=DB()

db.drop_tables()
db.create_tables()

#cardHandle = CardHandle
# TODO: have to fix
collectCardsFromFileSystem(media_path, db )


lang='hu'

# --- fetch all movie series with the title on the requested language ---
records = db.get_all_series_of_movies(lang=lang, limit=100)
print("\nMovie Series titles on '{0}' language and on original language".format(lang))
for record in records:
    if record["title_req"]:
        orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
        print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
    else:
        print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))

    # --- fetch the child hierarchy of the series - could be season or episode ---
    child_records = db.get_child_hierarchy_or_card(hierarchy_id=record["id"], lang=lang)
    for child_record in child_records:
        if child_record["level"]:
            print("         {0}".format(child_record["level"]), end=" ")
        else:
            print("         #{0} episode".format(child_record["sequence"]), end="  ")

        if child_record["title_req"]:
            title=child_record["title_req"]
        else:
            title=child_record["title_orig"]
        print(title)


# --- fetch all standalone movies with the title on the requested language ---
#records=db.get_standalone_movies_all(lang=lang, json=True, limit=100)
#for record in records:
#    print(record)

# --- fetch standalone movies with genre=action ---
print("Dramas:")
records=db.get_standalone_movies_by_genre(genre='drama', lang=lang, json=True, limit=100)
for record in records:    
    if record["title_req"]:
        orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
        print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
    else:
        print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))
