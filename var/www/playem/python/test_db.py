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
    title_orig_lang="hu", 
    titles={"hu": "Csapdlecsacsi"}, 
    date="1990", 
    length="01:00:00",
    sounds=['hu'], 
    subs=[], 
    genres=['satire','drama'], 
    themes=['life'], 
    origins=['hu']
)

db.append_card_movie(
    title_orig_lang="sv", 
    titles={"hu": "Magyar cim", "sv": "Man som heter Ove", "en": "Man who is called Ove"}, 
    date="1989", 
    length="01:45:23",
    sounds=['sv','en'], 
    subs=['en','hu'], 
    genres=['crime','action'], 
    themes=['war'], 
    origins=['se', 'gb']
)

db.append_card_movie(
    title_orig_lang="sv", 
    titles={"hu": "Another movie", "sv": "Vem", "en": "Who"}, 
    date="1970", 
    length="00:20:00",
    sounds=['sv','en'], 
    subs=['en','sv'], 
    genres=['action'], 
    themes=['ai'], 
    origins=['se', 'no']
)

records=db.get_all_cards()
print(records)



