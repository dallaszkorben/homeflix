import os
import sqlite3
import logging
from threading import Lock
from sqlite3 import Error
from datetime import datetime, timedelta

from playem.config.config import getConfig
from playem.translator.translator import Translator
from playem.exceptions.not_existing_table import NotExistingTable


class SqlDatabase:

    TABLE_CATEGORY = "Category"
    TABLE_PERSON = "Person"
    TABLE_COUNTRY = "Country"
    TABLE_LANGUAGE = "Language"
    TABLE_GENRE = "Genre"
    TABLE_THEME = "Theme"
    TABLE_MEDIATYPE = "MediaType"

    TABLE_CARD = "Card"

    TABLE_CARD_GENRE = "Card_Genre"
    TABLE_CARD_THEME = "Card_Theme"
    TABLE_CARD_MEDIA = "Card_Media"
    TABLE_CARD_SOUND = "Card_Sound"
    TABLE_CARD_SUB = "Card_Sub"
    TABLE_CARD_ORIGIN = "Card_Origin"
    TABLE_CARD_ACTOR = "Card_Actor"
    TABLE_CARD_STAR = "Card_Star"
    TABLE_CARD_WRITER = "Card_Writer"
    TABLE_CARD_DIRECTOR = "Card_Director"
    TABLE_CARD_VOICE = "Card_Voice"
    TABLE_CARD_HOST = "Card_Host"
    TABLE_CARD_GUEST = "Card_Guest"
    TABLE_CARD_INTERVIEWER = "Card_Interviewer"
    TABLE_CARD_INTERVIEWEE = "Card_Interviewee"
    TABLE_CARD_PRESENTER = "Card_Presenter"
    TABLE_CARD_LECTURER = "Card_Lecturer"
    TABLE_CARD_PERFORMER = "Card_Performer"
    TABLE_CARD_REPORTER = "Card_Reporter"
    TABLE_TEXT_CARD_LANG = "Text_Card_Lang"

    TABLE_ROLE = "Role"
    TABLE_ACTOR_ROLE = "Actor_Role"

    TABLE_USER = "User"
    TABLE_HISTORY = "History"
    TABLE_TAG = "Tag"

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

        config = getConfig()
        self.db_path = os.path.join(config["path"], config['card-db-name'])
        self.mediaAbsolutePath = config["media-absolute-path"]
        self.translator = Translator.getInstance("en")

        self.language = self.translator.get_actual_language_code()

        self.table_static_list = [
            SqlDatabase.TABLE_TEXT_CARD_LANG,
            SqlDatabase.TABLE_CARD_MEDIA,
            SqlDatabase.TABLE_CARD_VOICE,
            SqlDatabase.TABLE_CARD_WRITER,
            SqlDatabase.TABLE_CARD_DIRECTOR,
            SqlDatabase.TABLE_CARD_ACTOR,
            SqlDatabase.TABLE_CARD_STAR,
            SqlDatabase.TABLE_CARD_HOST,
            SqlDatabase.TABLE_CARD_GUEST,
            SqlDatabase.TABLE_CARD_INTERVIEWER,
            SqlDatabase.TABLE_CARD_INTERVIEWEE,
            SqlDatabase.TABLE_CARD_PRESENTER,
            SqlDatabase.TABLE_CARD_LECTURER,
            SqlDatabase.TABLE_CARD_PERFORMER,
            SqlDatabase.TABLE_CARD_REPORTER,

            SqlDatabase.TABLE_CARD_ORIGIN,
            SqlDatabase.TABLE_CARD_GENRE,
            SqlDatabase.TABLE_CARD_THEME,
            SqlDatabase.TABLE_CARD_SOUND,
            SqlDatabase.TABLE_CARD_SUB,

            SqlDatabase.TABLE_CARD,

            SqlDatabase.TABLE_COUNTRY,
            SqlDatabase.TABLE_LANGUAGE,

            SqlDatabase.TABLE_GENRE,
            SqlDatabase.TABLE_THEME,
            SqlDatabase.TABLE_PERSON,
            SqlDatabase.TABLE_MEDIATYPE,
            SqlDatabase.TABLE_CATEGORY,

            SqlDatabase.TABLE_ROLE,
            SqlDatabase.TABLE_ACTOR_ROLE,
        ]

        self.table_personal_list = [
            SqlDatabase.TABLE_USER,
            SqlDatabase.TABLE_HISTORY,
            SqlDatabase.TABLE_TAG,
        ]

        self.lock = Lock()

        # create connection
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=20)
            logging.debug( "Connection to {0} SQLite was successful".format(self.db_path))
            self.conn.row_factory = sqlite3.Row 
        except Error as e:
            logging.error( "Connection to {0} SQLite failed. Error: {1}".format(self.db_path, e))

            # TODO: handle this case
            exit()

        # check if the static databases are corrupted/not existed
        if not self.is_static_dbs_ok():
            self.recreate_static_dbs()

        self.fill_up_constant_dicts()

        # check if the personal databases are corrupted/not existed
        if not self.is_personal_dbs_ok():
            self.recreate_personal_dbs()


    def __del__(self):
        self.conn.close()


    def is_static_dbs_ok(self):
        error_code = 1001
        cur = self.conn.cursor()
        cur.execute("begin")

        try:
            for table in self.table_static_list:
                query ="SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{0}' ".format(table)
                records = cur.execute(query).fetchone()
                if records[0] != 1:
                    raise NotExistingTable("{0} 'Static' table does not exist. All 'Static' tables will be recreated".format(table), error_code)

        except NotExistingTable as e:
            logging.debug(e.message)   
            return False

        finally:
            cur.execute("commit")
        return True


    def is_personal_dbs_ok(self):
        error_code = 1001
        cur = self.conn.cursor()
        cur.execute("begin")

        try:
            for table in self.table_personal_list:
                query ="SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{0}' ".format(table)
                records = cur.execute(query).fetchone()
                if records[0] != 1:
                    raise NotExistingTable("{0} 'Personal' table does not exist. All 'Personal' tables will be recreated".format(table), error_code)

        except NotExistingTable as e:
            logging.debug(e.message)   
            return False

        finally:
            cur.execute("commit")
        return True


    def recreate_static_dbs(self):

        # Create new empty databases
        self.drop_static_tables()
        logging.debug("All static tables are dropped")
        self.create_static_tables()
        logging.debug("All static tables are recreated")

        # Fill up the database
        self.web_gadget.cardHandle.collectCardsFromFileSystem(self.mediaAbsolutePath, self )


    def recreate_personal_dbs(self):

        # Create new empty databases
        self.drop_personal_tables()
        logging.debug("All personal tables are dropped")
        self.create_personal_tables()
        logging.debug("All personal tables are recreated")


    def drop_static_tables(self):
        cur = self.conn.cursor()
        cur.execute("begin")
#        tables_all = list(cur.execute("SELECT name FROM sqlite_master WHERE type is 'table'"))
        cur.execute("commit")

#        for table in tables_all:
        for table in self.table_static_list:
            try:
#                self.conn.execute("DROP TABLE {0}".format(table[0]))
                self.conn.execute("DROP TABLE {0}".format(table))
            except sqlite3.OperationalError as e:
#                logging.error("Error while DROP TABLE ({0}): {1}".format(table[0], e))
                logging.error("Wanted to Drop '{0}' 'Static' table, but error happened: {1}".format(table, e))

    def drop_personal_tables(self):
        for table in self.table_personal_list:
            try:
                self.conn.execute("DROP TABLE {0}".format(table))
            except sqlite3.OperationalError as e:
                logging.error("Wanted to Drop '{0}' 'Personal' table, but error happened: {1}".format(table, e))


    def create_personal_tables(self):

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_USER + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name                   TEXT    NOT NULL,
                id_language            INTEGER NOT NULL ,
                show_original_title    BOOLEAN NOT NULL CHECK (show_original_title IN (0, 1)),
                show_lyrics_anyway     BOOLEAN NOT NULL CHECK (show_lyrics_anyway IN (0, 1)),
                show_storyline_anyway  BOOLEAN NOT NULL CHECK (show_storyline_anyway IN (0, 1)),
                play_continuously      BOOLEAN NOT NULL CHECK (play_continuously IN (0, 1)),
                created_epoch          INTEGER NOT NULL,
                FOREIGN KEY (id_language) REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                UNIQUE(name)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_HISTORY + '''(
                start_epoch   INTEGER NOT NULL,
                last_epoch    INTEGER NOT NULL,
                last_position TEXT    NOT NULL,
                id_card       INTEGER NOT NULL,
                id_user       INTEGER NOT NULL,
                FOREIGN KEY   (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY   (id_user) REFERENCES ''' + SqlDatabase.TABLE_USER + ''' (id),
                PRIMARY KEY   (id_card, id_user, start_epoch)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_TAG + '''(
                name          TEXT  NOT NULL,
                id_card       INTEGER NOT NULL,
                id_user       INTEGER NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_user) REFERENCES ''' + SqlDatabase.TABLE_USER + ''' (id),
                PRIMARY KEY (id_card, id_user, name)
            );
        ''')

        self.fill_up_user_table()


    def fill_up_user_table(self):
        cur = self.conn.cursor()
        cur.execute("begin")

        # admin
        user_name = "admin"
        user_id = 1234
        language_code = 'en'
        show_original_title = True
        show_lyrics_anyway = True
        show_storyline_anyway = True
        play_continuously = True

        id = self.append_user(cur, user_name, user_id=user_id, language_code=language_code, show_original_title=show_original_title, show_lyrics_anyway=show_lyrics_anyway, show_storyline_anyway=show_storyline_anyway, play_continuously=play_continuously)
        self.user_name = user_name

        cur.execute("commit")


    def create_static_tables(self):

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CATEGORY + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL,
                UNIQUE(name)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_PERSON + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_COUNTRY + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL,
                UNIQUE(name)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_LANGUAGE + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL,
                UNIQUE(name)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_THEME + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL,
                UNIQUE(name)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_GENRE + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL,
                UNIQUE(name)
            );
        ''')

        result=self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_MEDIATYPE + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL,
                UNIQUE(name)
            );
        ''')




        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD + '''(
                id                  INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                id_title_orig       INTEGER     NOT NULL,
                id_category         INTEGER     NOT NULL,
                isappendix          BOOLEAN     NOT NULL CHECK (isappendix IN (0, 1)),
                show                BOOLEAN     NOT NULL CHECK (show IN (0, 1)),
                download            BOOLEAN     NOT NULL CHECK (download IN (0, 1)),
                decade              TEXT,
                date                TEXT,
                length              TEXT,
                source_path         TEXT        NOT NULL,
                basename            TEXT        NOT NULL,
                sequence            INTEGER,
                id_higher_card      INTEGER,
                level               TEXT,
                title_on_thumbnail  BOOLEAN     NOT NULL CHECK (title_on_thumbnail IN (0, 1)),
                title_show_sequence TEXT        NOT NULL,
                FOREIGN KEY (id_title_orig) REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                FOREIGN KEY (id_higher_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id) 
            );
        ''')





        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_GENRE + '''(
                id_card INTEGER      NOT NULL,
                id_genre INTEGER      NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_genre) REFERENCES ''' + SqlDatabase.TABLE_GENRE + ''' (id),
                PRIMARY KEY (id_card, id_genre) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_THEME + '''(
                id_card INTEGER      NOT NULL,
                id_theme INTEGER      NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_theme) REFERENCES ''' + SqlDatabase.TABLE_THEME + ''' (id),
                PRIMARY KEY (id_card, id_theme) 
            );
        ''' )

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_SOUND + '''(
                id_card INTEGER      NOT NULL,
                id_sound INTEGER      NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_sound) REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                PRIMARY KEY (id_card, id_sound) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_SUB + '''(
                id_card INTEGER      NOT NULL,
                id_sub  INTEGER      NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_sub) REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                PRIMARY KEY (id_card, id_sub) 
            );
        ''' )

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_ORIGIN + '''(
                id_card   INTEGER      NOT NULL,
                id_origin INTEGER      NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_origin) REFERENCES ''' + SqlDatabase.TABLE_COUNTRY + ''' (id),
                PRIMARY KEY (id_card, id_origin) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_ACTOR + '''(
                id_card INTEGER        NOT NULL,
                id_actor INTEGER       NOT NULL,
                FOREIGN KEY (id_card)  REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_actor) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_actor) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_STAR + '''(
                id_card INTEGER        NOT NULL,
                id_star INTEGER       NOT NULL,
                FOREIGN KEY (id_card)  REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_star) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_star) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_VOICE + '''(
                id_card INTEGER        NOT NULL,
                id_voice INTEGER       NOT NULL,
                FOREIGN KEY (id_card)  REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_voice) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_voice) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_DIRECTOR + '''(
                id_card INTEGER           NOT NULL,
                id_director INTEGER       NOT NULL,
                FOREIGN KEY (id_card)     REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_director) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_director) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_WRITER + '''(
                id_card INTEGER          NOT NULL,
                id_writer INTEGER        NOT NULL,
                FOREIGN KEY (id_card)    REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_writer)  REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_writer) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_HOST + '''(
                id_card INTEGER          NOT NULL,
                id_host INTEGER          NOT NULL,
                FOREIGN KEY (id_card)    REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_host)    REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_host) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_GUEST + '''(
                id_card INTEGER          NOT NULL,
                id_guest INTEGER         NOT NULL,
                FOREIGN KEY (id_card)    REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_guest)   REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_guest) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_INTERVIEWER + '''(
                id_card INTEGER              NOT NULL,
                id_interviewer INTEGER       NOT NULL,
                FOREIGN KEY (id_card)        REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_interviewer) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_interviewer) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_INTERVIEWEE + '''(
                id_card INTEGER              NOT NULL,
                id_interviewee INTEGER       NOT NULL,
                FOREIGN KEY (id_card)        REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_interviewee) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_interviewee) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_PRESENTER + '''(
                id_card INTEGER            NOT NULL,
                id_presenter INTEGER       NOT NULL,
                FOREIGN KEY (id_card)      REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_presenter) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_presenter) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_LECTURER + '''(
                id_card INTEGER            NOT NULL,
                id_lecturer INTEGER        NOT NULL,
                FOREIGN KEY (id_card)      REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_lecturer)  REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_lecturer) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_PERFORMER + '''(
                id_card INTEGER             NOT NULL,
                id_performer INTEGER        NOT NULL,
                FOREIGN KEY (id_card)       REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_performer)  REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_performer) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_REPORTER + '''(
                id_card INTEGER            NOT NULL,
                id_reporter INTEGER        NOT NULL,
                FOREIGN KEY (id_card)      REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_reporter)  REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_reporter) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + '''(
                text         TEXT          NOT NULL,
                id_language  INTEGER       NOT NULL,
                id_card      INTEGER       NOT NULL,
                type         TEXT          NOT NULL,
                FOREIGN KEY (id_language)  REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                FOREIGN KEY (id_card)      REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                PRIMARY KEY (id_card, id_language, type)
            );
        ''' )

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_MEDIA + '''(
                name         TEXT     NOT NULL,
                id_card      INTEGER  NOT NULL,
                id_mediatype INTEGER  NOT NULL,

                FOREIGN KEY (id_card)      REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id), 
                FOREIGN KEY (id_mediatype) REFERENCES ''' + SqlDatabase.TABLE_MEDIATYPE + ''' (id),
                PRIMARY KEY (id_card, id_mediatype, name)
            );
        ''' )








        self.conn.execute('''
           CREATE TABLE ''' + SqlDatabase.TABLE_ROLE + '''(
               id      INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
               id_card INTEGER     NOT NULL,
               name    TEXT        NOT NULL,
               FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
               UNIQUE (id_card, name)
           );
        ''')

        self.conn.execute('''
           CREATE TABLE ''' + SqlDatabase.TABLE_ACTOR_ROLE + '''(
               id_actor      INTEGER  NOT NULL,
               id_role       INTEGER  NOT NULL,
               FOREIGN KEY (id_actor)     REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id), 
               FOREIGN KEY (id_role)      REFERENCES ''' + SqlDatabase.TABLE_ROLE + ''' (id),
               PRIMARY KEY (id_actor, id_role)
           );
        ''' )

        self.fill_up_theme_table_from_dict()
        self.fill_up_genre_table_from_dict()
        self.fill_up_language_table_from_dict()
        self.fill_up_country_table_from_dict()
        self.fill_up_category_table_from_dict()
        self.fill_up_mediatype_table_from_dict()

    def fill_up_constant_dicts(self):
        self.category_name_id_dict = {}
        self.genre_name_id_dict = {}
        self.theme_name_id_dict = {}
        self.language_name_id_dict = {}
        self.country_name_id_dict = {}
        self.mediatype_name_id_dict = {}

        self.category_id_name_dict = {}
        self.genre_id_name_dict = {}
        self.theme_id_name_dict = {}
        self.language_id_name_dict = {}
        self.country_id_name_dict = {}
        self.mediatype_id_name_dict = {}

        cur = self.conn.cursor()
        cur.execute("begin")

        query = 'SELECT name, id FROM ' + SqlDatabase.TABLE_CATEGORY + ' ORDER BY name;'
        records = cur.execute(query).fetchall()
        for pair in records:
            self.category_name_id_dict[pair[0]] = pair[1]
            self.category_id_name_dict[pair[1]] = pair[0]

        query = 'SELECT name, id FROM ' + SqlDatabase.TABLE_GENRE + ' ORDER BY name;'
        records = cur.execute(query).fetchall()
        for pair in records:
            self.genre_name_id_dict[pair[0]] = pair[1]
            self.genre_id_name_dict[pair[1]] = pair[0]

        query = 'SELECT name, id FROM ' + SqlDatabase.TABLE_THEME + ' ORDER BY name;'
        records = cur.execute(query).fetchall()
        for pair in records:
            self.theme_name_id_dict[pair[0]] = pair[1]
            self.theme_id_name_dict[pair[1]] = pair[0]

        query = 'SELECT name, id FROM ' + SqlDatabase.TABLE_MEDIATYPE + ' ORDER BY name;'
        records = cur.execute(query).fetchall()
        for pair in records:
            self.mediatype_name_id_dict[pair[0]] = pair[1]
            self.mediatype_id_name_dict[pair[1]] = pair[0]

        query = 'SELECT name, id FROM ' + SqlDatabase.TABLE_LANGUAGE + ' ORDER BY name;'
        records = cur.execute(query).fetchall()
        for pair in records:
            self.language_name_id_dict[pair[0]] = pair[1]
            self.language_id_name_dict[pair[1]] = pair[0]

        query = 'SELECT name, id FROM ' + SqlDatabase.TABLE_COUNTRY + ' ORDER BY name;'
        records = cur.execute(query).fetchall()
        for pair in records:
            self.country_name_id_dict[pair[0]] = pair[1]
            self.country_id_name_dict[pair[1]] = pair[0]

        cur.execute("commit")

    def fill_up_category_table_from_dict(self):
        cur = self.conn.cursor()
        cur.execute("begin")
        self.category_name_id_dict = {}
        self.category_id_name_dict = {}
        category_list = self.translator.get_all_category_codes()
        for category in category_list:
            id = self.append_category(cur, category)
            self.category_name_id_dict[category] = id
            self.category_id_name_dict[id] = category
        cur.execute("commit")

    def fill_up_genre_table_from_dict(self):
        cur = self.conn.cursor()
        cur.execute("begin")
        self.genre_name_id_dict = {}
        self.genre_id_name_dict = {}
        genre_list = self.translator.get_all_genre_codes()
        for genre in genre_list:
            id = self.append_genre(cur, genre)
            self.genre_name_id_dict[genre] = id
            self.genre_id_name_dict[id] = genre
        cur.execute("commit")

    def fill_up_mediatype_table_from_dict(self):
        cur = self.conn.cursor()
        cur.execute("begin")
        self.mediatype_name_id_dict = {}
        self.mediatype_id_name_dict = {}
        mediatype_list = self.translator.get_all_mediatype_codes()
        for mediatype in mediatype_list:
            id = self.append_mediatype(cur, mediatype)
            self.mediatype_name_id_dict[mediatype] = id
            self.mediatype_id_name_dict[id] = mediatype
        cur.execute("commit")

    def fill_up_theme_table_from_dict(self):
        cur = self.conn.cursor()
        cur.execute("begin")
        self.theme_name_id_dict = {}
        self.theme_id_name_dict = {}
        theme_list = self.translator.get_all_theme_codes()
        for theme in theme_list:
            id = self.append_theme(cur, theme)
            self.theme_name_id_dict[theme] = id
            self.theme_id_name_dict[id] = theme
        cur.execute("commit")

    def fill_up_language_table_from_dict(self):
        cur = self.conn.cursor()
        cur.execute("begin")
        self.language_name_id_dict = {}
        self.language_id_name_dict = {}
        lang_list = self.translator.get_all_language_codes()
        for lang in lang_list:
            id = self.append_language(cur, lang)
            self.language_name_id_dict[lang] = id
            self.language_id_name_dict[id] = lang
        cur.execute("commit")

    def fill_up_country_table_from_dict(self):
        cur = self.conn.cursor()
        cur.execute("begin")
        self.country_name_id_dict = {}        
        self.country_id_name_dict = {}        
        country_list = self.translator.get_all_country_codes()
        for country in country_list:
            id = self.append_country(cur, country)
            self.country_name_id_dict[country] = id
            self.country_id_name_dict[id] = country
        cur.execute("commit")

    def append_user(self, cur, user_name, user_id=None, language_code="en", show_original_title=True, show_lyrics_anyway=True, show_storyline_anyway=True, play_continuously=True):
        created_epoch = int(datetime.now().timestamp())
        id_language = self.language_name_id_dict[language_code]
        if user_id:
            cur.execute('INSERT INTO ' + SqlDatabase.TABLE_USER + ' (name, id, created_epoch, id_language, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously) VALUES (:user_name, :user_id, :created_epoch, :id_language, :show_original_title, :show_lyrics_anyway, :show_storyline_anyway, :play_continuously) RETURNING id', (user_name, user_id, created_epoch, id_language, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously))
        else:
            cur.execute('INSERT INTO ' + SqlDatabase.TABLE_USER + ' (name, created_epoch, id_language, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously) VALUES (:user_name, :created_epoch, :id_language, :show_original_title, :show_lyrics_anyway, :show_storyline_anyway, :play_continuously) RETURNING id', (user_name, created_epoch, id_language, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously))
        record = cur.fetchone()
        (user_id, ) = record if record else (None,)
        return user_id

    def append_category(self, cur, category):
        #cur = self.conn.cursor()
        cur.execute('INSERT INTO ' + SqlDatabase.TABLE_CATEGORY + ' (name) VALUES (?) RETURNING id', (category,))
        record = cur.fetchone()
        (category_id, ) = record if record else (None,)
        return category_id

    def append_language(self, cur, sound):
        #cur = self.conn.cursor()
        cur.execute('INSERT INTO ' + SqlDatabase.TABLE_LANGUAGE + ' (name) VALUES (?) RETURNING id', (sound,))
        record = cur.fetchone()
        (language_id, ) = record if record else (None,)
        return language_id

    def append_country(self, cur, origin):
        cur.execute('INSERT INTO ' + SqlDatabase.TABLE_COUNTRY + ' (name) VALUES (?) RETURNING id', (origin,))
        record = cur.fetchone()
        (country_id, ) = record if record else (None,)
        return country_id

    def append_genre(self, cur, genre):
        cur.execute('INSERT INTO ' + SqlDatabase.TABLE_GENRE + ' (name) VALUES (?) RETURNING id', (genre,))
        record = cur.fetchone()
        (genre_id, ) = record if record else (None,)
        return genre_id

    def append_theme(self, cur, theme):
        cur.execute('INSERT INTO ' + SqlDatabase.TABLE_THEME + ' (name) VALUES (?) RETURNING id', (theme,))
        record = cur.fetchone()
        (theme_id, ) = record if record else (None,)
        return theme_id

    def append_mediatype(self, cur, mediatype):
        cur.execute('INSERT INTO ' + SqlDatabase.TABLE_MEDIATYPE + ' (name) VALUES (?) RETURNING id', (mediatype,))
        record = cur.fetchone()
        (mediatype_id, ) = record if record else (None,)
        return mediatype_id

    def append_card_media(self, card_path, title_orig, titles={}, title_on_thumbnail=1, title_show_sequence='', show=1, download=0, card_id=None, isappendix=0, category=None, storylines={}, lyrics={}, decade=None, date=None, length=None, sounds=[], subs=[], genres=[], themes=[], origins=[], writers=[], actors=[], stars=[], directors=[], voices=[], hosts=[], guests=[], interviewers=[], interviewees=[], presenters=[], lecturers=[], performers=[], reporters=[], media={}, basename=None, source_path=None, sequence=None, higher_card_id=None):

        # logging.error( "title_on_thumbnail: '{0}', title_show_sequence: '{1}'".format(title_on_thumbnail, title_show_sequence))

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            title_orig_id = self.language_name_id_dict[title_orig]
            category_id = self.category_name_id_dict[category]

            #
            # INSERT into CARD
            #
            # if the card has its own ID, meaning it is media card
            if card_id:

                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                        (id, show, download, isappendix, id_title_orig, title_on_thumbnail, title_show_sequence, id_category, decade, date, length, basename, source_path, id_higher_card, sequence)
                        VALUES (:id, :show, :download, :isappendix, :id_title_orig, :title_on_thumbnail, :title_show_sequence, :id_category, :decade, :date, :length, :basename, :source_path, :id_higher_card, :sequence)
                        RETURNING id;
                '''
            else:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                        (show, download, isappendix, id_title_orig, title_on_thumbnail, title_show_sequence, id_category, decade, date, length, basename, source_path, id_higher_card, sequence)
                        VALUES (:show, :download, :isappendix, :id_title_orig, :title_on_thumbnail, :title_show_sequence, :id_category, :decade, :date, :length, :basename, :source_path, :id_higher_card, :sequence)
                        RETURNING id;
                '''
            cur.execute(query, {'id': card_id, 'show': show, 'download': download, 'isappendix': isappendix, 'id_title_orig': title_orig_id, 'title_on_thumbnail': title_on_thumbnail, 'title_show_sequence': title_show_sequence, 'id_category': category_id, 'decade': decade, 'date': date, 'length': length, 'basename': basename, 'source_path': source_path, 'id_higher_card': higher_card_id, 'sequence': sequence})

            record = cur.fetchone()
            (card_id, ) = record if record else (None,)

            #
            # INSERT into TABLE_CARD_WRITER
            #
            for writer in writers:

                if writer:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': writer}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': writer})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_WRITER + ''' 
                            (id_writer, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_ACTOR
            #
            if isinstance(actors, list):

                tmp_actors = {}
                for key in actors:
                    tmp_actors[key] = ""
                actors = tmp_actors

            for actor, role in actors.items():

                if actor:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': actor}).fetchone()
                    (person_id, ) = record if record else (None,)

                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': actor})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_ACTOR + ''' 
                            (id_actor, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

##################################

                    # Ask if there is Role for this Card
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_ROLE + '''
                        WHERE name= :name AND id_card= :card_id;
                    '''
                    record=cur.execute(query, {'name': role, 'card_id': card_id}).fetchone()
                    (role_id, ) = record if record else (None,)

                    # If the Role does not exist for the Card
                    if not role_id:

                        # Creates to Role
                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_ROLE + ''' 
                           (id_card, name) 
                           VALUES (:card_id, :name);'''
                        res = cur.execute(query, {'card_id': card_id, 'name': role})
                        role_id = res.lastrowid

                    # Connects the Role to the Actor
                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_ACTOR_ROLE + ''' 
                        (id_actor, id_role) 
                        VALUES (:person_id, :role_id);'''
                    cur.execute(query, {'person_id': person_id, 'role_id': role_id})

                    # logging.error( "    card_id: '{0}'. person_id: {1}. Person: {2}. role_id: {3}. Role: {4}.".format(card_id, person_id, actor, role_id, role))
                    # logging.error( "    card_id: '{0}'. person_id: {1}. Person: {2}. Role: {3}.".format(card_id, person_id, actor, role))



#                    logging.error( "TEST - there is actor: '{0}'. From select query: {1}. Person Id: {2}".format(actor, record, person_id))
###################################33

            #
            # INSERT into TABLE_CARD_STARS
            #
            for star in stars:

                if star:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': star}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': star})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_STAR + ''' 
                            (id_star, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_DIRECTOR
            #
            for director in directors:

                if director:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': director}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': director})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_DIRECTOR + ''' 
                            (id_director, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_VOICE
            #
            for voice in voices:

                if voice:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': voice}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': voice})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_VOICE + ''' 
                            (id_voice, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_HOST
            #
            for host in hosts:

                if host:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': host}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': host})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_HOST + ''' 
                            (id_host, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})


            #
            # INSERT into TABLE_CARD_GUEST
            #
            for guest in guests:

                if guest:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': guest}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': guest})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_GUEST + ''' 
                            (id_guest, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_INTERVIEWER
            #
            for interviewer in interviewers:

                if interviewer:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': interviewer}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': interviewer})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_INTERVIEWER + ''' 
                            (id_interviewer, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_INTERVIEWEE
            #
            for interviewee in interviewees:

                if interviewee:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': interviewee}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': interviewee})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_INTERVIEWEE + ''' 
                            (id_interviewee, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_PRESENTER
            #
            for presenter in presenters:

                if presenter:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': presenter}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': presenter})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_PRESENTER + ''' 
                            (id_presenter, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_LECTURER
            #
            for lecturer in lecturers:

                if lecturer:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': lecturer}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': lecturer})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_LECTURER + ''' 
                            (id_lecturer, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_PERFORMER
            #
            for performer in performers:

                if performer:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': performer}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': performer})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_PERFORMER + ''' 
                            (id_performer, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_REPORTER
            #
            for reporter in reporters:

                if reporter:
                    query = '''SELECT id FROM ''' + SqlDatabase.TABLE_PERSON + '''
                        WHERE name= :name;
                    '''
                    record=cur.execute(query, {'name': reporter}).fetchone()
                    (person_id, ) = record if record else (None,)
                    if not person_id:

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_PERSON + ''' 
                                (name) 
                                VALUES (:name);'''
                        res = cur.execute(query, {'name': reporter})
                        person_id = res.lastrowid

                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_REPORTER + ''' 
                            (id_reporter, id_card) 
                            VALUES (:person_id, :card_id);'''
                    cur.execute(query, {'person_id': person_id, 'card_id': card_id})

            #
            # INSERT into TABLE_CARD_SOUND
            #
            for sound in sounds:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_SOUND + '''
                    (id_sound, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.language_name_id_dict[sound], card_id))

            #
            # INSERT into TABLE_CARD_SUB
            #
            for sub in subs:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_SUB + '''
                    (id_sub, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.language_name_id_dict[sub], card_id))

            #
            # INSERT into TABLE_CARD_GENRE
            #
            for sub in genres:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_GENRE + '''
                    (id_genre, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.genre_name_id_dict[sub], card_id))

            #
            # INSERT into TABLE_CARD_THEME
            #
            for theme in themes:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_THEME + '''
                    (id_theme, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.theme_name_id_dict[theme], card_id))

            #
            # INSERT into TABLE_CARD_ORIGIN
            #
            for origin in origins:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_ORIGIN + '''
                    (id_origin, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.country_name_id_dict[origin], card_id))

            #
            # INSERT into TABLE_TEXT_CARD_LANG Title
            #
            for lang, title in titles.items():
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + '''
                    (id_language, id_card, text, type)
                    VALUES (?, ?, ?, "T");
                '''
                cur.execute(query, (self.language_name_id_dict[lang], card_id, title))    

            #
            # INSERT into TABLE_TEXT_CARD_LANG Storyline
            #
            for lang, storyline in storylines.items():
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + '''
                    (id_language, id_card, text, type)
                    VALUES (?, ?, ?, "S");
                '''
                cur.execute(query, (self.language_name_id_dict[lang], card_id, storyline))

            #
            # INSERT into TABLE_TEXT_CARD_LANG Lyrics
            #
            for lang, lyrics in lyrics.items():
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + '''
                    (id_language, id_card, text, type)
                    VALUES (?, ?, ?, "L");
                '''
                cur.execute(query, (self.language_name_id_dict[lang], card_id, lyrics))    

            #
            # INSERT into TABLE_CARD_MEDIA
            #

            #logging.error("media: '{0}' ".format(media))


            for media_type in media:
                media_list = media[media_type]
                for medium in media_list:
                    if media_type in self.mediatype_name_id_dict:
                        mediatype_id = self.mediatype_name_id_dict[media_type]

                        query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_MEDIA + '''
                            (name, id_card, id_mediatype)
                            VALUES (:medium, :card_id, :mediatype_id);
                        '''
                        cur.execute(query, (medium, card_id, mediatype_id))   

        except sqlite3.Error as e:
            logging.error("To append media failed with: '{0}' while inserting record, configured in {1} card".format(e, card_path))
            cur.execute("rollback")

        # close the insert transaction
        cur.execute("commit")

        return card_id


    def append_hierarchy(self, card_path, title_orig, titles, title_on_thumbnail=1, title_show_sequence='', show=1, download=0, card_id=None, isappendix=0, date=None, decade=None, category=None, storylines={}, level=None, genres=None, themes=None, origins=None, basename=None, source_path=None, sequence=None, higher_card_id=None):

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            category_id = self.category_name_id_dict[category]
            title_orig_id = self.language_name_id_dict[title_orig]

            #
            # INSERT into Level
            #

            # if higher_card_id:
            if card_id:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                    (id, level, show, download, isappendix, id_title_orig, title_on_thumbnail, title_show_sequence, date, decade, id_category, basename, source_path, id_higher_card, sequence)
                    VALUES (:id, :level, :show, :download, :isappendix, :id_title_orig, :title_on_thumbnail, :title_show_sequence, :date, :decade, :id_category, :basename, :source_path, :id_higher_card, :sequence)
                    RETURNING id;
                '''
            else:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                    (level, show, download, isappendix, id_title_orig, title_on_thumbnail, title_show_sequence, date, decade, id_category, basename, source_path, id_higher_card, sequence)
                    VALUES (:level, :show, :download, :isappendix, :id_title_orig, :title_on_thumbnail, :title_show_sequence, :date, :decade, :id_category, :basename, :source_path, :id_higher_card, :sequence)
                    RETURNING id;
                '''
            cur.execute(query, {'id': card_id, 'level': level, 'show': show, 'download': download, 'isappendix': isappendix, 'id_title_orig': title_orig_id, 'title_on_thumbnail': title_on_thumbnail, 'title_show_sequence': title_show_sequence, 'date': date, 'decade': decade, 'id_category': category_id, 'basename': basename, 'source_path': source_path, 'id_higher_card': higher_card_id, 'sequence': sequence})
            record = cur.fetchone()
            (hierarchy_id, ) = record if record else (None,)

            #
            # INSERT into TABLE_TEXT_CARD_LANG Title
            #
            for lang, title in titles.items():
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + '''
                    (id_language, id_card, text, type)
                    VALUES (?, ?, ?, "T");
                '''
                cur.execute(query, (self.language_name_id_dict[lang], hierarchy_id, title))    

            #
            # INSERT into TABLE_CARD_GENRE
            #
            for sub in genres:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_GENRE + '''
                    (id_genre, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.genre_name_id_dict[sub], hierarchy_id))

            #
            # INSERT into TABLE_CARD_THEME
            #
            for theme in themes:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_THEME + '''
                    (id_theme, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.theme_name_id_dict[theme], hierarchy_id))

            #
            # INSERT into TABLE_CARD_ORIGIN
            #
            for origin in origins:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_ORIGIN + '''
                    (id_origin, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.country_name_id_dict[origin], hierarchy_id))    

            #
            # INSERT into TABLE_TEXT_CARD_LANG Storyline
            #
            for lang, storyline in storylines.items():
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + '''
                    (id_language, id_card, text, type)
                    VALUES (?, ?, ?, "S");
                '''
                cur.execute(query, (self.language_name_id_dict[lang], hierarchy_id, storyline))

        except sqlite3.Error as e:
            logging.error("To append hierarchy failed with: '{0}' while inserting record. Level: {1}, configured in {2} card".format(e, level, card_path))

            cur.execute("rollback")

        cur.execute("commit")

        #logging.error("TEST returns {0} with id: {1}".format(titles, hierarchy_id))
        return hierarchy_id







    # ================
    #
    # === requests ===
    #
    # ================

    def update_play_position(self, user_id, card_id, last_position, start_epoch=None):
        """
        Updates the player's position of a movie. This method is periodically called from the browser
        It returns with the start_epoch value if the UPDATE or INSERT was successful
        If something went wrong, it returns with None
        user_id:        User ID
        card_id         Card ID
        last_position   Player's recent position. Like: 1:18:28
        start_epoch     Timestamp when the play started. This method generates this value
        """
        try:
            with self.lock:

                cur = self.conn.cursor()
                cur.execute("begin")

                # Verify user existence
                query = '''
                    SELECT 
                        COUNT(*) as user_number
                FROM 
                    ''' + SqlDatabase.TABLE_USER + ''' user

                WHERE
                    user.id=:user_id;
                '''
                query_parameters = {'user_id': user_id}
                record=cur.execute(query, query_parameters).fetchone()
                (user_number, ) = record if record else (0,)
                if user_number == 0:
                    logging.error("The requested user_id({0}) does NOT exist".format(user_id))
                    return None

                # Verify card existence
                query = '''
                    SELECT 
                        COUNT(*) as card_number
                    FROM 
                        ''' + SqlDatabase.TABLE_CARD + ''' card
                    WHERE
                        card.id=:card_id
                '''
                query_parameters = {'card_id': card_id}
                record=cur.execute(query, query_parameters).fetchone()
                (card_number, ) = record if record else (0,)
                if card_number == 0:
                    logging.error("The requested card_id({0}) does NOT exist".format(card_id))
                    return None

                # Verify history existence
                query = '''
                    SELECT 
                        COUNT(*) as history_number
                    FROM 
                        ''' + SqlDatabase.TABLE_HISTORY + ''' history
                    WHERE
                        history.id_card=:card_id
                        AND history.id_user=:user_id
                        AND history.start_epoch=:start_epoch
                '''

                query_parameters = {'card_id': card_id, 'user_id': user_id, 'start_epoch': start_epoch if start_epoch else 0}

#                logging.debug("refresh_play_position query: '{0} / {1}'".format(query, query_parameters))

                record=cur.execute(query, query_parameters).fetchone()
                (history_number, ) = record if record else (0,)

#                logging.debug("history number of user({0}), card_id({1}), start_epoch({2}): {3} ".format(user_id, card_id, start_epoch, history_number))

                # New history
                if history_number == 0 and not start_epoch:

                    start_epoch = int(datetime.now().timestamp())
                    last_epoch = start_epoch
                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_HISTORY + '''
                        (id_card, id_user, start_epoch, last_epoch, last_position)
                        VALUES (:card_id, :user_id, :start_epoch, :last_epoch, :last_position);
                    '''
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'start_epoch': start_epoch, 'last_epoch': last_epoch, 'last_position': last_position})
                    record = cur.fetchone()                

                # Update history
                elif history_number == 1 and start_epoch:

                    last_epoch = int(datetime.now().timestamp())
                    query = '''
                        UPDATE ''' + SqlDatabase.TABLE_HISTORY + '''
                        SET last_epoch = :last_epoch, last_position = :last_position
                        WHERE
                            history.id_card=:card_id
                            AND history.id_user=:user_id
                            AND history.start_epoch=:start_epoch
                    '''                
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'start_epoch': start_epoch, 'last_epoch': last_epoch, 'last_position': last_position})
                    record = cur.fetchone()                

                # Something went wrong
                else:
                    logging.debug("Something went wrong. The parameter 'start_epoch'={0} but the SELECT in History table returned with value={1}".format(start_epoch, history_number))
                    return None

                return int(start_epoch)

        finally:
            cur.execute("commit")


    def get_user(self, user_name):
        try:
            with self.lock:

                cur = self.conn.cursor()
                cur.execute("begin")

                # Verify user existence
                query = '''
                    SELECT 
                        user.id as id,
                        user.name as name,
                        lang.name as language_code,
                        lang.id as language_id,
                        user.show_original_title   as show_original_title,
                        user.show_lyrics_anyway    as show_lyrics_anyway,
                        user.show_storyline_anyway as show_storyline_anyway,
                        user.play_continuously     as play_continuously 
                FROM 
                    ''' + SqlDatabase.TABLE_USER + ''' user,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    user.name=:user_name
                    AND user.id_language=lang.id;
                '''
                query_parameters = {'user_name': user_name}
                record=cur.execute(query, query_parameters).fetchone()
                return dict(record) if record else record

        finally:
            cur.execute("commit")


    def update_user_data(self, user_id, language_code=None, show_original_title=None, show_lyrics_anyway=None, show_storyline_anyway=None, play_continuously=None):
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                #
                # Verify user existence
                #
                # User
                query = '''
                    SELECT 
                        COUNT(*) as user_number
                FROM 
                    ''' + SqlDatabase.TABLE_USER + ''' user

                WHERE
                    user.id=:user_id;
                '''
                query_parameters = {'user_id': user_id}
                record=cur.execute(query, query_parameters).fetchone()
                (user_number, ) = record if record else (0,)
                if user_number == 0:
                    logging.error("The requested user_id({0}) does NOT exist".format(user_id))
                    return None

                # Language
                language_id = None
                if language_code:
                    query = '''
                        SELECT 
                            id
                    FROM 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang

                    WHERE
                        lang.name = :language_code;
                    '''
                    query_parameters = {'language_code': language_code}
                    record=cur.execute(query, query_parameters).fetchone()
                    (language_id, ) = record if record else (None,)
                    if language_id is None:
                        logging.error("The requested language_code({0}) does NOT exist".format(language_code))
                        return None

                #
                # Update
                #
                set_list = []
                if language_code:
                    set_list.append("'id_language' = :language_id")

                if show_original_title is not None:
                    set_list.append("'show_original_title' = :show_original_title")

                if show_lyrics_anyway is not None:
                    set_list.append("'show_lyrics_anyway' = :show_lyrics_anyway")

                if show_storyline_anyway is not None:
                    set_list.append("'show_storyline_anyway' = :show_storyline_anyway")

                query = '''
                        UPDATE ''' + SqlDatabase.TABLE_USER + '''
                        SET 
                            ''' + ", ".join(set_list) + '''
                        WHERE
                            user.id=:user_id
                    '''

                cur.execute(query, {'user_id': user_id, 'language_id': language_id, 'show_original_title': show_original_title, 'show_lyrics_anyway': show_lyrics_anyway, 'show_storyline_anyway': show_storyline_anyway, 'play_continuously': play_continuously})
                record = cur.fetchone()

                #
                # Get recent values
                #
                # Ugly: code repeating
                # TODO: fix it
                #
                query = '''
                    SELECT 
                        user.id as id,
                        user.name as name,
                        lang.name as language_code,
                        lang.id as language_id,
                        user.show_original_title   as show_original_title,
                        user.show_lyrics_anyway    as show_lyrics_anyway,
                        user.show_storyline_anyway as show_storyline_anyway,
                        user.play_continuously     as play_continuously 
                FROM 
                    ''' + SqlDatabase.TABLE_USER + ''' user,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    user.id=:user_id
                    AND user.id_language=lang.id;
                '''
                query_parameters = {'user_id': user_id}
                record=cur.execute(query, query_parameters).fetchone()
                return dict(record) if record else record

            finally:
                cur.execute("commit")
    

    def get_history(self, user_id, card_id=None, limit_days=None, limit_records=None):                  
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                limit_epoch = None
                if limit_days:
                    limit_epoch=int((datetime.now() + timedelta(days=limit_days)).timestamp())

                # Verify user existence
                query = '''
                    SELECT 
                        *
                    FROM 
                        ''' + SqlDatabase.TABLE_HISTORY + ''' history
                    WHERE
                        id_user=:user_id
                        ''' + ('''
                        AND id_card=:card_id
                        ''' if card_id else '') + ('''
                        AND start_epoch <= :limit_epoch
                        ''' if limit_days else '') + '''
                    ORDER BY start_epoch DESC''' + ('''
                    LIMIT :limit_records
                        ''' if limit_records else '') + '''
                ;'''
                query_parameters = {'user_id': user_id, 'card_id': card_id, 'limit_epoch': limit_epoch, 'limit_records': limit_records}
                print("{0}/{1}".format(query,query_parameters))
                records=cur.execute(query, query_parameters).fetchall()

                records = [{key: record[key] for key in record.keys()} for record in records]
                return records

            finally:
                cur.execute("commit")





    def get_numbers_of_records_in_card(self):
        """
        Gives back the number of records in the Card table
        """
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("begin")

            # Get Card list
            query = "SELECT COUNT(*) FROM " + SqlDatabase.TABLE_CARD + ";" 
            record=cur.execute(query).fetchone()
            cur.execute("commit")
            return record


    #
    # --- Movie series queries ---
    #

    def get_all_series_of_movies(self, lang, limit=100, json=True):
        return self.get_general_level(level='series', category='movie', lang=lang, limit=limit, json=json)

    def get_all_series_comedies_of_movies(self, lang, limit=100, json=True):
        return self.get_all_level(level='series', category='movie', genre='comedy', lang=lang, limit=limit, json=json)

    #
    # --- Video Music queries ---
    #

    def get_all_new_wave_bands_of_music_video(self, lang, limit=100, json=True):
        return self.get_general_level(level='band', category='music_video', genre='new_wave', lang=lang, limit=limit, json=json)

    def get_all_bands_of_music_video_from_decade(self, decade, lang, limit=100, json=True):
        return self.get_general_level(level='band', category='music_video', decade=decade, lang=lang, limit=limit, json=json)

    #
    # reviewed
    #
    # General - for any kind of Card on a certain level
    #
    #
    def get_general_level(self, level, category, genre=None, theme=None, origin=None, decade=None, lang='en', limit=100, json=True):
        """
        It returns a list of the given level cards in the given category, optionally filtered by genre/theme/origin/decade
        """
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            # Get Card list
            query = '''
                SELECT 
                    merged.id, 
                    merged.level level,
                    MAX(title_req) title_req, 
                    MAX(lang_req) lang_req, 
                    MAX(title_orig) title_orig, 
                    MAX(lang_orig) lang_orig,

                    title_on_thumbnail,
                    title_show_sequence,

                    source_path
                FROM (
                    SELECT 
                        card.id id,
                        card.level level,
                        card.id_category id_category,
                        card.decade decade,
                        NULL title_req, 
                        NULL lang_req, 
                        htl.text title_orig, 
                        lang.name lang_orig,

                        title_on_thumbnail,
                        title_show_sequence,                        

                        card.source_path source_path,
                        card.sequence sequence,
                        card.basename
                    FROM
                        ''' + SqlDatabase.TABLE_CARD + ''' card,
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' htl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
                    WHERE
                        card.level=:level
                        AND htl.id_card=card.id
                        AND htl.id_language=lang.id
                        AND card.id_title_orig=lang.id
                        AND lang.name <> :lang
                        AND card.isappendix = 0
    
                    UNION
    
                    SELECT 
                        card.id id,
                        card.level level,
                        card.id_category id_category,
                        card.decade decade,
                        htl.text title_req, 
                        lang.name lang_req, 
                        NULL title_orig, 
                        NULL lang_orig,

                        title_on_thumbnail,
                        title_show_sequence,

                        card.source_path source_path,
                        card.sequence sequence,
                        card.basename
                    FROM
                        ''' + SqlDatabase.TABLE_CARD + ''' card,
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' htl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
                    WHERE
                        card.level=:level
                        AND htl.id_card=card.id
                        AND htl.id_language=lang.id
                        AND lang.name = :lang
                        AND card.isappendix = 0
                    ) merged,
            ''' + ('''
                    --- origin ---
                    ''' + SqlDatabase.TABLE_COUNTRY + ''' country,
                    ''' + SqlDatabase.TABLE_CARD_ORIGIN + ''' co,                    
            ''' if origin else '') + ('''

                    --- genre ---
                    ''' + SqlDatabase.TABLE_GENRE + ''' genre,
                    ''' + SqlDatabase.TABLE_CARD_GENRE + ''' cg,                    
            ''' if genre else '') + ('''

                    --- theme ---
                    ''' + SqlDatabase.TABLE_THEME + ''' theme,
                    ''' + SqlDatabase.TABLE_CARD_THEME + ''' ct,                    
            ''' if theme else '') + '''

                    ''' + SqlDatabase.TABLE_CATEGORY + ''' cat
    
                WHERE
                    merged.id_category=cat.id
                    AND cat.name=:category
            ''' + ('''

                    --- genre ---
                    AND cg.id_genre = genre.id
                    AND cg.id_card = merged.id 
                    AND genre.name =:genre    
            ''' if genre else '') + ('''

                    --- theme ---
                    AND ct.id_theme = theme.id
                    AND ct.id_card = merged.id 
                    AND theme.name = :theme
            ''' if theme else '') + ('''

                    --- origin ---
                    AND co.id_card = merged.id
                    AND co.id_origin = country.id
            ''' if origin else '') + ('''

                    AND country.name = :origin
            ''' if origin else '') + ('''

                    --- decade ---
                    AND merged.decade = :decade
            ''' if decade else '') +  '''

                GROUP BY merged.id
                ORDER BY CASE 
                    WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
                    WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
                    WHEN sequence<0 THEN basename
                    WHEN sequence>=0 THEN sequence
                END
                LIMIT :limit;
            '''

            query_parameters = {'level': level, 'decade': decade, 'category': category, 'genre': genre, 'theme': theme, 'origin': origin, 'lang': lang, 'limit':limit}

            logging.debug("get_general_level query: '{0} / {1}'".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

                #
                # Translate
                #

                trans = Translator.getInstance(lang)

                for record in records:

                    # Lang Orig
                    lang_orig = record["lang_orig"]
                    lang_orig_translated = trans.translate_language_short(lang_orig)
                    record["lang_orig"] = lang_orig_translated

                    # Lang Req
                    lang_req = record["lang_req"]
                    lang_req_translated = trans.translate_language_short(lang_req)
                    record["lang_req"] = lang_req_translated

            return records


    #
    # reviewed
    #
    # General - for any kind of hierarchy if it has parent id
    #
    #
    def get_child_hierarchy_or_card(self, higher_card_id, lang, json=True):
        """
        Gives back child Hiearchy of the given hierarchy id. If the child hierarchy is Card
        then it gives back the child Cards
        """
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            # Get Card list
            query = '''
            SELECT id, level, title_req, title_orig, lang_req, lang_orig, title_on_thumbnail, title_show_sequence, sequence, source_path, date, appendix, medium
            FROM (

                --- all cards connected to higher card ---
                SELECT merged.id, merged.level level, MAX(merged.title_req) title_req, MAX(merged.title_orig) title_orig, MAX(merged.lang_orig) lang_orig, MAX(merged.lang_req) lang_req, merged.title_on_thumbnail, merged.title_show_sequence, merged.sequence, merged.basename, merged.source_path, merged.date, group_concat(appendix_card.id) appendix, group_concat( mt.name || "=" || cm.name) medium
                FROM (

                    --- requested language not the original ---
                    SELECT 
                        card.id id, 
                        card.level level, 
                        NULL title_req,
                        NULL lang_req,
                        lang.name lang_orig,
                        tcl.text title_orig,
                        
                        title_on_thumbnail,
                        title_show_sequence,

                        sequence,
                        basename, 
                        source_path,
                        date
                    FROM
                        ''' + SqlDatabase.TABLE_CARD + ''' card, 
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang

                    WHERE
                        card.id_higher_card=:higher_card_id
                        AND tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"
                        AND card.id_title_orig=lang.id
                        AND lang.name <> :lang
                        AND card.isappendix = 0
                    UNION    
                        
                    --- requested language is any existing language ---
                    SELECT 
                        card.id id, 
                        card.level level, 
                        tcl.text title_req,
                        lang.name lang_req, 
                        NULL title_orig,
                        NULL lang_orig,

                        title_on_thumbnail,
                        title_show_sequence,

                        sequence, 
                        basename, 
                        source_path,
                        date
                    FROM 
                        ''' + SqlDatabase.TABLE_CARD + ''' card, 
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                    WHERE
                        card.id_higher_card=:higher_card_id
                        AND tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"                 
                        AND lang.name = :lang
                        AND card.isappendix = 0
                ) merged

                LEFT JOIN Card appendix_card 
                    ON appendix_card.id_higher_card = merged.id
                    AND appendix_card.isappendix = 1

                LEFT JOIN Card_Media cm 
                    ON cm.id_card=merged.id
                    LEFT JOIN MediaType mt
                    ON cm.id_mediatype = mt.id               
                        
                GROUP BY merged.id
            )

            ORDER BY CASE 
                WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
                WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
                WHEN sequence<0 THEN basename
                WHEN sequence>=0 THEN sequence
            END
            '''

            query_parameters = {'higher_card_id': higher_card_id, 'lang':lang}

            logging.debug("child_hierarchy_or_card query: '{0}'".format(query))
            logging.debug("get_general_level query: '{0} / {1}'".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

                #
                # Translate
                #

                trans = Translator.getInstance(lang)

                index = 0
                for record in records:

                    logging.debug("  {0}. record: '{1}'".format(index, record))
                    index += 1

                    # Lang Orig
                    lang_orig = record["lang_orig"]
                    lang_orig_translated = trans.translate_language_short(lang_orig)
                    record["lang_orig"] = lang_orig_translated

                    # Lang Req
                    lang_req = record["lang_req"]
                    lang_req_translated = trans.translate_language_short(lang_req)
                    record["lang_req"] = lang_req_translated


                    # Media
                    medium_string = record["medium"]
                    media_dict = {}
                    if medium_string:
                        medium_string_list = medium_string.split(',')
                        for medium_string in medium_string_list:
                            (media_type, media) = medium_string.split("=")
                            if not media_type in media_dict:
                                media_dict[media_type] = []
                            media_dict[media_type].append(media)
                    record["medium"] = media_dict

            return records


    #
    # --- Movie queries ---
    #
    def get_standalone_movies_by_genre(self, genre, lang, limit=100, json=True):
        return self.get_general_standalone(category='movie', genre=genre, lang=lang, limit=limit, json=json)
































    # reviewed
    #
    #
    # Only for standalone media search with 
    # logical operands (_AND_, _NOT_) in
    #   - genre
    #   - theme
    #
    #
    def get_general_standalone(self, category, genres=None, themes=None, directors=None, actors=None, origins=None, decade=None, lang='en', limit=100, json=True):
             
        with self.lock:
            where = ''

            # Generate and Convert GENRE conditions
            genre_list =             [] if genres == None else genres.split('_AND_')
            genre_in_list =          [] if genres == None else [genre for genre in genre_list if not genre.startswith("_NOT_")]
            genre_not_in_list =      [] if genres == None else [genre.removeprefix("_NOT_") for genre in genre_list if genre.startswith("_NOT_")]
            genres_where =           '' if genres == None else 'AND ' + ' AND '.join(["',' || genres || ',' " + ("NOT " if genre.startswith("_NOT_") else "") + "LIKE '%," + genre.removeprefix("_NOT_") + ",%'" for genre in genre_list])
            logging.error("GENRE IN LIST: {}".format(genre_in_list))
            logging.error("GENRE NOT IN LIST: {}".format(genre_not_in_list))
            logging.error("GENRE WHERE: {}".format(genres_where))

            # Generate and Convert THEME conditions
            theme_list =             [] if themes == None else themes.split('_AND_')
            theme_in_list =          [] if themes == None else [theme for theme in theme_list if not theme.startswith("_NOT_")]
            theme_not_in_list =      [] if themes == None else [theme.removeprefix("_NOT_") for theme in theme_list if theme.startswith("_NOT_")]
            themes_where =           '' if themes == None else 'AND ' + ' AND '.join(["',' || themes || ',' " + ("NOT " if theme.startswith("_NOT_") else "") + "LIKE '%," + theme.removeprefix("_NOT_") + ",%'" for theme in theme_list])
            logging.error("THEME IN LIST: {}".format(theme_in_list))
            logging.error("THEME NOT IN LIST: {}".format(theme_not_in_list))
            logging.error("THEME WHERE: {}".format(themes_where))

            # Generate and Convert ORIGIN conditions
            origin_list =            [] if origins == None else origins.split('_AND_')
            origin_in_list =         [] if origins == None else [origin for origin in origin_list if not origin.startswith("_NOT_")]
            origin_not_in_list =     [] if origins == None else [origin.removeprefix("_NOT_") for origin in origin_list if origin.startswith("_NOT_")]
            origins_where =          '' if origins == None else 'AND ' + ' AND '.join(["',' || origins || ',' " + ("NOT " if origin.startswith("_NOT_") else "") + "LIKE '%," + origin.removeprefix("_NOT_") + ",%'" for origin in origin_list])
            logging.error("ORIGIN IN LIST: {}".format(theme_in_list))
            logging.error("ORIGIN NOT IN LIST: {}".format(origin_not_in_list))
            logging.error("ORIGIN WHERE: {}".format(origins_where))

            # Generate and Convert ACTORS conditions
            actor_list =            [] if actors == None else actors.split('_AND_')
            actor_in_list =         [] if actors == None else [actor for actor in actor_list if not actor.startswith("_NOT_")]
            actor_not_in_list =     [] if actors == None else [actor.removeprefix("_NOT_") for actor in actor_list if actor.startswith("_NOT_")]
            actors_where =          '' if actors == None else 'AND ' + ' AND '.join(["',' || actors || ',' " + ("NOT " if actor.startswith("_NOT_") else "") + "LIKE '%," + actor.removeprefix("_NOT_") + ",%'" for actor in actor_list])
            logging.error("ACTOR IN LIST: {}".format(actor_in_list))
            logging.error("ACTOR NOT IN LIST: {}".format(actor_not_in_list))
            logging.error("ACTOR WHERE: {}".format(actors_where))

            # Generate and Convert DIRECTOR conditions
            director_list =         [] if directors == None else directors.split('_AND_')
            director_in_list =      [] if directors == None else [director for director in director_list if not director.startswith("_NOT_")]
            director_not_in_list =  [] if directors == None else [director.removeprefix("_NOT_") for director in director_list if director.startswith("_NOT_")]
            directors_where =       '' if directors == None else 'AND' + ' AND '.join(["',' || directors || ',' " + ("NOT " if director.startswith("_NOT_") else "") + "LIKE '%," + director.removeprefix("_NOT_") + ",%'" for director in director_list])
            logging.error("DIRECTOR IN LIST: {}".format(director_in_list))
            logging.error("DIRECTOR NOT IN LIST: {}".format(director_not_in_list))
            logging.error("DIRECTOR WHERE: {}".format(directors_where))

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}


#''' + SqlDatabase.TABLE_CARD + ''' card,
#''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
#''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
#''' + SqlDatabase.TABLE_CARD + ''' card,
#''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
#''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
#''' + SqlDatabase.TABLE_COUNTRY + ''' country,
#''' + SqlDatabase.TABLE_CARD_ORIGIN + ''' co,
#''' + SqlDatabase.TABLE_PERSON + ''' actor,
#''' + SqlDatabase.TABLE_CARD_ACTOR + ''' ca,
#''' + SqlDatabase.TABLE_PERSON + ''' director,
#''' + SqlDatabase.TABLE_CARD_DIRECTOR + ''' cd,
#'' + SqlDatabase.TABLE_CATEGORY + ''' cat ''' + ('''


            query = '''
SELECT
    core.*,

    storyline,
    lyrics,

    sounds,
    subs,
    directors,
    writers,
    voices,
    stars,
    actors,
    genres,
    themes,
    origins,
    appendix,
    medium
FROM
(
    SELECT 
        unioned.id id,
        unioned.level level,
        MAX(title_req) title_req, 
        MAX(title_orig) title_orig, 
        MAX(lang_orig) lang_orig,
        MAX(lang_req) lang_req,
        unioned.title_on_thumbnail,
        unioned.title_show_sequence,
        unioned.decade,
        unioned.date,
        unioned.length,

        unioned.source_path,
        unioned.id_category
    FROM 
    (
        SELECT 
            card.id id, 
            card.level level,
            card.id_category id_category,
            NULL title_req, 
            NULL lang_req, 
            tcl.text title_orig, 
            lang.name lang_orig,
            title_on_thumbnail,
            title_show_sequence,
            card.decade decade,
            card.date date,
            card.length length,

            card.source_path source_path
        FROM                     
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE                
            card.id_higher_card IS NULL
            AND tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
            AND card.id_title_orig=lang.id
            AND card.level IS NULL
            AND card.isappendix = 0
            AND lang.name <> :lang

        UNION

        SELECT 
            card.id id,
            card.level level,
            card.id_category id_category,
            tcl.text title_req, 
            lang.name lang_req, 
            NULL title_orig, 
            NULL lang_orig,
            title_on_thumbnail,
            title_show_sequence,
            card.decade decade,
            card.date date,
            card.length length,

            card.source_path source_path
        FROM               
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE               
            card.id_higher_card IS NULL
            AND tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
            AND card.level IS NULL
            AND card.isappendix = 0
            AND lang.name=:lang
    ) unioned

    GROUP BY unioned.id               
) core,
''' + SqlDatabase.TABLE_CATEGORY + ''' cat


--- STORYLINE ---
LEFT JOIN
    (
        SELECT ord, storyline, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL

            UNION

            --- Select the storyline on the original language ---

            SELECT "2" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
--        HAVING MIN(ord)
--        ORDER BY ord
    )strl
    ON strl.id_card=core.id

--- LYRICS ---
LEFT JOIN
    (
        SELECT ord, lyrics, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the storyline on the original language ---

            SELECT "2" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
--        HAVING MIN(ord)
--        ORDER BY ord
    )lrx
    ON lrx.id_card=core.id 

--- MEDIUM ---
LEFT JOIN
    (SELECT group_concat( media_type.name || "=" || card_media.name) medium, card_media.id_card
    FROM
        MediaType media_type,
        Card_Media card_media
    WHERE
        card_media.id_mediatype=media_type.id
    GROUP BY card_media.id_card
    )mdt
    ON mdt.id_card=core.id

--- APPENDIX ---
LEFT JOIN    
    (    
    SELECT
        card_id,
        group_concat("id=" || id || ";mt=" || media_type || ";cm=" || contact_media || ";sw=" || show || ";dl=" || download || ";rt=" || title_req || ";ot=" || title_orig || ";sp=" || source_path) appendix
    FROM
    
        (
        SELECT                
            merged_appendix.id,
            merged_appendix.card_id,
            MAX(merged_appendix.title_req) title_req, 
            MAX(merged_appendix.title_orig) title_orig,
            merged_appendix.show,
            merged_appendix.download,
            merged_appendix.source_path,
            mt.name media_type,
            cm.name contact_media                
        FROM
            (
            SELECT 
                app_card.id id,
                id_higher_card card_id,
                app_card.isappendix,
                app_card.show,
                app_card.download,
                app_card.source_path,
                "" title_req, 
                tcl.text title_orig
            FROM 
                CARD app_card,
                TEXT_CARD_LANG tcl, 
                LANGUAGE lang                    
            WHERE                
                app_card.isappendix=1
                AND tcl.id_card=app_card.id
                AND tcl.id_language=lang.id
                AND tcl.type="T"
                AND app_card.id_title_orig=lang.id
                AND lang.name <> :lang
            UNION
            SELECT 
                app_card.id id,
                id_higher_card card_id,
                app_card.isappendix,
                app_card.show,
                app_card.download,
                app_card.source_path,
                tcl.text title_req, 
                "" title_orig
            FROM 
                CARD app_card,
                TEXT_CARD_LANG tcl, 
                LANGUAGE lang                    
            WHERE
                app_card.isappendix=1
                AND tcl.id_card=app_card.id
                AND tcl.id_language=lang.id
                AND tcl.type="T"
                AND lang.name=:lang
            ) merged_appendix,
            Card_Media cm,
            MediaType mt
            
        WHERE
            cm.id_card=merged_appendix.id
            AND mt.id=cm.id_mediatype
            
        GROUP BY merged_appendix.id
        )
    GROUP BY card_id
) pndx
ON pndx.card_id=core.id 

-- LEFT JOIN
--     (SELECT group_concat(appendix_card.id) appendix, appendix_card.id_higher_card
--     FROM
--         Card appendix_card        
--     WHERE
--         appendix_card.isappendix=1
--     GROUP BY appendix_card.id_higher_card
--     )pndx
--     ON pndx.id_higher_card=core.id

--- ORIGIN ---
LEFT JOIN
    (SELECT group_concat(origin.name) origins, card_origin.id_card
    FROM
        Country origin,
        Card_Origin card_origin
    WHERE
        card_origin.id_origin=origin.id
    GROUP BY card_origin.id_card
    )rgn
    ON rgn.id_card=core.id

--- THEME ---
LEFT JOIN 
    (SELECT group_concat(theme.name) themes, card_theme.id_card
        FROM
            Theme theme,
            Card_Theme card_theme
        WHERE            
            card_theme.id_theme=theme.id
        GROUP BY card_theme.id_card
    )thm
    ON thm.id_card=core.id

--- GENRE ---
LEFT JOIN 
    (SELECT group_concat(genre.name) genres, card_genre.id_card
        FROM
            Genre genre,
            Card_Genre card_genre
        WHERE            
            card_genre.id_genre=genre.id
        GROUP BY card_genre.id_card
    )gnr
    ON gnr.id_card=core.id

--- LANGUAGE ---   
LEFT JOIN 
    (SELECT group_concat(language.name) sounds, card_sound.id_card
        FROM 
            Language language,
            Card_Sound card_sound
        WHERE 
            card_sound.id_sound=language.id 
        GROUP BY card_sound.id_card
    ) snd
    ON snd.id_card=core.id

--- SUB ---
LEFT JOIN
    (SELECT group_concat(language.name) subs, card_sub.id_card
        FROM 
            Language language,
            Card_Sub card_sub
        WHERE 
            card_sub.id_sub=language.id
        GROUP BY card_sub.id_card
    ) sb
    ON sb.id_card=core.id

--- DIRECTORS ---
LEFT JOIN    
    (SELECT group_concat(person.name) directors,  card_dir.id_card
        FROM 
            Person person,
            Card_Director card_dir
        WHERE 
            card_dir.id_director = person.id
        GROUP BY card_dir.id_card
    ) dr
    ON dr.id_card=core.id

--- WRITERS ---
LEFT JOIN    
    (SELECT group_concat(person.name) writers,  card_writer.id_card
        FROM 
            Person person,
            Card_Writer card_writer
        WHERE 
            card_writer.id_writer = person.id
        GROUP BY card_writer.id_card
    ) wr
    ON wr.id_card=core.id

--- VOICES ---
LEFT JOIN    
    (SELECT group_concat(person.name) voices,  card_voice.id_card
        FROM 
            Person person,
            Card_Voice card_voice
        WHERE 
            card_voice.id_voice = person.id
        GROUP BY card_voice.id_card
    ) vc
    ON vc.id_card=core.id    

--- STARS ---
LEFT JOIN    
    (SELECT group_concat(person.name) stars,  card_star.id_card
        FROM 
            Person person,
            Card_Star card_star
        WHERE 
            card_star.id_star = person.id
        GROUP BY card_star.id_card
    ) str
    ON str.id_card=core.id
    
--- ACTORS ---
LEFT JOIN    
    (SELECT group_concat(person.name) actors,  card_actor.id_card
        FROM 
            Person person,
            Card_Actor card_actor
        WHERE 
            card_actor.id_actor = person.id
        GROUP BY card_actor.id_card
    ) act
    ON act.id_card=core.id

WHERE           

    --- category --- 
    core.id_category=cat.id
    AND cat.name=:category

    ''' + ('''
    --- WHERE decade - conditional ---
    AND core.decade=:decade ''' if decade else '') + ('''
                        
    --- WHERE ORIGIN - conditional ---
    ''' + origins_where if origins else '') + ('''

    --- WHERE THEMES - conditional ---
    ''' + themes_where if themes else '') + ('''

    --- WHERE GENRES - conditional ---
    ''' + genres_where if genres else '') + ('''

    --- WHERE ACTORS - conditional ---
    ''' + actors_where if actors else '') + ('''

    --- WHERE DIRECTORS - conditional ---
    ''' + directors_where if directors else '') + '''

ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END

LIMIT :limit; '''

            query_parameters = {'category': category, 'decade': decade, 'lang': lang, 'limit': limit}            

            logging.debug("get_general_standalone query: '{0}' / {1}".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

                #
                # Translate and Convert
                #

                trans = Translator.getInstance(lang)

                for record in records:

                    # Lang Orig
                    lang_orig = record["lang_orig"]
                    lang_orig_translated = trans.translate_language_short(lang_orig)
                    record["lang_orig"] = lang_orig_translated

                    # Lang Req
                    lang_req = record["lang_req"]
                    lang_req_translated = trans.translate_language_short(lang_req)
                    record["lang_req"] = lang_req_translated

                    # Media
                    medium_string = record["medium"]
                    media_dict = {}
                    if medium_string:
                        medium_string_list = medium_string.split(',')
                        for medium_string in medium_string_list:
                            (media_type, media) = medium_string.split("=")
                            if not media_type in media_dict:
                                media_dict[media_type] = []
                            media_dict[media_type].append(media)
                    record["medium"] = media_dict

                    # Appendix
                    appendix_string = record["appendix"]
                    appendix_list = []
                    if appendix_string:
                        text_list = appendix_string.split(',')
                        for appendix_string in text_list:
                            var_list = appendix_string.split(";")
                            appendix_dict = {}
                            for var_pair in var_list:
                                (key, value) = var_pair.split("=")
                                appendix_dict[key] = value
                            appendix_list.append(appendix_dict)
                    record["appendix"] = appendix_list

                    # Writers
                    writers_string = record["writers"]
                    writers_list = []
                    if writers_string:
                        writers_list = writers_string.split(',')
                    record["writers"] = writers_list
    
                    # Directors
                    directors_string = record["directors"]
                    directors_list = []
                    if directors_string:
                        directors_list = directors_string.split(',')
                    record["directors"] = directors_list
    
                    # Stars
                    stars_string = record["stars"]
                    stars_list = []
                    if stars_string:
                        stars_list = stars_string.split(',')
                    record["stars"] = stars_list
    
                    # Actors
                    actors_string = record["actors"]
                    actors_list = []
                    if actors_string:
                        actors_list = actors_string.split(',')
                    record["actors"] = actors_list
    
                    # Voices
                    voices_string = record["voices"]
                    voices_list = []
                    if voices_string:
                        voices_list = voices_string.split(',')
                    record["voices"] = voices_list
    
                    # Host
                    hosts_string = record.get("hosts")
                    hosts_list = []
                    if hosts_string:
                        hosts_list = hosts_string.split(',')
                    record["hosts"] = hosts_list
    
                    # Guests
                    guests_string = record.get("guests")
                    guests_list = []
                    if guests_string:
                        guests_list = guests_string.split(',')
                    record["guests"] = guests_list
    
                    # Interviewers
                    interviewers_string = record.get("interviewers")
                    interviewers_list = []
                    if interviewers_string:
                        interviewers_list = interviewers_string.split(',')
                    record["interviewers"] = interviewers_list
    
                    # Interviewees
                    interviewees_string = record.get("interviewees")
                    interviewees_list = []
                    if interviewees_string:
                        interviewees_list = interviewees_string.split(',')
                    record["interviewees"] = interviewees_list
    
                    # Presenters
                    presenters_string = record.get("presenters")
                    presenters_list = []
                    if presenters_string:
                        presenters_list = presenters_string.split(',')
                    record["presenters"] = presenters_list
    
                    # Lecturers
                    lecturers_string = record.get("lecturers")
                    lecturers_list = []
                    if lecturers_string:
                        lecturers_list = lecturers_string.split(',')
                    record["lecturers"] = lecturers_list
    
                    # Performers
                    performers_string = record.get("performers")
                    performers_list = []
                    if performers_string:
                        performers_list = performers_string.split(',')
                    record["performers"] = performers_list
    
                    # Reporters
                    reporters_string = record.get("reporters")
                    reporters_list = []
                    if reporters_string:
                        reporters_list = reporters_string.split(',')
                    record["reporters"] = reporters_list
    
                    # Genre
                    genres_string = record.get("genres")
                    genres_list = []
                    if genres_string:
                        genres_list = genres_string.split(',')
                        genres_list = [trans.translate_genre(category=category, genre=genre) for genre in genres_list]
                    record["genres"] = genres_list
    
                    # Theme
                    themes_string = record["themes"]
                    themes_list = []
                    if themes_string:
                        themes_list = themes_string.split(',')
                        themes_list = [trans.translate_theme(theme=theme) for theme in themes_list]
                    record["themes"] = themes_list
    
                    # Origin
                    origins_string = record["origins"]
                    origins_list = []
                    if origins_string:
                        origins_list = origins_string.split(',')
                        origins_list = [trans.translate_country_long(origin) for origin in origins_list]
                    record["origins"] = origins_list
    
                    # Sub
                    subs_string = record["subs"]
                    subs_list = []
                    if subs_string:
                        subs_list = subs_string.split(',')
                        subs_list = [trans.translate_language_long(sub) for sub in subs_list]
                    record["subs"] = subs_list
    
                    # Sounds
                    sounds_string = record["sounds"]
    
                    sounds_list = []
                    if sounds_string:
                        sounds_list = sounds_string.split(',')
                        sounds_list = [trans.translate_language_long(sounds) for sounds in sounds_list]
                    record["sounds"] = sounds_list
    
                logging.debug("Converted records: '{0}'".format(records))

            return records















    # 
    #
    #
    # Detailed Card for any movie with card id
    #
    #

    # TODO: DB name should be replaced by variables
    # TODO: Give back all existing/posible fields

    def get_media_by_card_id(self, card_id, lang, limit=100, json=True):
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            # Get Card list
            query = '''
            SELECT             
                card.id as id,
                category.name as category,
                card.date as date,
                card.length as length,
                card.source_path as source_path,
                card.download,
                medium,
                storyline,
                lyrics,
                sounds,
                subs,
                origins,
                genres,
                themes,
                directors,
                writers,
                voices,
                stars,
                actors,
                hosts,
                guests,
                interviewers,
                interviewees,
                presenters,
                reporters,
                lecturers,
                performers,
                appendix
            FROM
                (SELECT group_concat( mt.name || "=" || m.name) medium

                    FROM 
                        Card_Media m,
                        MediaType mt
                    WHERE
                        m.id_card= :card_id AND
                        m.id_mediatype = mt.id
                ),
            
                (SELECT group_concat(tcl.text) storyline
                    FROM 
                        Text_Card_Lang tcl,
                        Language language
                    WHERE 
                        tcl.type = "S" AND
                        tcl.id_card = :card_id AND
                        tcl.id_language = language.id AND
                        language.name = :lang
                ),

                (SELECT * FROM 
                    (SELECT tcl.text lyrics
                        FROM 
                            Text_Card_Lang tcl,
                            Language language
                        WHERE 
                            tcl.type = "L" AND
                            tcl.id_card = :card_id AND
                            tcl.id_language = language.id AND
                            language.name = :lang
                    UNION
                    SELECT group_concat(tcl.text) lyrics
                        FROM 
                            Text_Card_Lang tcl,
                            Language language,
                            Card card
                        WHERE 
                            tcl.type = "L" AND
                            tcl.id_card = :card_id AND
                            tcl.id_language = language.id AND
                            card.id = :card_id AND
                            card.id_title_orig = language.id AND
                        tcl.text IS NOT NULL
                    )                
                ),

                (SELECT group_concat(language.name) sounds
                    FROM 
                        Language language,
                        Card_Sound card_sound
                    WHERE 
                        card_sound.id_sound=language.id AND
                        card_sound.id_card = :card_id
                ),
                (SELECT group_concat(language.name) subs
                    FROM 
                        Language language,
                        Card_Sub card_sub
                    WHERE 
                        card_sub.id_sub=language.id AND
                        card_sub.id_card = :card_id
                ),
                
                (SELECT group_concat(country.name) origins
                    FROM 
                        Country country,
                        Card_Origin card_origin
                    WHERE 
                        card_origin.id_card = :card_id AND
                        country.id = card_origin.id_origin
                ),                        
                (SELECT group_concat(genre.name) genres
                    FROM 
                        Genre genre,
                        Card_Genre card_genre
                    WHERE 
                        card_genre.id_card = :card_id AND
                        genre.id = card_genre.id_genre
                ),
                   
                (SELECT group_concat(theme.name) themes
                    FROM 
                        Theme theme,
                        Card_Theme card_theme
                    WHERE 
                        card_theme.id_card = :card_id AND
                        theme.id = card_theme.id_theme
                ),
                (SELECT group_concat(person.name) directors
                    FROM 
                        Person person,
                        Card_Director cd
                    WHERE 
                        cd.id_director = person.id AND
                        cd.id_card = :card_id
                ),
                (SELECT group_concat(person.name) writers
                    FROM 
                        Person person,
                        Card_Writer cv                            
                    WHERE 
                        cv.id_writer = person.id AND
                        cv.id_card = :card_id
                ),
                (SELECT group_concat(person.name) voices
                    FROM 
                        Person person,
                        Card_Voice cv
                    WHERE 
                        cv.id_voice = person.id AND
                        cv.id_card = :card_id
                ),
                (SELECT group_concat(person.name) stars
                    FROM 
                        Person person,
                        Card_Star cs
                    WHERE 
                        cs.id_star = person.id AND
                        cs.id_card = :card_id
                ),
                (SELECT group_concat(person.name) actors
                    FROM 
                        Person person,
                        Card_Actor ca
                    WHERE 
                        ca.id_actor = person.id AND
                        ca.id_card = :card_id
                ),
                (SELECT group_concat(person.name) hosts
                    FROM 
                        Person person,
                        Card_Host ch
                    WHERE 
                        ch.id_host = person.id AND
                        ch.id_card = :card_id
                ),
                (SELECT group_concat(person.name) guests
                    FROM 
                        Person person,
                        Card_Guest cg
                    WHERE 
                        cg.id_guest = person.id AND
                        cg.id_card = :card_id
                ),
                (SELECT group_concat(person.name) interviewers
                    FROM 
                        Person person,
                        Card_Interviewer ci
                    WHERE 
                        ci.id_interviewer = person.id AND
                        ci.id_card = :card_id
                ),
                (SELECT group_concat(person.name) interviewees
                    FROM 
                        Person person,
                        Card_Interviewee ci
                    WHERE 
                        ci.id_interviewee = person.id AND
                        ci.id_card = :card_id
                ),
                (SELECT group_concat(person.name) presenters
                    FROM 
                        Person person,
                        Card_Presenter ci
                    WHERE 
                        ci.id_presenter = person.id AND
                        ci.id_card = :card_id
                ),
                (SELECT group_concat(person.name) lecturers
                    FROM 
                        Person person,
                        Card_Lecturer ci
                    WHERE 
                        ci.id_lecturer = person.id AND
                        ci.id_card = :card_id
                ),
                (SELECT group_concat(person.name) performers
                    FROM 
                        Person person,
                        Card_Performer cp
                    WHERE 
                        cp.id_performer = person.id AND
                        cp.id_card = :card_id
                ),
                (SELECT group_concat(person.name) reporters
                    FROM 
                        Person person,
                        Card_Reporter cr
                    WHERE 
                        cr.id_reporter = person.id AND
                        cr.id_card = :card_id
                ),

                (SELECT group_concat(appendix_card.id) appendix
                    FROM 
                        Card appendix_card
                    WHERE 
                        appendix_card.id_higher_card = :card_id
                        AND appendix_card.isappendix = 1
                ),

                Card card,
                Category category
            WHERE
                card.id = :card_id  AND
                card.id_category = category.id

            LIMIT :limit;
            '''
            
            query_parameters = {'card_id': card_id, 'lang':lang, 'limit':limit}

            logging.debug("detailed query: '{0}' / {1}".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            # I expect 1 record
            logging.debug("response: '{0}'".format(records[0]))         

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

                #
                # Translate
                #

                category = records[0]["category"]
                trans = Translator.getInstance(lang)
        
                # Writers
                writers_string = records[0]["writers"]
                writers_list = []
                if writers_string:
                    writers_list = writers_string.split(',')
                records[0]["writers"] = writers_list

                # Directors
                directors_string = records[0]["directors"]
                directors_list = []
                if directors_string:
                    directors_list = directors_string.split(',')
                records[0]["directors"] = directors_list

                # Stars
                stars_string = records[0]["stars"]
                stars_list = []
                if stars_string:
                    stars_list = stars_string.split(',')
                records[0]["stars"] = stars_list

                # Actors
                actors_string = records[0]["actors"]
                actors_list = []
                if actors_string:
                    actors_list = actors_string.split(',')
                records[0]["actors"] = actors_list

                # Voices
                voices_string = records[0]["voices"]
                voices_list = []
                if voices_string:
                    voices_list = voices_string.split(',')
                records[0]["voices"] = voices_list

                # Host
                hosts_string = records[0]["hosts"]
                hosts_list = []
                if hosts_string:
                    hosts_list = hosts_string.split(',')
                records[0]["hosts"] = hosts_list

                # Guests
                guests_string = records[0]["guests"]
                guests_list = []
                if guests_string:
                    guests_list = guests_string.split(',')
                records[0]["guests"] = guests_list

                # Interviewers
                interviewers_string = records[0]["interviewers"]
                interviewers_list = []
                if interviewers_string:
                    interviewers_list = interviewers_string.split(',')
                records[0]["interviewers"] = interviewers_list

                # Interviewees
                interviewees_string = records[0]["interviewees"]
                interviewees_list = []
                if interviewees_string:
                    interviewees_list = interviewees_string.split(',')
                records[0]["interviewees"] = interviewees_list

                # Presenters
                presenters_string = records[0]["presenters"]
                presenters_list = []
                if presenters_string:
                    presenters_list = presenters_string.split(',')
                records[0]["presenters"] = presenters_list

                # Lecturers
                lecturers_string = records[0]["lecturers"]
                lecturers_list = []
                if lecturers_string:
                    lecturers_list = lecturers_string.split(',')
                records[0]["lecturers"] = lecturers_list

                # Performers
                performers_string = records[0]["performers"]
                performers_list = []
                if performers_string:
                    performers_list = performers_string.split(',')
                records[0]["performers"] = performers_list

                # Reporters
                reporters_string = records[0]["reporters"]
                reporters_list = []
                if reporters_string:
                    reporters_list = reporters_string.split(',')
                records[0]["reporters"] = reporters_list

                # Genre
                genres_string = records[0]["genres"]
                genres_list = []
                if genres_string:
                    genres_list = genres_string.split(',')
                    genres_list = [trans.translate_genre(category=category, genre=genre) for genre in genres_list]
                records[0]["genres"] = genres_list

                # Theme
                themes_string = records[0]["themes"]
                themes_list = []
                if themes_string:
                    themes_list = themes_string.split(',')
                    themes_list = [trans.translate_theme(theme=theme) for theme in themes_list]
                records[0]["themes"] = themes_list

                # Origin
                origins_string = records[0]["origins"]
                origins_list = []
                if origins_string:
                    origins_list = origins_string.split(',')
                    origins_list = [trans.translate_country_long(origin) for origin in origins_list]
                records[0]["origins"] = origins_list

                # Sub
                subs_string = records[0]["subs"]
                subs_list = []
                if subs_string:
                    subs_list = subs_string.split(',')
                    subs_list = [trans.translate_language_long(sub) for sub in subs_list]
                records[0]["subs"] = subs_list

                # Sounds
                sounds_string = records[0]["sounds"]

                sounds_list = []
                if sounds_string:
                    sounds_list = sounds_string.split(',')
                    sounds_list = [trans.translate_language_long(sounds) for sounds in sounds_list]
                records[0]["sounds"] = sounds_list

                # Media
                medium_string = records[0]["medium"]
                media_dict = {}
                if medium_string:
                    medium_string_list = medium_string.split(',')
                    for medium_string in medium_string_list:
                        (media_type, media) = medium_string.split("=")
                        if not media_type in media_dict:
                            media_dict[media_type] = []
                        media_dict[media_type].append(media)
                records[0]["medium"] = media_dict

            return records







    #
    #
    #
    # Detailed Card for appendix
    #
    # more records can be fetched
    #
    def get_all_appendix(self, card_id, lang='en', limit=100, json=True):
             
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            query = '''
            SELECT 
                merged.id id, 
                MAX(title_req) title_req, 
                MAX(title_orig) title_orig, 
                MAX(lang_orig) lang_orig,
                MAX(lang_req) lang_req,
                sequence,
                show,
                download,
                source_path,
                media
            FROM (
                SELECT 
                    card.id id, 
                    card.id_category id_category,
                    NULL title_req, 
                    NULL lang_req, 
                    tcl.text title_orig, 
                    lang.name lang_orig,
                    card.sequence sequence,
                    card.show,
                    card.download,
                    card.source_path source_path
                FROM 
                    
                    CARD card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                   
                WHERE
                
                    tcl.id_card=card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND card.id_title_orig=lang.id

                    AND card.id_higher_card = :card_id
                    AND lang.name <> :lang

                UNION

                SELECT 
                    card.id id,
                    card.id_category id_category,
                    tcl.text title_req, 
                    lang.name lang_req, 
                    NULL title_orig, 
                    NULL lang_orig,
                    card.sequence sequence,
                    card.show,
                    card.download,
                    card.source_path source_path
                FROM 
               
                    CARD card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE
               
                    tcl.id_card=card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"

                    AND card.id_higher_card = :card_id 
                    AND lang.name=:lang
                ) merged,

               (SELECT group_concat( mt.name || "=" || m.name) media, m.id_card card_id
                    FROM 
                        Card c,
                        Card_Media m,
                        MediaType mt
                    WHERE
                        c.id = m.id_card
                        AND m.id_mediatype = mt.id
                        AND c.isappendix=1
                    GROUP BY c.id
                ) media

            WHERE media.card_id = merged.id
            GROUP BY merged.id
            ORDER BY sequence
            LIMIT :limit;           
            '''

            query_parameters = {'card_id': card_id, 'lang': lang, 'limit': limit}            

            logging.debug("get_appendix query: '{0}' / {1}".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

                #
                # Translate
                #

                trans = Translator.getInstance(lang)

                for record in records:

                    # Lang Orig
                    lang_orig = record["lang_orig"]
                    lang_orig_translated = trans.translate_language_short(lang_orig)
                    record["lang_orig"] = lang_orig_translated

                    # Lang Req
                    lang_req = record["lang_req"]
                    lang_req_translated = trans.translate_language_short(lang_req)
                    record["lang_req"] = lang_req_translated

                    # Media
                    medium_string = record["media"]
                    media_dict = {}
                    if medium_string:
                        medium_string_list = medium_string.split(',')
                        for medium_string in medium_string_list:
                            (media_type, media) = medium_string.split("=")
                            if not media_type in media_dict:
                                media_dict[media_type] = []
                            media_dict[media_type].append(media)
                    record["media"] = media_dict

            return records



    def get_medium_by_card_id(self, card_id, limit=100, json=True):
        """
        It returns a list of medium by the card id.
        Return fields:
            card_id:     card ID
            file_name:   name of the media file
            source_path: source path of the media file
        Example:
            records=db.get_medium_path_list(card_id=33, limit=100)
        Output:
            [{"card_id": 33, "file_name": "PsycheEsNarcisz-1-1980.m4v", source_path: "MEDIA/01.Movie/01.Standalone/Amerikai.Pszicho-2000"}] 
        """
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            query = '''
                SELECT 
                    card.id card_id,
                    card.source_path,
                    medium.name file_name
                FROM 
                    Card card, 
                    Medium medium
                WHERE
                    card.id = :card_id AND
                    card.id=medium.id_card
                ORDER BY file_name
                LIMIT :limit;
            '''
            records=cur.execute(query, {'card_id': card_id, 'limit':limit}).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

            return records



















# ================================================================================================================================================
# ================================================================================================================================================
# ================================================================================================================================================
# TODO: use variables for tables
#''' + SqlDatabase.TABLE_CARD + ''' card,
#''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
#''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
#''' + SqlDatabase.TABLE_CARD + ''' card,
#''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
#''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
#''' + SqlDatabase.TABLE_COUNTRY + ''' country,
#''' + SqlDatabase.TABLE_CARD_ORIGIN + ''' co,
#''' + SqlDatabase.TABLE_PERSON + ''' actor,
#''' + SqlDatabase.TABLE_CARD_ACTOR + ''' ca,
#''' + SqlDatabase.TABLE_PERSON + ''' director,
#''' + SqlDatabase.TABLE_CARD_DIRECTOR + ''' cd,
#'' + SqlDatabase.TABLE_CATEGORY + ''' cat ''' + ('''





    def get_highest_level_cards(self, category, level=None, genres=None, themes=None, directors=None, actors=None, lecturers=None, origins=None, decade=None, lang='en', limit=100, json=True):
        """
        FULL QUERY for highest level list                ---
        Returns mixed standalone media and level cards   ---
        With filters category/genre                      ---

        Why need to use recursive search?                ---
        Because I filter by the lower level card (media) ---
        but I show the highest                           ---
                                                                       
        Parameters for filtering:
          - category
          - level
          - decade                                                     
          - language                                                   
                                                                       
          logical operands (_AND_, _NOT_) in                           
          - genres                                                     
          - themes                                                     
          - actors                                                     
          - directors                                                  
          - lecturers                                                 
          - origins                                                    
        """
        with self.lock:

            genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
            themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
            actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors')
            directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
            lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
            origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            query = '''

SELECT
    core.*,

    mixed_id_list.id_higher_card,
    mixed_id_list.category,
    mixed_id_list.level,
    mixed_id_list.source_path,
    mixed_id_list.basename,        
    mixed_id_list.sequence,
    
    mixed_id_list.title_on_thumbnail,
    mixed_id_list.title_show_sequence,

    mixed_id_list.decade,
    mixed_id_list.date,
    mixed_id_list.length,     
    
    
    mixed_id_list.themes,
    mixed_id_list.genres,
    mixed_id_list.origins,
    mixed_id_list.directors,
    mixed_id_list.actors,

    mixed_id_list.sounds,
    mixed_id_list.subs,
    mixed_id_list.writers,
    mixed_id_list.voices,
    mixed_id_list.stars,
    mixed_id_list.lecturers,
    
    mixed_id_list.hosts,
    mixed_id_list.guests,
    mixed_id_list.interviewers,
    mixed_id_list.interviewees,
    mixed_id_list.presenters,
    mixed_id_list.reporters,
    mixed_id_list.performers,

    storyline,
    lyrics,
    medium,
    appendix
FROM

    ---------------------------
    --- mixed level id list ---
    ---------------------------
    (
    WITH RECURSIVE
        rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers) AS
        
        (
            SELECT                 
                card.id, 
                card.id_higher_card,
                category.name category,
                card.level,
                card.source_path,
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                card.decade,
                card.date,
                card.length,     
                
                themes,
                genres,
                origins,
                directors,
                actors,
                lecturers,
                
                sounds,
                subs,
                writers,
                voices,
                stars,        
                hosts,
                guests,
                interviewers,
                interviewees,
                presenters,
                reporters,
                performers
                
            FROM 
                Card card,
                
                --- Conditional ---
                Category category
            
            -------------
            --- GENRE ---
            -------------
            LEFT JOIN 
            (
                SELECT group_concat(genre.name) genres, card_genre.id_card
                FROM
                    Genre genre,
                    Card_Genre card_genre
                WHERE            
                    card_genre.id_genre=genre.id
                GROUP BY card_genre.id_card
            )gnr
            ON gnr.id_card=card.id
            
            -------------
            --- THEME ---
            -------------
            LEFT JOIN 
            (
                SELECT group_concat(theme.name) themes, card_theme.id_card
                FROM
                    Theme theme,
                    Card_Theme card_theme
                WHERE            
                    card_theme.id_theme=theme.id
                GROUP BY card_theme.id_card
            )thm
            ON thm.id_card=card.id
    
            ---------------
            --- ORIGINS ---
            ---------------
            LEFT JOIN
            (
                SELECT group_concat(origin.name) origins, card_origin.id_card
                FROM
                    Country origin,
                    Card_Origin card_origin
                WHERE
                    card_origin.id_origin=origin.id
                GROUP BY card_origin.id_card
            )rgn
            ON rgn.id_card=card.id    
    
            -----------------
            --- DIRECTORS ---
            -----------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) directors,  card_dir.id_card
                FROM 
                    Person person,
                    Card_Director card_dir
                WHERE 
                    card_dir.id_director = person.id
                GROUP BY card_dir.id_card
            ) dr
            ON dr.id_card=card.id

            --------------
            --- ACTORS ---
            --------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) actors,  card_actor.id_card
                FROM 
                    Person person,
                    Card_Actor card_actor
                WHERE 
                    card_actor.id_actor = person.id
                GROUP BY card_actor.id_card
            ) act
            ON act.id_card=card.id
    
            ----------------
            --- LECTURER ---
            ----------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) lecturers,  card_lecturer.id_card
                FROM 
                    Person person,
                    Card_Lecturer card_lecturer
                WHERE 
                    card_lecturer.id_lecturer = person.id
                GROUP BY card_lecturer.id_card
            ) lctr
            ON lctr.id_card=card.id           
    
            --- No Filter ---

            --------------
            --- SOUNDS ---
            --------------
            LEFT JOIN 
            (
                SELECT group_concat(language.name) sounds, card_sound.id_card
                FROM 
                    Language language,
                    Card_Sound card_sound
                WHERE 
                    card_sound.id_sound=language.id 
                GROUP BY card_sound.id_card
            ) snd
            ON snd.id_card=card.id

            ----------------
            --- SUBTITLE ---
            ----------------
            LEFT JOIN
            (
                SELECT group_concat(language.name) subs, card_sub.id_card
                FROM 
                    Language language,
                    Card_Sub card_sub
                WHERE 
                    card_sub.id_sub=language.id
                GROUP BY card_sub.id_card
            ) sb
            ON sb.id_card=card.id

            ---------------
            --- WRITERS ---
            ---------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) writers,  card_writer.id_card
                FROM 
                    Person person,
                    Card_Writer card_writer
                WHERE 
                    card_writer.id_writer = person.id
                GROUP BY card_writer.id_card
            ) wr
            ON wr.id_card=card.id

            --------------
            --- VOICES ---
            --------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) voices,  card_voice.id_card
                FROM 
                    Person person,
                    Card_Voice card_voice
                WHERE 
                    card_voice.id_voice = person.id
                GROUP BY card_voice.id_card
            ) vc
            ON vc.id_card=card.id    

            -------------
            --- STARS ---
            -------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) stars,  card_star.id_card
                FROM 
                    Person person,
                    Card_Star card_star
                WHERE 
                    card_star.id_star = person.id
                GROUP BY card_star.id_card
            ) str
            ON str.id_card=card.id

            -------------
            --- HOSTS ---
            -------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) hosts,  card_host.id_card
                FROM 
                    Person person,
                    Card_Host card_host
                WHERE 
                    card_host.id_host = person.id
                GROUP BY card_host.id_card
            ) hst
            ON hst.id_card=card.id    
    
            --------------
            --- GUESTS ---
            --------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) guests,  card_guest.id_card
                FROM 
                    Person person,
                    Card_Guest card_guest
                WHERE 
                    card_guest.id_guest = person.id
                GROUP BY card_guest.id_card
            ) gst
            ON gst.id_card=card.id
            
            ---------------------
            --- INTERVIEWERS  ---
            ---------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) interviewers,  card_interviewer.id_card
                FROM 
                    Person person,
                    Card_Interviewer card_interviewer
                WHERE 
                    card_interviewer.id_interviewer = person.id
                GROUP BY card_interviewer.id_card
            ) ntrvwr
            ON ntrvwr.id_card=card.id

            ---------------------
            --- INTERVIEWEES  ---
            ---------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) interviewees,  card_interviewee.id_card
                FROM 
                    Person person,
                    Card_Interviewee card_interviewee
                WHERE 
                    card_interviewee.id_interviewee = person.id
                GROUP BY card_interviewee.id_card
            ) ntrw
            ON ntrw.id_card=card.id

            -------------------
            --- PRESENTERS  ---
            -------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) presenters,  card_presenter.id_card
                FROM 
                    Person person,
                    Card_Presenter card_presenter
                WHERE 
                    card_presenter.id_presenter = person.id
                GROUP BY card_presenter.id_card
            ) prsntr
            ON prsntr.id_card=card.id

            ------------------
            --- REPORTERS  ---
            ------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) reporters,  card_reporter.id_card
                FROM 
                    Person person,
                    Card_Reporter card_reporter
                WHERE 
                    card_reporter.id_reporter = person.id
                GROUP BY card_reporter.id_card
            ) rprtr
            ON rprtr.id_card=card.id

            ------------------
            --- PERFORMER  ---
            ------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) performers,  card_performer.id_card
                FROM 
                    Person person,
                    Card_Performer card_performer
                WHERE 
                    card_performer.id_performer = person.id
                GROUP BY card_performer.id_card
            ) prfrmr
            ON prfrmr.id_card=card.id            

            ------------------------
            --- Initial WHERE    ---
            --- the lowest level ---
            ------------------------
            
            WHERE 
                -- card can not be appendix --
                card.isappendix == 0

                -- connect card to category --
                AND category.id=card.id_category

                -- Find the lowest level --
                AND card.level IS NULL
               
                -- Select the given category --
                AND category.name = :category

                -------------------
                -------------------
                --- Conditional ---
                ---   filter    ---
                -------------------
                -------------------

                --- WHERE DECADE ---
                AND CASE
                    WHEN :decade IS NOT NULL THEN card.decade = :decade ELSE 1
                END

                ''' + ('''                
                --- WHERE THEMES - conditional ---
                AND ''' + themes_where if themes_where else '') + '''
                
                ''' + ('''
                --- WHERE GENRES - conditional ---
                AND ''' + genres_where if genres_where else '') + '''

                ''' + ('''               
                --- WHERE DIRECTORS - conditional ---
                AND ''' + directors_where if directors_where else '') + '''
               
                ''' + ('''
                --- WHERE ACTORS - conditional ---
                AND ''' + actors_where if actors_where else '') + '''

                ''' + ('''
                --- WHERE ORIGINS - conditional ---
                AND ''' + origins_where if origins_where else '') + '''

                ''' + ('''
                --- WHERE LECTURERS - conditional ---
                AND ''' + lecturers_where if lecturers_where else '') + '''
                
            UNION ALL

            SELECT 
                card.id,
                card.id_higher_card,
                category.name category,
                card.level,
                card.source_path,
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                NULL decade,
                NULL date,
                NULL length,
                
                NULL themes,
                NULL genres,
                NULL origins,
                NULL directors,
                NULL actors,
                NULL lecturers,
                NULL sounds,
                NULL subs,
                NULL writers,
                NULL voices,
                NULL stars,
                NULL hosts,
                NULL guests,
                NULL interviewers,
                NULL interviewees,
                NULL presenters,
                NULL reporters,
                NULL performers
                
            FROM
                rec,
                Card card,
                Category category
            WHERE
                rec.id_higher_card=card.id
                AND category.id=card.id_category
        )
    SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers
    
    FROM
        rec
    WHERE

        -------------------
        -------------------
        --- Conditional ---
        ---   filter    ---
        -------------------
        -------------------
    
        --- if :level is set, then takes that specific level as highest level
        --- if :level is NOT set, then takes the highest level
        CASE
            WHEN :level IS NULL THEN id_higher_card IS NULL ELSE level = :level
        END

    GROUP BY id
    ) mixed_id_list,
    
    --------------------------
    --- unioned with title ---
    --------------------------
    (
    SELECT 
        unioned.id id,
                
        MAX(title_req) title_req, 
        MAX(title_orig) title_orig, 
        MAX(lang_orig) lang_orig,
        MAX(lang_req) lang_req

    FROM 
        (
        SELECT 
            card.id id, 

            NULL title_req, 
            NULL lang_req, 
            tcl.text title_orig, 
            lang.name lang_orig
        FROM                     
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE                
            tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
            AND card.id_title_orig=lang.id

            AND card.isappendix = 0
            AND lang.name <> :lang
        UNION

        SELECT 
            card.id id,

            tcl.text title_req, 
            lang.name lang_req, 
            NULL title_orig, 
            NULL lang_orig
        FROM               
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE               
            tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
 
            AND card.isappendix = 0
            AND lang.name=:lang
        ) unioned

    -- because of the title required and origin
    GROUP BY unioned.id               

    ) core
  
    -----------------
    --- STORYLINE ---
    -----------------
    LEFT JOIN
    (
        SELECT ord, storyline, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the storyline on the original language ---

            SELECT "2" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
--        HAVING MIN(ord)
--        ORDER BY ord
    )strl
    ON strl.id_card=core.id
   
    --------------
    --- LYRICS ---
    --------------
    LEFT JOIN
    (
        SELECT ord, lyrics, id_card
        FROM
        (

            --- Select the lyrics on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the lyrics on the original language ---

            SELECT "2" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
    )lrx
    ON lrx.id_card=core.id       
   
    --------------
    --- MEDIUM ---
    --------------
    LEFT JOIN
    (
        SELECT group_concat( media_type.name || "=" || card_media.name) medium, card_media.id_card
        FROM
            MediaType media_type,
            Card_Media card_media
        WHERE
            card_media.id_mediatype=media_type.id
        GROUP BY card_media.id_card
    )mdt
    ON mdt.id_card=core.id
   
    ----------------
    --- APPENDIX ---
    ----------------
     LEFT JOIN    
    (    
        SELECT
            card_id,
            group_concat("id=" || id || ";mt=" || media_type || ";cm=" || contact_media || ";sw=" || show || ";dl=" || download || ";rt=" || title_req || ";ot=" || title_orig || ";sp=" || source_path) appendix
        FROM
        
            (
            SELECT                
                merged_appendix.id,
                merged_appendix.card_id,
                MAX(merged_appendix.title_req) title_req, 
                MAX(merged_appendix.title_orig) title_orig,
                merged_appendix.show,
                merged_appendix.download,
                merged_appendix.source_path,
                mt.name media_type,
                cm.name contact_media                
            FROM
                (
                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    "" title_req, 
                    tcl.text title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE                
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND app_card.id_title_orig=lang.id
                    AND lang.name <> :lang

                UNION

                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    tcl.text title_req, 
                    "" title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND lang.name=:lang
                ) merged_appendix,
                Card_Media cm,
                MediaType mt
                
            WHERE
                cm.id_card=merged_appendix.id
                AND mt.id=cm.id_mediatype
                
            GROUP BY merged_appendix.id
            )
        GROUP BY card_id
    ) pndx
    ON pndx.card_id=core.id

WHERE
    mixed_id_list.id=core.id
                    
ORDER BY CASE 
    WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
    WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
    WHEN sequence<0 THEN basename
    WHEN sequence>=0 THEN sequence
END
LIMIT :limit; '''

            query_parameters = {'level': level, 'category': category, 'decade': decade, 'lang': lang, 'limit': limit}

            logging.error("get_highest_level_cards query: '{0}' / {1}".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            if json:
                records = self.get_converted_query_to_json(records, category, lang)

            return records


# ---


    def get_next_level_cards(self, card_id, category, genres=None, themes=None, directors=None, actors=None, lecturers=None, origins=None, decade=None, lang='en', limit=100, json=True):
        """
        FULL QUERY for the children cards of the given card
        Returns the next child cards which could ne:                                           
          - media card        
          - level cards
                                                                       
        Parameters for filtering:
          - category                                                   
          - decade                                                     
          - language                                                   
                                                                       
          logical operands (_AND_, _NOT_) in                           
          - genres                                                     
          - themes                                                     
          - actors                                                     
          - directors                                                  
          - lecturers                                                 
          - origins                                                    
        """
        with self.lock:
            where = ''

            genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
            themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
            actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors')
            directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
            lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
            origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            query = '''

SELECT
    core.*,

    mixed_id_list.id_higher_card,
    mixed_id_list.category,
    mixed_id_list.level,
    mixed_id_list.source_path,
    mixed_id_list.basename,        
    mixed_id_list.sequence,
    
    mixed_id_list.title_on_thumbnail,
    mixed_id_list.title_show_sequence,

    mixed_id_list.decade,
    mixed_id_list.date,
    mixed_id_list.length,     
    
    
    mixed_id_list.themes,
    mixed_id_list.genres,
    mixed_id_list.origins,
    mixed_id_list.directors,
    mixed_id_list.actors,

    mixed_id_list.sounds,
    mixed_id_list.subs,
    mixed_id_list.writers,
    mixed_id_list.voices,
    mixed_id_list.stars,
    mixed_id_list.lecturers,
    
    mixed_id_list.hosts,
    mixed_id_list.guests,
    mixed_id_list.interviewers,
    mixed_id_list.interviewees,
    mixed_id_list.presenters,
    mixed_id_list.reporters,
    mixed_id_list.performers,

    storyline,
    lyrics,
    medium,
    appendix
FROM

    ---------------------------
    --- mixed level id list ---
    ---------------------------
    (
    WITH RECURSIVE
        rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers) AS
        
        (
            SELECT                 
                card.id, 
                card.id_higher_card,
                category.name category,
                card.level,
                card.source_path,
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                card.decade,
                card.date,
                card.length,     
                
                themes,
                genres,
                origins,
                directors,
                actors,
                lecturers,
                
                sounds,
                subs,
                writers,
                voices,
                stars,        
                hosts,
                guests,
                interviewers,
                interviewees,
                presenters,
                reporters,
                performers
                
            FROM 
                Card card,
                
                --- Conditional ---
                Category category
            
            -------------
            --- GENRE ---
            -------------
            LEFT JOIN 
            (
                SELECT group_concat(genre.name) genres, card_genre.id_card
                FROM
                    Genre genre,
                    Card_Genre card_genre
                WHERE            
                    card_genre.id_genre=genre.id
                GROUP BY card_genre.id_card
            )gnr
            ON gnr.id_card=card.id
            
            -------------
            --- THEME ---
            -------------
            LEFT JOIN 
            (
                SELECT group_concat(theme.name) themes, card_theme.id_card
                FROM
                    Theme theme,
                    Card_Theme card_theme
                WHERE            
                    card_theme.id_theme=theme.id
                GROUP BY card_theme.id_card
            )thm
            ON thm.id_card=card.id
    
            ---------------
            --- ORIGINS ---
            ---------------
            LEFT JOIN
            (
                SELECT group_concat(origin.name) origins, card_origin.id_card
                FROM
                    Country origin,
                    Card_Origin card_origin
                WHERE
                    card_origin.id_origin=origin.id
                GROUP BY card_origin.id_card
            )rgn
            ON rgn.id_card=card.id    
    
            -----------------
            --- DIRECTORS ---
            -----------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) directors,  card_dir.id_card
                FROM 
                    Person person,
                    Card_Director card_dir
                WHERE 
                    card_dir.id_director = person.id
                GROUP BY card_dir.id_card
            ) dr
            ON dr.id_card=card.id

            --------------
            --- ACTORS ---
            --------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) actors,  card_actor.id_card
                FROM 
                    Person person,
                    Card_Actor card_actor
                WHERE 
                    card_actor.id_actor = person.id
                GROUP BY card_actor.id_card
            ) act
            ON act.id_card=card.id
    
            ----------------
            --- LECTURER ---
            ----------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) lecturers,  card_lecturer.id_card
                FROM 
                    Person person,
                    Card_Lecturer card_lecturer
                WHERE 
                    card_lecturer.id_lecturer = person.id
                GROUP BY card_lecturer.id_card
            ) lctr
            ON lctr.id_card=card.id           
    
            --- No Filter ---

            --------------
            --- SOUNDS ---
            --------------
            LEFT JOIN 
            (
                SELECT group_concat(language.name) sounds, card_sound.id_card
                FROM 
                    Language language,
                    Card_Sound card_sound
                WHERE 
                    card_sound.id_sound=language.id 
                GROUP BY card_sound.id_card
            ) snd
            ON snd.id_card=card.id

            ----------------
            --- SUBTITLE ---
            ----------------
            LEFT JOIN
            (
                SELECT group_concat(language.name) subs, card_sub.id_card
                FROM 
                    Language language,
                    Card_Sub card_sub
                WHERE 
                    card_sub.id_sub=language.id
                GROUP BY card_sub.id_card
            ) sb
            ON sb.id_card=card.id

            ---------------
            --- WRITERS ---
            ---------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) writers,  card_writer.id_card
                FROM 
                    Person person,
                    Card_Writer card_writer
                WHERE 
                    card_writer.id_writer = person.id
                GROUP BY card_writer.id_card
            ) wr
            ON wr.id_card=card.id

            --------------
            --- VOICES ---
            --------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) voices,  card_voice.id_card
                FROM 
                    Person person,
                    Card_Voice card_voice
                WHERE 
                    card_voice.id_voice = person.id
                GROUP BY card_voice.id_card
            ) vc
            ON vc.id_card=card.id    

            -------------
            --- STARS ---
            -------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) stars,  card_star.id_card
                FROM 
                    Person person,
                    Card_Star card_star
                WHERE 
                    card_star.id_star = person.id
                GROUP BY card_star.id_card
            ) str
            ON str.id_card=card.id

            -------------
            --- HOSTS ---
            -------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) hosts,  card_host.id_card
                FROM 
                    Person person,
                    Card_Host card_host
                WHERE 
                    card_host.id_host = person.id
                GROUP BY card_host.id_card
            ) hst
            ON hst.id_card=card.id    
    
            --------------
            --- GUESTS ---
            --------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) guests,  card_guest.id_card
                FROM 
                    Person person,
                    Card_Guest card_guest
                WHERE 
                    card_guest.id_guest = person.id
                GROUP BY card_guest.id_card
            ) gst
            ON gst.id_card=card.id
            
            ---------------------
            --- INTERVIEWERS  ---
            ---------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) interviewers,  card_interviewer.id_card
                FROM 
                    Person person,
                    Card_Interviewer card_interviewer
                WHERE 
                    card_interviewer.id_interviewer = person.id
                GROUP BY card_interviewer.id_card
            ) ntrvwr
            ON ntrvwr.id_card=card.id

            ---------------------
            --- INTERVIEWEES  ---
            ---------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) interviewees,  card_interviewee.id_card
                FROM 
                    Person person,
                    Card_Interviewee card_interviewee
                WHERE 
                    card_interviewee.id_interviewee = person.id
                GROUP BY card_interviewee.id_card
            ) ntrw
            ON ntrw.id_card=card.id

            -------------------
            --- PRESENTERS  ---
            -------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) presenters,  card_presenter.id_card
                FROM 
                    Person person,
                    Card_Presenter card_presenter
                WHERE 
                    card_presenter.id_presenter = person.id
                GROUP BY card_presenter.id_card
            ) prsntr
            ON prsntr.id_card=card.id

            ------------------
            --- REPORTERS  ---
            ------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) reporters,  card_reporter.id_card
                FROM 
                    Person person,
                    Card_Reporter card_reporter
                WHERE 
                    card_reporter.id_reporter = person.id
                GROUP BY card_reporter.id_card
            ) rprtr
            ON rprtr.id_card=card.id

            ------------------
            --- PERFORMER  ---
            ------------------
            LEFT JOIN    
            (
                SELECT group_concat(person.name) performers,  card_performer.id_card
                FROM 
                    Person person,
                    Card_Performer card_performer
                WHERE 
                    card_performer.id_performer = person.id
                GROUP BY card_performer.id_card
            ) prfrmr
            ON prfrmr.id_card=card.id            

            ------------------------
            --- Initial WHERE    ---
            --- the lowest level ---
            ------------------------
            
            WHERE 
                -- card can not be appendix --
                card.isappendix == 0

                -- connect card to category --
                AND category.id=card.id_category

                -- Find the lowest level --
                AND card.level IS NULL
               
                -- Select the given category --
                AND category.name = :category

                -------------------
                -------------------
                --- Conditional ---
                ---   filter    ---
                -------------------
                -------------------

            --- WHERE DECADE ---
            AND CASE
                WHEN :decade IS NOT NULL THEN card.decade = :decade ELSE 1
            END

            ''' + ('''                
            --- WHERE THEMES - conditional ---
            AND ''' + themes_where if themes_where else '') + '''
                
            ''' + ('''
            --- WHERE GENRES - conditional ---
            AND ''' + genres_where if genres_where else '') + '''

            ''' + ('''               
            --- WHERE DIRECTORS - conditional ---
            AND ''' + directors_where if directors_where else '') + '''
               
            ''' + ('''
            --- WHERE ACTORS - conditional ---
            AND ''' + actors_where if actors_where else '') + '''

            ''' + ('''
            --- WHERE ORIGINS - conditional ---
            AND ''' + origins_where if origins_where else '') + '''

            ''' + ('''
            --- WHERE LECTURERS - conditional ---
            AND ''' + lecturers_where if lecturers_where else '') + '''
                
            UNION ALL

            SELECT 
                card.id,
                card.id_higher_card,
                category.name category,
                card.level,
                card.source_path,
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                NULL decade,
                NULL date,
                NULL length,
                
                NULL themes,
                NULL genres,
                NULL origins,
                NULL directors,
                NULL actors,
                NULL lecturers,
                NULL sounds,
                NULL subs,
                NULL writers,
                NULL voices,
                NULL stars,
                NULL hosts,
                NULL guests,
                NULL interviewers,
                NULL interviewees,
                NULL presenters,
                NULL reporters,
                NULL performers
                
            FROM
                rec,
                Card card,
                Category category
            WHERE
                rec.id_higher_card=card.id
                AND category.id=card.id_category
        )
    SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers
    
    FROM
        rec
    WHERE

        -------------------
        -------------------
        --- Conditional ---
        ---   filter    ---
        -------------------
        -------------------
    
    
    
    
        --- if :level is set, then takes that specific level as highest level
        --- if :level is NOT set, then takes the highest level
--        CASE
--            WHEN :level IS NULL THEN id_higher_card IS NULL ELSE level = :level
--        END

        id_higher_card = :card_id

    GROUP BY id
    ) mixed_id_list,
    
    --------------------------
    --- unioned with title ---
    --------------------------
    (
    SELECT 
        unioned.id id,
                
        MAX(title_req) title_req, 
        MAX(title_orig) title_orig, 
        MAX(lang_orig) lang_orig,
        MAX(lang_req) lang_req

    FROM 
        (
        SELECT 
            card.id id, 

            NULL title_req, 
            NULL lang_req, 
            tcl.text title_orig, 
            lang.name lang_orig
        FROM                     
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE                
            tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
            AND card.id_title_orig=lang.id

            AND card.isappendix = 0
            AND lang.name <> :lang
        UNION

        SELECT 
            card.id id,

            tcl.text title_req, 
            lang.name lang_req, 
            NULL title_orig, 
            NULL lang_orig
        FROM               
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE               
            tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
 
            AND card.isappendix = 0
            AND lang.name=:lang
        ) unioned

    -- because of the title required and origin
    GROUP BY unioned.id               

    ) core
  
    -----------------
    --- STORYLINE ---
    -----------------
    LEFT JOIN
    (
        SELECT ord, storyline, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the storyline on the original language ---

            SELECT "2" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
--        HAVING MIN(ord)
--        ORDER BY ord
    )strl
    ON strl.id_card=core.id
   
    --------------
    --- LYRICS ---
    --------------
    LEFT JOIN
    (
        SELECT ord, lyrics, id_card
        FROM
        (

            --- Select the lyrics on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the lyrics on the original language ---

            SELECT "2" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
    )lrx
    ON lrx.id_card=core.id       
   
    --------------
    --- MEDIUM ---
    --------------
    LEFT JOIN
    (
        SELECT group_concat( media_type.name || "=" || card_media.name) medium, card_media.id_card
        FROM
            MediaType media_type,
            Card_Media card_media
        WHERE
            card_media.id_mediatype=media_type.id
        GROUP BY card_media.id_card
    )mdt
    ON mdt.id_card=core.id
   
    ----------------
    --- APPENDIX ---
    ----------------
     LEFT JOIN    
    (    
        SELECT
            card_id,
            group_concat("id=" || id || ";mt=" || media_type || ";cm=" || contact_media || ";sw=" || show || ";dl=" || download || ";rt=" || title_req || ";ot=" || title_orig || ";sp=" || source_path) appendix
        FROM
        
            (
            SELECT                
                merged_appendix.id,
                merged_appendix.card_id,
                MAX(merged_appendix.title_req) title_req, 
                MAX(merged_appendix.title_orig) title_orig,
                merged_appendix.show,
                merged_appendix.download,
                merged_appendix.source_path,
                mt.name media_type,
                cm.name contact_media                
            FROM
                (
                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    "" title_req, 
                    tcl.text title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE                
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND app_card.id_title_orig=lang.id
                    AND lang.name <> :lang

                UNION

                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    tcl.text title_req, 
                    "" title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND lang.name=:lang
                ) merged_appendix,
                Card_Media cm,
                MediaType mt
                
            WHERE
                cm.id_card=merged_appendix.id
                AND mt.id=cm.id_mediatype
                
            GROUP BY merged_appendix.id
            )
        GROUP BY card_id
    ) pndx
    ON pndx.card_id=core.id

WHERE
    mixed_id_list.id=core.id
                    
ORDER BY CASE 
    WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
    WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
    WHEN sequence<0 THEN basename
    WHEN sequence>=0 THEN sequence
END
LIMIT :limit;

'''
            query_parameters = {'card_id': card_id, 'category': category, 'decade': decade, 'lang': lang, 'limit': limit}            

            logging.debug("get_highest_level_cards query: '{0}' / {1}".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            if json:
                records = self.get_converted_query_to_json(records, category, lang)

            return records


# ---


    def get_lowest_level_cards(self, category, level=None, genres=None, themes=None, directors=None, actors=None, lecturers=None, origins=None, decade=None, lang='en', limit=100, json=True):
        """
        FULL QUERY for lowest (medium) level list
        Returns only medium level cards level cards
        With filters category/genre/theme/origin/director/actor 
                                                                       
        Parameters for filtering:
          - category
          - level                                                  
          - decade                                                     
          - language                                                   
                                                                       
          logical operands (_AND_, _NOT_) in                           
          - genres                                                     
          - themes                                                     
          - actors                                                     
          - directors                                                  
          - lecturers                                                 
          - origins                                                    
        """
        with self.lock:

            genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
            themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
            actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors')
            directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
            lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
            origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            query = '''

SELECT 
    recursive_list.*,

    category.name category,
    themes,
    genres,
    origins,
    directors,
    actors,

    sounds,
    subs,
    writers,
    voices,
    stars,
    lecturers,
    
    hosts,
    guests,
    interviewers,
    interviewees,
    presenters,
    reporters,
    performers,
    
    storyline,
    lyrics,
    medium,
    appendix
FROM
    (
    WITH RECURSIVE
        rec(id, id_higher_card,level, source_path, title_req, title_orig, lang_orig, lang_req, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, ord) AS
        
        (
            SELECT
            
                card.id, 
                card.id_higher_card, 
                card.level,
                card.source_path,
                
                core.title_req, 
                core.title_orig, 
                core.lang_orig,
                core.lang_req,
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                NULL decade,
                NULL date,
                NULL length,
              
                CASE 
                    WHEN sequence IS NULL AND core.title_req IS NOT NULL THEN core.title_req
                    WHEN sequence IS NULL AND core.title_orig IS NOT NULL THEN core.title_orig
                    WHEN sequence<0 THEN basename
                END ord

            FROM 
                Card card,
                
                (
                SELECT 
                    unioned.id id,
                
                    MAX(title_req) title_req, 
                    MAX(title_orig) title_orig, 
                    MAX(lang_orig) lang_orig,
                    MAX(lang_req) lang_req

                FROM 
                    (
                    SELECT 
                        card.id id, 

                        NULL title_req, 
                        NULL lang_req, 
                        tcl.text title_orig, 
                        lang.name lang_orig
                    FROM                     
                        Card card,
                        Text_Card_Lang tcl, 
                        Language lang                    
                    WHERE                
                        tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"
                        AND card.id_title_orig=lang.id

                        AND card.isappendix = 0
                        AND lang.name <> :lang
                    UNION

                    SELECT 
                        card.id id,

                        tcl.text title_req, 
                        lang.name lang_req, 
                        NULL title_orig, 
                        NULL lang_orig
                    FROM               
                        Card card,
                        Text_Card_Lang tcl, 
                        Language lang                    
                    WHERE               
                        tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"
 
                        AND card.isappendix = 0
                        AND lang.name=:lang
                    ) unioned

                -- because of the title required and origin
                GROUP BY unioned.id               

                ) core,               
                
                
                --- Conditional ---
                Category category
            
            ------------------------
            --- Initial WHERE    ---
            --- the lowest level ---
            ------------------------
            
            WHERE 

                core.id = card.id
            
                -- connect card to category --
                AND category.id=card.id_category

                -- card can not be appendix --
                AND card.isappendix == 0

                -- Find the highest level --
                --- if :level is set, then takes that specific level as highest level
                --- if :level is NOT set, then takes the highest level
                AND CASE
                    WHEN :level IS NULL THEN id_higher_card IS NULL ELSE card.level = :level
                END                
   
                -- Select the given category --
                AND category.name = :category
                
            UNION ALL

            SELECT                
                card.id,
                card.id_higher_card,
                card.level,
                card.source_path,
                
                core.title_req, 
                core.title_orig, 
                core.lang_orig,
                core.lang_req,                
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                card.decade,
                card.date,
                card.length,     
                
                CASE 
                    WHEN card.sequence IS NULL AND core.title_req IS NOT NULL THEN ord || '_' || core.title_req
                    WHEN card.sequence IS NULL AND core.title_orig IS NOT NULL THEN ord || '_' || core.title_orig
                    WHEN card.sequence<0 THEN ord || '_' || card.basename
                    WHEN card.sequence>=0 THEN ord || '_' || card.sequence
                END ord                
  
            FROM
                rec,
                Card card,
                
                
                (
                SELECT 
                    unioned.id id,
                
                    MAX(title_req) title_req, 
                    MAX(title_orig) title_orig, 
                    MAX(lang_orig) lang_orig,
                    MAX(lang_req) lang_req

                FROM 
                    (
                    SELECT 
                        card.id id, 

                        NULL title_req, 
                        NULL lang_req, 
                        tcl.text title_orig, 
                        lang.name lang_orig
                    FROM                     
                        Card card,
                        Text_Card_Lang tcl, 
                        Language lang                    
                    WHERE                
                        tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"
                        AND card.id_title_orig=lang.id

                        AND card.isappendix = 0
                        AND lang.name <> :lang
                    UNION

                    SELECT 
                        card.id id,

                        tcl.text title_req, 
                        lang.name lang_req, 
                        NULL title_orig, 
                        NULL lang_orig
                    FROM               
                        Card card,
                        Text_Card_Lang tcl, 
                        Language lang                    
                    WHERE               
                        tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"
 
                        AND card.isappendix = 0
                        AND lang.name=:lang
                    ) unioned

                -- because of the title required and origin
                GROUP BY unioned.id               

                ) core                                
                
                
            WHERE
 
                card.id_higher_card=rec.id
                AND core.id = card.id

        )
    SELECT id, id_higher_card, level, source_path, title_req, title_orig, lang_orig, lang_req, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, ord
    
    FROM
        rec
    WHERE

        level IS NULL

    GROUP BY id
   
    ) recursive_list,
    Card card,
    Category category
    
    -------------
    --- GENRE ---
    -------------
    LEFT JOIN 
    (
        SELECT group_concat(genre.name) genres, card_genre.id_card
        FROM
            Genre genre,
            Card_Genre card_genre
        WHERE            
            card_genre.id_genre=genre.id
        GROUP BY card_genre.id_card
    )gnr
    ON gnr.id_card=card.id
            
    -------------
    --- THEME ---
    -------------
    LEFT JOIN 
    (
        SELECT group_concat(theme.name) themes, card_theme.id_card
        FROM
            Theme theme,
            Card_Theme card_theme
        WHERE            
            card_theme.id_theme=theme.id
        GROUP BY card_theme.id_card
    )thm
    ON thm.id_card=card.id            
    
    ---------------
    --- ORIGINS ---
    ---------------
    LEFT JOIN
    (
        SELECT group_concat(origin.name) origins, card_origin.id_card
        FROM
            Country origin,
            Card_Origin card_origin
        WHERE
            card_origin.id_origin=origin.id
        GROUP BY card_origin.id_card
    )rgn
    ON rgn.id_card=card.id    
    
    -----------------
    --- DIRECTORS ---
    -----------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) directors,  card_dir.id_card
        FROM 
            Person person,
            Card_Director card_dir
        WHERE 
            card_dir.id_director = person.id
        GROUP BY card_dir.id_card
    ) dr
    ON dr.id_card=card.id

    --------------
    --- ACTORS ---
    --------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) actors,  card_actor.id_card
        FROM 
            Person person,
            Card_Actor card_actor
        WHERE 
            card_actor.id_actor = person.id
        GROUP BY card_actor.id_card
    ) act
    ON act.id_card=card.id
       
    ----------------
    --- LECTURER ---
    ----------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) lecturers,  card_lecturer.id_card
        FROM 
            Person person,
            Card_Lecturer card_lecturer
        WHERE 
            card_lecturer.id_lecturer = person.id
        GROUP BY card_lecturer.id_card
    ) lctr
    ON lctr.id_card=card.id       
       
    --- No filter ---
       
    --------------
    --- SOUNDS ---
    --------------
    LEFT JOIN 
    (
        SELECT group_concat(language.name) sounds, card_sound.id_card
        FROM 
            Language language,
            Card_Sound card_sound
        WHERE 
            card_sound.id_sound=language.id 
        GROUP BY card_sound.id_card
    ) snd
    ON snd.id_card=card.id

    ----------------
    --- SUBTITLE ---
    ----------------
    LEFT JOIN
    (
        SELECT group_concat(language.name) subs, card_sub.id_card
        FROM 
            Language language,
            Card_Sub card_sub
        WHERE 
            card_sub.id_sub=language.id
        GROUP BY card_sub.id_card
    ) sb
    ON sb.id_card=card.id

    ---------------
    --- WRITERS ---
    ---------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) writers,  card_writer.id_card
        FROM 
            Person person,
            Card_Writer card_writer
        WHERE 
            card_writer.id_writer = person.id
        GROUP BY card_writer.id_card
    ) wr
    ON wr.id_card=card.id

    --------------
    --- VOICES ---
    --------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) voices,  card_voice.id_card
        FROM 
            Person person,
            Card_Voice card_voice
        WHERE 
            card_voice.id_voice = person.id
        GROUP BY card_voice.id_card
    ) vc
    ON vc.id_card=card.id

    -------------
    --- STARS ---
    -------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) stars,  card_star.id_card
        FROM 
            Person person,
            Card_Star card_star
        WHERE 
            card_star.id_star = person.id
        GROUP BY card_star.id_card
    ) str
    ON str.id_card=card.id

    -------------
    --- HOSTS ---
    -------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) hosts,  card_host.id_card
        FROM 
            Person person,
            Card_Host card_host
        WHERE 
            card_host.id_host = person.id
        GROUP BY card_host.id_card
    ) hst
    ON hst.id_card=card.id
    
    --------------
    --- GUESTS ---
    --------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) guests,  card_guest.id_card
        FROM 
            Person person,
            Card_Guest card_guest
        WHERE 
            card_guest.id_guest = person.id
        GROUP BY card_guest.id_card
    ) gst
    ON gst.id_card=card.id

    ---------------------
    --- INTERWIEVERS  ---
    ---------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) interviewers,  card_interviewer.id_card
        FROM 
            Person person,
            Card_Interviewer card_interviewer
        WHERE 
            card_interviewer.id_interviewer = person.id
        GROUP BY card_interviewer.id_card
    ) ntrvwr
    ON ntrvwr.id_card=card.id

    ---------------------
    --- INTERVIEWEES  ---
    ---------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) interviewees,  card_interviewee.id_card
        FROM 
            Person person,
            Card_Interviewee card_interviewee
        WHERE 
            card_interviewee.id_interviewee = person.id
        GROUP BY card_interviewee.id_card
    ) ntrw
    ON ntrw.id_card=card.id

    -------------------
    --- PRESENTERS  ---
    -------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) presenters,  card_presenter.id_card
        FROM 
            Person person,
            Card_Presenter card_presenter
        WHERE 
            card_presenter.id_presenter = person.id
        GROUP BY card_presenter.id_card
    ) prsntr
    ON prsntr.id_card=card.id

    ------------------
    --- REPORTERS  ---
    ------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) reporters,  card_reporter.id_card
        FROM 
            Person person,
            Card_Reporter card_reporter
        WHERE 
            card_reporter.id_reporter = person.id
        GROUP BY card_reporter.id_card
    ) rprtr
    ON rprtr.id_card=card.id
    
    ------------------
    --- PERFORMER  ---
    ------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) performers,  card_performer.id_card
        FROM 
            Person person,
            Card_Performer card_performer
        WHERE 
            card_performer.id_performer = person.id
        GROUP BY card_performer.id_card
    ) prfrmr
    ON prfrmr.id_card=card.id    
    
    ---
    
    -----------------
    --- STORYLINE ---
    -----------------
    LEFT JOIN
    (
        SELECT ord, storyline, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the storyline on the original language ---

            SELECT "2" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
--        HAVING MIN(ord)
--        ORDER BY ord
    )strl
    ON strl.id_card=card.id
   
    --------------
    --- LYRICS ---
    --------------
    LEFT JOIN
    (
        SELECT ord, lyrics, id_card
        FROM
        (

            --- Select the lyrics on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the lyrics on the original language ---

            SELECT "2" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
    )lrx
    ON lrx.id_card=card.id       
   
    --------------
    --- MEDIUM ---
    --------------
    LEFT JOIN
    (
        SELECT group_concat( media_type.name || "=" || card_media.name) medium, card_media.id_card
        FROM
            MediaType media_type,
            Card_Media card_media
        WHERE
            card_media.id_mediatype=media_type.id
        GROUP BY card_media.id_card
    )mdt
    ON mdt.id_card=card.id
   
    ----------------
    --- APPENDIX ---
    ----------------
     LEFT JOIN    
    (    
        SELECT
            card_id,
            group_concat("id=" || id || ";mt=" || media_type || ";cm=" || contact_media || ";sw=" || show || ";dl=" || download || ";rt=" || title_req || ";ot=" || title_orig || ";sp=" || source_path) appendix
        FROM
        
            (
            SELECT                
                merged_appendix.id,
                merged_appendix.card_id,
                MAX(merged_appendix.title_req) title_req, 
                MAX(merged_appendix.title_orig) title_orig,
                merged_appendix.show,
                merged_appendix.download,
                merged_appendix.source_path,
                mt.name media_type,
                cm.name contact_media                
            FROM
                (
                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    "" title_req, 
                    tcl.text title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE                
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND app_card.id_title_orig=lang.id
                    AND lang.name <> :lang

                UNION

                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    tcl.text title_req, 
                    "" title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND lang.name=:lang
                ) merged_appendix,
                Card_Media cm,
                MediaType mt
                
            WHERE
                cm.id_card=merged_appendix.id
                AND mt.id=cm.id_mediatype
                
            GROUP BY merged_appendix.id
            )
        GROUP BY card_id
    ) pndx
    ON pndx.card_id=card.id     

WHERE
    card.id=recursive_list.id
    AND category.id=card.id_category

    -------------------
    -------------------
    --- Conditional ---
    ---   filter    ---
    -------------------
    -------------------

    --- WHERE DECADE ---
    AND CASE
        WHEN :decade IS NOT NULL THEN card.decade = :decade ELSE 1
    END

    ''' + ('''                
    --- WHERE THEMES - conditional ---
    AND ''' + themes_where if themes_where else '') + '''
                
    ''' + ('''
    --- WHERE GENRES - conditional ---
    AND ''' + genres_where if genres_where else '') + '''

    ''' + ('''               
    --- WHERE DIRECTORS - conditional ---
    AND ''' + directors_where if directors_where else '') + '''
               
    ''' + ('''
    --- WHERE ACTORS - conditional ---
    AND ''' + actors_where if actors_where else '') + '''

    ''' + ('''
    --- WHERE ORIGINS - conditional ---
    AND ''' + origins_where if origins_where else '') + '''

    ''' + ('''
    --- WHERE LECTURERS - conditional ---
    AND ''' + lecturers_where if lecturers_where else '') + '''  

ORDER BY ord

LIMIT :limit; '''

            query_parameters = {'category': category, 'level': level, 'decade': decade, 'lang': lang, 'limit': limit}            

            logging.debug("get_highest_level_cards query: '{0}' / {1}".format(query, query_parameters))

            records=cur.execute(query, query_parameters).fetchall()
            cur.execute("commit")

            if json:
                records = self.get_converted_query_to_json(records, category, lang)

            return records



# ---


    def get_sql_where_condition_from_text_filter(self, text_filter, field_name):

        filter_list =        [] if text_filter == None else text_filter.split('_AND_')
        filter_in_list =     [] if text_filter == None else [filter for filter in filter_list if not filter.startswith("_NOT_")]
        filter_not_in_list = [] if text_filter == None else [filter.removeprefix("_NOT_") for filter in filter_list if filter.startswith("_NOT_")]
        filter_where =       None if text_filter == None else ' AND '.join(["',' || " + field_name + " || ',' " + ("NOT " if filter.startswith("_NOT_") else "") + "LIKE '%," + filter.removeprefix("_NOT_") + ",%'" for filter in filter_list])

        logging.error("{} IN LIST: {}".format(field_name, filter_in_list))
        logging.error("{} NOT IN LIST: {}".format(field_name, filter_not_in_list))
        logging.error("{} WHERE: {}".format(field_name, filter_where if filter_where is not None else 'None'))

        return filter_where


    def get_converted_query_to_json(self, sql_record_list, category, lang):
        """
        Convert and translate the given SQL card-response
        """

        records = [{key: record[key] for key in record.keys()} for record in sql_record_list]

        trans = Translator.getInstance(lang)
        for record in records:

            # It is needed to convert ID to string, otherwise I got back a different value in the jquery response if it is too high
            # I could not figure out how this mechanizm works
            # IMPORTANT !!!
            record["id"] = str(record["id"])

            # Lang Orig
            lang_orig = record["lang_orig"]
            lang_orig_translated = trans.translate_language_short(lang_orig)
            record["lang_orig"] = lang_orig_translated
            # Lang Req
            lang_req = record["lang_req"]
            lang_req_translated = trans.translate_language_short(lang_req)
            record["lang_req"] = lang_req_translated
            # Media
            medium_string = record["medium"]
            media_dict = {}
            if medium_string:
                medium_string_list = medium_string.split(',')
                for medium_string in medium_string_list:
                    (media_type, media) = medium_string.split("=")
                    if not media_type in media_dict:
                        media_dict[media_type] = []
                    media_dict[media_type].append(media)
            record["medium"] = media_dict
            # Appendix
            appendix_string = record["appendix"]
            appendix_list = []
            if appendix_string:
                text_list = appendix_string.split(',')
                for appendix_string in text_list:
                    var_list = appendix_string.split(";")
                    appendix_dict = {}
                    for var_pair in var_list:
                        (key, value) = var_pair.split("=")
                        appendix_dict[key] = value
                    appendix_list.append(appendix_dict)
            record["appendix"] = appendix_list
            # Writers
            writers_string = record["writers"]
            writers_list = []
            if writers_string:
                writers_list = writers_string.split(',')
            record["writers"] = writers_list
            # Directors
            directors_string = record["directors"]
            directors_list = []
            if directors_string:
                directors_list = directors_string.split(',')
            record["directors"] = directors_list
            # Stars
            stars_string = record["stars"]
            stars_list = []
            if stars_string:
                stars_list = stars_string.split(',')
            record["stars"] = stars_list
            # Actors
            actors_string = record["actors"]
            actors_list = []
            if actors_string:
                actors_list = actors_string.split(',')
            record["actors"] = actors_list
            # Voices
            voices_string = record["voices"]
            voices_list = []
            if voices_string:
                voices_list = voices_string.split(',')
            record["voices"] = voices_list
            # Host
            hosts_string = record.get("hosts")
            hosts_list = []
            if hosts_string:
                hosts_list = hosts_string.split(',')
            record["hosts"] = hosts_list
            # Guests
            guests_string = record.get("guests")
            guests_list = []
            if guests_string:
                guests_list = guests_string.split(',')
            record["guests"] = guests_list
            # Interviewers
            interviewers_string = record.get("interviewers")
            interviewers_list = []
            if interviewers_string:
                interviewers_list = interviewers_string.split(',')
            record["interviewers"] = interviewers_list
            # Interviewees
            interviewees_string = record.get("interviewees")
            interviewees_list = []
            if interviewees_string:
                interviewees_list = interviewees_string.split(',')
            record["interviewees"] = interviewees_list
            # Presenters
            presenters_string = record.get("presenters")
            presenters_list = []
            if presenters_string:
                presenters_list = presenters_string.split(',')
            record["presenters"] = presenters_list
            # Lecturers
            lecturers_string = record.get("lecturers")
            lecturers_list = []
            if lecturers_string:
                lecturers_list = lecturers_string.split(',')
            record["lecturers"] = lecturers_list
            # Performers
            performers_string = record.get("performers")
            performers_list = []
            if performers_string:
                performers_list = performers_string.split(',')
            record["performers"] = performers_list
            # Reporters
            reporters_string = record.get("reporters")
            reporters_list = []
            if reporters_string:
                reporters_list = reporters_string.split(',')
            record["reporters"] = reporters_list
            # Genre
            genres_string = record.get("genres")
            genres_list = []
            if genres_string:
                genres_list = genres_string.split(',')
                genres_list = [trans.translate_genre(category=category, genre=genre) for genre in genres_list]
            record["genres"] = genres_list
            # Theme
            themes_string = record["themes"]
            themes_list = []
            if themes_string:
                themes_list = themes_string.split(',')
                themes_list = [trans.translate_theme(theme=theme) for theme in themes_list]
            record["themes"] = themes_list
            # Origin
            origins_string = record["origins"]
            origins_list = []
            if origins_string:
                origins_list = origins_string.split(',')
                origins_list = [trans.translate_country_long(origin) for origin in origins_list]
            record["origins"] = origins_list
            # Sub
            subs_string = record["subs"]
            subs_list = []
            if subs_string:
                subs_list = subs_string.split(',')
                subs_list = [trans.translate_language_long(sub) for sub in subs_list]
            record["subs"] = subs_list
            # Sounds
            sounds_string = record["sounds"]
            sounds_list = []
            if sounds_string:
                sounds_list = sounds_string.split(',')
                sounds_list = [trans.translate_language_long(sounds) for sounds in sounds_list]
            record["sounds"] = sounds_list
        logging.debug("Converted records: '{0}'".format(records))

        return records