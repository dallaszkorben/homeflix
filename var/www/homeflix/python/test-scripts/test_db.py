#!env/bin/python
from playem.card.database import SqlDatabase as DB
from playem.config.config import Config

import sqlite3
from sqlite3 import Error

config = Config()
media_path = config.getMediaAbsolutePath()
config_path = config.getConfigPath()

def translate(value, language):
    tr ={
        'hu': {'gen_drama': 'dráma', 'gen_comedy': 'vígjáték', 'gen_crime': 'bűnügy', 'gen_action': 'akció'},
        'en': {'gen_drama': 'drama', 'gen_comedy': 'comedu', 'gen_crime': 'crime', 'gen_action': 'action'},
    }

    try:
        ret=tr[language][value]
    except:
        ret=value

    return ret
    




db=DB()
db.drop_tables()
db.create_tables()



db.append_card_movie(
    category="movie",
    mtypes=["video"],
    title_orig="hu", 
    titles={"hu": "Csapdlecsacsi"}, 
    storylines={"hu": "Ez egy nagyon jo film"},
    date="1990", 
    length="01:00:00",
    sounds=['hu'], 
    subs=[], 
    genres=['satire','drama'], 
    themes=['life'], 
    origins=['hu'],

    source_path='/var/dfdsf/fgsfd',
    media=['movie.mkv']
)

db.append_card_movie(
    category="music",
    mtypes=["video"],
    title_orig="sv", 
    titles={"hu": "Ember akit Ovenek hívnak", "sv": "Man som heter Ove", "en": "Man who is called Ove"}, 
    storylines={"hu": "Vicces történet", "en": "Very interesting movie"},
    date="1989", 
    length="01:45:23",
    sounds=['sv','en'], 
    subs=['en','hu'], 
    genres=['crime','action'], 
    themes=['war'], 
    origins=['se', 'gb'],

    source_path='/var/dfdsf/fgsfd',
    media=['movie2.mkv']
)

db.append_card_movie(
    category="radio_play",
    mtypes=["audio"],
    title_orig="sv", 
    titles={"hu": "Another movie", "sv": "Vem", "en": "Who"}, 
    storylines={"hu": "Ezt a filmet nem ismerem", "en": "I do not know this movie"},
    date="1970", 
    length="00:20:00",
    sounds=['sv','en'], 
    subs=['en','sv'], 
    genres=['action'], 
    themes=['ai'], 
    origins=['se', 'no'],

    source_path='/var/dfdsf/fgsfd',
    media=['music.mp3']
)

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


    # print("Id: {0}, Original title: {1}".format(id, record['title'][record['title_orig']]))
    # print("    Category:    {0}".format(record['category']))
    # print("    Storyline:   {0}".format(record['storyline']))
    # print("    Date:        {0}".format(record['date']))
    # print("    Length:      {0}".format(record['length']))

    # print("    Sound:       {0}".format(record['sound']))
    # print("    Sub:         {0}".format(record['sub']))
    # print("    Genre:       {0}".format(record['genre']))
    # print("    Theme:       {0}".format(record['theme']))
    # print("    Source Path: {0}".format(record['source_path']))
    # print("    Media:       {0}".format(record['media']))






