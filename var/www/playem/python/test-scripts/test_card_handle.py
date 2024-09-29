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

records=db.get_all_cards()

for id, record in records.items():

    print("Id: {0}, Title: {1}".format(id, record['title']))
    print("    Original Title: {0}".format(record['original_title']))

    print("    Category:       {0}".format(record['category']))
    print("    Storyline:      {0}".format(record['storyline']))
    print("    Date:           {0}".format(record['date']))
    print("    Length:         {0}".format(record['length']))

    print("    Sound:          {0}".format(record['sounds']))
    print("    Sub:            {0}".format(record['subs']))
    print("    Genre:          {0}".format(record['genres']))
    print("    Theme:          {0}".format(record['themes']))
    print("    Origin:         {0}".format(record['origins']))

    print("    Source Path:    {0}".format(record['source_path']))
    print("    Media:          {0}".format(record['media']))
    print("    Media type:     {0}".format(record['mtypes']))









