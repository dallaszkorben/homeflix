import os
import sqlite3
import logging
import hashlib
import locale

from flask import has_request_context, session

from threading import Lock
from sqlite3 import Error
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from homeflix.config.config import getConfig
from homeflix.translator.translator import Translator
from homeflix.exceptions.not_existing_table import NotExistingTable

class SqlDatabase:

    # Media card level condition - cards that represent playable media content
    MEDIA_CARD_LEVEL_CONDITION = "(card.level IS NULL OR card.level = 'record' OR card.level = 'episode')"

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
    TABLE_VOICE_ROLE = "Voice_Role"

    TABLE_USER = "User"
    TABLE_HISTORY = "History"
    TABLE_RATING = "Rating"
    TABLE_TAG = "Tag"

    def __init__(self, web_gadget):
        self.web_gadget = web_gadget

        config = getConfig()
        self.db_path = os.path.join(config["path"], config['card-db-name'])
        self.mediaAbsolutePath = config["media-absolute-path"]

        # used for getting language independent code lists
        self.translator = Translator.getInstance()
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
            SqlDatabase.TABLE_VOICE_ROLE,
        ]

        self.table_personal_list = [
            SqlDatabase.TABLE_USER,
            SqlDatabase.TABLE_HISTORY,
            SqlDatabase.TABLE_RATING,
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

        # set the default locale. The locale.strxfrm needed it for sorting in the right language specific order
        # It depends on the user's selected language - session needed - so it must be set after the login
        self.locale_map = {'hu': 'hu_HU.UTF-8', 'en': 'en_US.UTF-8', 'sv': 'sv_SE.UTF-8'}
        self._set_locale()


    def _set_locale(self):
        """
        Sets the system locale based on the logged-in user's language preference.
        This is crucial for proper string sorting (locale.strxfrm) in language-specific order.

        The locale affects:
        - String collation and sorting order - ! this is the real reason I need it !
        - Date/time formatting
        - Number formatting
        - Character classification

        Must be called after user login since it depends on session data.
        """

        # Attempt to get the logged-in user's language preference
        result = self.get_logged_in_user_data()

        # Use user's preferred language if login successful
        if result['result']:
            language_code = result['data']['language_code']

        else:
            # Fall back to translator's default language if user not logged in
            language_code = self.language

        # Attempt to set the locale using the language-to-locale mapping
        try:

            # Map language code to full locale string (e.g., 'en' -> 'en_US.UTF-8')
            locale.setlocale(locale.LC_ALL, self.locale_map.get(language_code, 'en_US.UTF-8'))

        except locale.Error:

            # Fallback to C.UTF-8 if the desired locale is not available on the system
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')

        # Debug output to verify the set locale
        # print(f"\n\nlocale: {locale.getlocale()}\n\n")


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
        cur.execute("commit")

        for table in self.table_static_list:
            try:
                self.conn.execute("DROP TABLE {0}".format(table))
            except sqlite3.OperationalError as e:
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
                id                     INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name                   TEXT    NOT NULL,
                password               TEXT    NOT NULL,
                is_admin               BOOLEAN NOT NULL CHECK (show_original_title IN (0, 1)),
                id_language            INTEGER NOT NULL,
                descriptor_color       TEXT    NOT NULL,
                show_original_title    BOOLEAN NOT NULL CHECK (show_original_title IN (0, 1)),
                show_lyrics_anyway     BOOLEAN NOT NULL CHECK (show_lyrics_anyway IN (0, 1)),
                show_storyline_anyway  BOOLEAN NOT NULL CHECK (show_storyline_anyway IN (0, 1)),
                play_continuously      BOOLEAN NOT NULL CHECK (play_continuously IN (0, 1)),
                history_days           INTEGER NOT NULL,
                created_epoch          INTEGER NOT NULL,
                FOREIGN KEY (id_language) REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                UNIQUE(name)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_HISTORY + '''(
                start_epoch     INTEGER       NOT NULL,
                recent_epoch    INTEGER       NOT NULL,
                recent_position DECIMAL(10,2) NOT NULL,
                id_card         TEXT          NOT NULL,
                id_user         INTEGER       NOT NULL,
                FOREIGN KEY     (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY     (id_user) REFERENCES ''' + SqlDatabase.TABLE_USER + ''' (id),
                PRIMARY KEY     (id_card, id_user, start_epoch)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_RATING + '''(
                id_card              TEXT    NOT NULL,
                id_user              INTEGER NOT NULL,
                rate                 INTEGER CHECK(rate BETWEEN 0 AND 5),
                skip_continuous_play BOOLEAN NOT NULL CHECK (skip_continuous_play IN (0, 1)),
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_user) REFERENCES ''' + SqlDatabase.TABLE_USER + ''' (id),
                PRIMARY KEY (id_card, id_user)
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_TAG + '''(
                id_card              TEXT    NOT NULL,
                id_user              INTEGER NOT NULL,
                name                 TEXT    NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_user) REFERENCES ''' + SqlDatabase.TABLE_USER + ''' (id),
                PRIMARY KEY (id_card, id_user, name)
            );
        ''')

        self.fill_up_user_table()


    def fill_up_user_table(self):

        with self.lock:
            try:

                cur = self.conn.cursor()
                cur.execute("begin")

                # admin
                username = 'admin'
                password = 'admin'
                is_admin = True
                hashed_password = generate_password_hash(password)
                user_id = 1234
                language_code = 'en'
                descriptor_color = 'rgb(0, 117, 104)'
                show_original_title = True
                show_lyrics_anyway = True
                show_storyline_anyway = True
                history_days = 365
                play_continuously = True

                id = self.append_user(cur, username, password=hashed_password, is_admin=is_admin, user_id=user_id, language_code=language_code, descriptor_color=descriptor_color, show_original_title=show_original_title, show_lyrics_anyway=show_lyrics_anyway, show_storyline_anyway=show_storyline_anyway, play_continuously=play_continuously, history_days=history_days)

                # default
                username = 'default'
                password = 'default'
                is_admin = False
                hashed_password = generate_password_hash(password)
                user_id = 1235
                language_code = 'en'
                descriptor_color = 'rgb(69, 113, 144)'
                show_original_title = True
                show_lyrics_anyway = True
                show_storyline_anyway = True
                history_days = 365
                play_continuously = True

                id = self.append_user(cur, username, password=hashed_password, is_admin=is_admin, user_id=user_id, language_code=language_code, descriptor_color=descriptor_color, show_original_title=show_original_title, show_lyrics_anyway=show_lyrics_anyway, show_storyline_anyway=show_storyline_anyway, play_continuously=play_continuously, history_days=history_days)

            except sqlite3.Error as e:
                error_message = "Filling up the User table FAILED: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.execute("commit")
                cur.close


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
                id                  TEXT        NOT NULL,
                id_title_orig       INTEGER     NOT NULL,
                id_category         INTEGER     NOT NULL,
                isappendix          BOOLEAN     NOT NULL CHECK (isappendix IN (0, 1)),
                show                BOOLEAN     NOT NULL CHECK (show IN (0, 1)),
                download            BOOLEAN     NOT NULL CHECK (download IN (0, 1)),
                decade              TEXT,
                date                TEXT,
                length              TEXT,
                full_time           DECIMAL(10,2),
                net_start_time      DECIMAL(10,2),
                net_stop_time       DECIMAL(10,2),
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

        self.conn.execute('''
           CREATE TABLE ''' + SqlDatabase.TABLE_VOICE_ROLE + '''(
               id_voice      INTEGER  NOT NULL,
               id_role       INTEGER  NOT NULL,
               FOREIGN KEY (id_voice)     REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
               FOREIGN KEY (id_role)      REFERENCES ''' + SqlDatabase.TABLE_ROLE + ''' (id),
               PRIMARY KEY (id_voice, id_role)
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


    def append_user(self, cur, username, password, is_admin=False, user_id=None, language_code='en', descriptor_color='rgb(69,113,144)', show_original_title=True, show_lyrics_anyway=True, show_storyline_anyway=True, play_continuously=True, history_days=365):
        created_epoch = int(datetime.now().timestamp())
        id_language = self.language_name_id_dict[language_code]
        if user_id:
            cur.execute(
                'INSERT INTO ' + SqlDatabase.TABLE_USER + '''
                    (name, password, is_admin, id, created_epoch, id_language, descriptor_color, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously, history_days)
                VALUES
                    (:username, :password, :is_admin, :user_id, :created_epoch, :id_language, :show_original_title, :descriptor_color, :show_lyrics_anyway, :show_storyline_anyway, :play_continuously, :history_days)
                RETURNING id''',
                (username, password, is_admin, user_id, created_epoch, id_language, descriptor_color, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously, history_days))
        else:
            cur.execute(
                'INSERT INTO ' + SqlDatabase.TABLE_USER + '''
                    (name, password, is_admin, created_epoch, id_language, descriptor_color, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously, history_days)
                VALUES
                    (:username, :password, :is_admin, :created_epoch, :id_language, :descriptor_color, :show_original_title, :show_lyrics_anyway, :show_storyline_anyway, :play_continuously, :history_days)
                RETURNING id''',
                (username, password, is_admin, created_epoch, id_language, descriptor_color, show_original_title, show_lyrics_anyway, show_storyline_anyway, play_continuously, history_days))
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


    def append_card_media(self, card_path, title_orig, titles={}, title_on_thumbnail=1, title_show_sequence='', card_id=None, isappendix=0, show=1, download=0, category=None,  level=None, storylines={}, lyrics={}, decade=None, date=None, length=None, full_time=None, net_start_time=None, net_stop_time=None, sounds=[], subs=[], genres=[], themes=[], origins=[], writers=[], actors=[], stars=[], directors=[], voices=[], hosts=[], guests=[], interviewers=[], interviewees=[], presenters=[], lecturers=[], performers=[], reporters=[], media={}, basename=None, source_path=None, sequence=None, higher_card_id=None):

        # logging.error( "title_on_thumbnail: '{0}', title_show_sequence: '{1}'".format(title_on_thumbnail, title_show_sequence))

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            title_orig_id = self.language_name_id_dict[title_orig]
            category_id = self.category_name_id_dict[category]

            # Generate ID
            if card_id is None:
                hasher = hashlib.md5()
                hasher.update(card_path.encode('utf-8'))
                card_id = hasher.hexdigest()

            #
            # INSERT into CARD
            #
            # if the card has its own ID, meaning it is media card
            query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                    (id, level, show, download, isappendix, id_title_orig, title_on_thumbnail, title_show_sequence, id_category, decade, date, length, full_time, net_start_time, net_stop_time, basename, source_path, id_higher_card, sequence)
                    VALUES (:id, :level, :show, :download, :isappendix, :id_title_orig, :title_on_thumbnail, :title_show_sequence, :id_category, :decade, :date, :length, :full_time, :net_start_time, :net_stop_time, :basename, :source_path, :id_higher_card, :sequence)
                    RETURNING id;
            '''
            cur.execute(query, {'id': card_id, 'level': level, 'show': show, 'download': download, 'isappendix': isappendix, 'id_title_orig': title_orig_id, 'title_on_thumbnail': title_on_thumbnail, 'title_show_sequence': title_show_sequence, 'id_category': category_id, 'decade': decade, 'date': date, 'length': length, 'full_time': full_time, 'net_start_time': net_start_time, 'net_stop_time': net_stop_time, 'basename': basename, 'source_path': source_path, 'id_higher_card': higher_card_id, 'sequence': sequence})

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

        ###################################33

            #
            # INSERT into TABLE_CARD_VOICE
            #
            if isinstance(voices, list):
                tmp_voices = {}
                for key in voices:
                    tmp_voices[key] = ""
                voices = tmp_voices

            for voice, role in voices.items():
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

                    # Connects the Role to the Voice
                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_VOICE_ROLE + '''
                        (id_voice, id_role)
                        VALUES (:person_id, :role_id);'''
                    cur.execute(query, {'person_id': person_id, 'role_id': role_id})

                    # logging.error( "    card_id: '{0}'. person_id: {1}. Person: {2}. role_id: {3}. Role: {4}.".format(card_id, person_id, actor, role_id, role))
                    # logging.error( "    card_id: '{0}'. person_id: {1}. Person: {2}. Role: {3}.".format(card_id, person_id, actor, role))


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


    def append_hierarchy(self, card_path, title_orig, titles, title_on_thumbnail=1, title_show_sequence='', card_id=None, show=1, download=0, isappendix=0, date=None, decade=None, category=None, storylines={}, level=None, genres=None, themes=None, origins=None, basename=None, source_path=None, sequence=None, higher_card_id=None):

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            category_id = self.category_name_id_dict[category]
            title_orig_id = self.language_name_id_dict[title_orig]

            # Generate ID
            if card_id is None:
                hasher = hashlib.md5()
                hasher.update(card_path.encode('utf-8'))
                card_id = hasher.hexdigest()

            #
            # INSERT into Level
            #

            query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                (id, level, show, download, isappendix, id_title_orig, title_on_thumbnail, title_show_sequence, date, decade, id_category, basename, source_path, id_higher_card, sequence)
                VALUES (:id, :level, :show, :download, :isappendix, :id_title_orig, :title_on_thumbnail, :title_show_sequence, :date, :decade, :id_category, :basename, :source_path, :id_higher_card, :sequence)
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

    def update_play_position(self, card_id, recent_position, start_epoch=None):
        """
        Updates the player's position of a movie. This method is periodically called from the browser
        It returns with the start_epoch value if the UPDATE or INSERT was successful.
        If the start_epoch is given, it is an UPDATE, if it is not given, it is INSERT.
        If something went wrong, it returns with None
        card_id           Card ID
        recent_position   Player's recent position in seconds
        start_epoch       Timestamp when the play started. This method generates this value
        """

        with self.lock:
            result = False
            data = {}
            error_message = "Lock error"

            try:

                cur = self.conn.cursor()
                cur.execute("begin")

                # TODO
                # put this block after the connection to be handled well in the catch
                # But it is really stupid to start a coursor before I decide if the user is logged in or not
                # figure out how to make this code clean
                #

                user_data = session.get('logged_in_user')
                if user_data:
                    user_id = user_data["user_id"]
                else:
                    error_message = 'Not logged in'
                    raise sqlite3.Error(error_message)

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
                    error_message = "The requested user_id({0}) does NOT exist".format(user_id)
                    logging.error(error_message)
                    raise sqlite3.Error(error_message)

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
                    error_message = "The requested card_id({0}) does NOT exist".format(card_id)
                    logging.error(error_message)
                    raise sqlite3.Error(error_message)


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

                # New history - INSERT
                if history_number == 0 and not start_epoch:

                    start_epoch = int(datetime.now().timestamp())
                    recent_epoch = start_epoch
                    query = '''INSERT INTO ''' + SqlDatabase.TABLE_HISTORY + '''
                        (id_card, id_user, start_epoch, recent_epoch, recent_position)
                        VALUES (:card_id, :user_id, :start_epoch, :recent_epoch, :recent_position);
                    '''
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'start_epoch': start_epoch, 'recent_epoch': recent_epoch, 'recent_position': recent_position})
                    record = cur.fetchone()
                    logging.debug("The registered new history of card_id: {0} has 'start_epoch': {1}".format(card_id, start_epoch))

                # Update history
                elif history_number == 1 and start_epoch:

                    recent_epoch = int(datetime.now().timestamp())
                    query = '''
                        UPDATE ''' + SqlDatabase.TABLE_HISTORY + '''
                        SET recent_epoch = :recent_epoch, recent_position = :recent_position
                        WHERE
                            history.id_card=:card_id
                            AND history.id_user=:user_id
                            AND history.start_epoch=:start_epoch
                    '''
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'start_epoch': start_epoch, 'recent_epoch': recent_epoch, 'recent_position': recent_position})
                    record = cur.fetchone()

                # Something went wrong
                else:
                    error_message = "Something went wrong. The parameter 'start_epoch'={0} but the SELECT in History table returned with value={1}".format(start_epoch, history_number)
                    logging.error(error_message)
                    raise sqlite3.Error(error_message)

                result = True
                data['start_epoch'] = int(start_epoch)
                error_message = None

            except sqlite3.Error as e:
                error_message = str(e)
                logging.error(error_message)

            finally:
                cur.execute("commit")
                cur.close()
                return {"result": result, "data": data, "error": error_message}

        # If the lock failed
        return {"result": result, "data": data, "error": error_message}


    def get_logged_in_user_data(self):
        result = False
        data = {}
        error_message = "Lock error"

        username = None

        if has_request_context():

            user_data = session.get('logged_in_user', None)
            if user_data:
                username = user_data['username']
            else:
                error_message = 'Not logged in'
        else:
            error_message = 'No request context'

        if username is None:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:

            try:
                cur = self.conn.cursor()

                # Verify user existence
                query = '''
                    SELECT
                        user.is_admin as is_admin,
                        user.name as name,
                        lang.name as language_code,
                        user.show_original_title   as show_original_title,
                        user.show_lyrics_anyway    as show_lyrics_anyway,
                        user.show_storyline_anyway as show_storyline_anyway,
                        user.play_continuously     as play_continuously
                FROM
                    ''' + SqlDatabase.TABLE_USER + ''' user,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    user.name=:username
                    AND user.id_language=lang.id;
                '''
                query_parameters = {'username': username}
                record=cur.execute(query, query_parameters).fetchone()

                if record:
                    result = True
                    data = dict(record) if record else record
                    error_message = None
                else:
                    data = {}
                    error_message = "Not logged in"

            except sqlite3.Error as e:
                error_message = "The operation for user: '{0}' failed because of an error: {1}".format(username, e)
                logging.error(error_message)

            finally:
                cur.close()
                return {"result": result, "data": data, "error": error_message}

        # If the lock failed
        return {"result": result, "data": data, "error": error_message}

    #
    # Used only locally
    # Not used in any REST
    #
    def _get_user_data_with_password(self, username):
        data = {}

        with self.lock:

            try:
                cur = self.conn.cursor()

                # Verify user existence
                query = '''
                    SELECT
                        user.id                    as id,
                        user.password              as password,
                        user.is_admin              as is_admin,
                        user.name                  as name,
                        lang.name                  as language_code,
                        lang.id                    as language_id,
                        user.descriptor_color      as descriptor_color,
                        user.show_original_title   as show_original_title,
                        user.show_lyrics_anyway    as show_lyrics_anyway,
                        user.show_storyline_anyway as show_storyline_anyway,
                        user.play_continuously     as play_continuously
                FROM
                    ''' + SqlDatabase.TABLE_USER + ''' user,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    user.name = :username
                    AND user.id_language=lang.id;
                '''
                query_parameters = {'username': username}
                record=cur.execute(query, query_parameters).fetchone()

                data = dict(record) if record else {}

            finally:
                cur.close()
                return data

        # If the lock failed
        return data

    #
    # Used only locally
    # Not used in any REST
    #
    def _get_publishable_user_data(self, username=None):
        """
        Retrieves user profile data safe for client consumption (excludes sensitive information).

        This method fetches user preferences and settings from the database while
        filtering out sensitive data like password hashes. It provides fallback
        defaults for anonymous/guest users when no username is provided.

        Args:
            username (str, optional): Username to fetch data for.
                                      If None, returns default guest user configuration.

        Returns:
            dict: User profile data containing:
                - is_admin (bool): Administrative privileges flag
                - name (str): Username or None for guest users
                - language_code (str): User's preferred language code
                - descriptor_color (str): UI color theme preference
                - show_original_title (bool): Display original title preference
                - show_lyrics_anyway (bool): Always show lyrics preference
                - show_storyline_anyway (bool): Always show storyline preference
                - play_continuously (bool): Continuous playback preference

        Note:
            - Used internally by login and session management methods
            - Does NOT include sensitive data (password, user ID, etc.)
            - Returns empty dict if database error occurs
            - Provides guest defaults when username is None
        """
        data = {}

        # Return guest/anonymous user defaults when no username provided
        if username is None:
            data = {
                "is_admin": False,
                "name": None,
                "language_code": self.language,
                "descriptor_color": 'rgb(129, 60, 41)',
                "always_show_original_title": True,
                "show_lyrics_anyway": True,
                "show_storyline_anyway": True,
                "play_continuously": True
            }
            return data

        with self.lock:
            try:
                cur = self.conn.cursor()

                # Fetch user profile data excluding sensitive information
                query = '''
                    SELECT
                        user.is_admin              as is_admin,
                        user.name                  as name,
                        lang.name                  as language_code,
                        user.descriptor_color      as descriptor_color,
                        user.show_original_title   as show_original_title,
                        user.show_lyrics_anyway    as show_lyrics_anyway,
                        user.show_storyline_anyway as show_storyline_anyway,
                        user.play_continuously     as play_continuously
                FROM
                    ''' + SqlDatabase.TABLE_USER + ''' user,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    user.name = :username
                    AND user.id_language=lang.id;
                '''
                query_parameters = {'username': username}
                record=cur.execute(query, query_parameters).fetchone()

                # Convert SQLite Row to dictionary, return empty dict if user not found
                data = dict(record) if record else {}

            except sqlite3.Error as e:
                error_message = "The SELECTION in the database for user: '{0}' failed because of an error: {1}".format(username, e)
                logging.error(error_message)

            finally:
                cur.close()
                return data

        # If the lock failed
        return data


    def update_user_data(self, password=None, language_code=None, descriptor_color=None, show_original_title=None, show_lyrics_anyway=None, show_storyline_anyway=None, play_continuously=None, history_days=None):
        """
        Updates user profile data in the database with selective field updates.

        This method allows partial updates of user preferences and settings.
        Only non-None parameters will be updated in the database, allowing
        clients to update specific fields without affecting others.

        Args:
            password (str, optional): New password (will be hashed before storage)
            language_code (str, optional): Language preference code (e.g., 'en', 'hu')
            descriptor_color (str, optional): UI color theme preference
            show_original_title (bool, optional): Whether to show original titles
            show_lyrics_anyway (bool, optional): Whether to always show lyrics
            show_storyline_anyway (bool, optional): Whether to always show storylines
            play_continuously (bool, optional): Continuous playback preference
            history_days (int, optional): Number of days to keep history

        Returns:
            dict: {'result': bool, 'data': dict, 'error': str|None}
                  result: True if update successful
                  data: Empty dict (no data returned)
                  error: Error message if operation failed

        Side Effects:
            - Updates database User table
            - Synchronizes Flask session with updated data
            - Triggers locale reconfiguration if language changed
        """
        result = False
        data = {}
        error_message = "Lock error"

        # Extract username from current session
        user_data = session.get('logged_in_user', None)
        if user_data:
            username = user_data['username']

        # language can be set even the user is not looged in
        elif language_code:
            self.language = language_code
            self._set_locale()

            return {'result': True, 'data': data, 'error': 'Not logged in'}

        else:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:

            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Verify user exists in database
                query = '''
                    SELECT
                        COUNT(*) as user_number
                    FROM
                        ''' + SqlDatabase.TABLE_USER + ''' user
                    WHERE
                        user.name=:username;
                '''
                query_parameters = {'username': username}
                record=cur.execute(query, query_parameters).fetchone()
                (user_number, ) = record if record else (0,)

                if user_number == 0:
                    raise sqlite3.Error("The requested username({0}) does NOT exist".format(username))

                # Validate language code if provided
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
                        raise sqlite3.Error("The requested language_code({0}) does NOT exist".format(language_code))

                # Build dynamic UPDATE query based on provided parameters
                set_list = []
                if language_code:
                    set_list.append("'id_language' = :language_id")

                if password is not None:

                    # Hash password before storage for security
                    set_list.append("'password' = :password")
                    hashed_password = generate_password_hash(password)
                else:
                    hashed_password = ''

                if descriptor_color is not None:
                    set_list.append("'descriptor_color' = :descriptor_color")

                if show_original_title is not None:
                    set_list.append("'show_original_title' = :show_original_title")

                if show_lyrics_anyway is not None:
                    set_list.append("'show_lyrics_anyway' = :show_lyrics_anyway")

                if show_storyline_anyway is not None:
                    set_list.append("'show_storyline_anyway' = :show_storyline_anyway")

                if history_days is not None:
                    set_list.append("'history_days' = :history_days")

                # Execute the dynamic UPDATE query
                query = '''
                        UPDATE ''' + SqlDatabase.TABLE_USER + '''
                        SET
                            ''' + ", ".join(set_list) + '''
                        WHERE
                            user.name=:username
                    '''

                cur.execute(query, {'username': username, 'password': hashed_password, 'language_id': language_id, 'descriptor_color': descriptor_color, 'show_original_title': show_original_title, 'show_lyrics_anyway': show_lyrics_anyway, 'show_storyline_anyway': show_storyline_anyway, 'play_continuously': play_continuously, 'history_days': history_days})
                number_of_updated_rows = cur.rowcount

                # Verify exactly one row was updated
                if number_of_updated_rows == 1:
                    result = True
                    error_message = None
                else:
                    error_message = "User update failed"

            except sqlite3.Error as e:
                error_message = "The User update for user: '{0}' failed because of an error: {1}".format(username, e)
                logging.error(error_message)

            finally:
                cur.execute("commit")
                cur.close()

        # Synchronize session with updated database state if update succeeded
        if result:

            # Update Flask session with fresh database values
            self._update_session_with_db(username)

            return {"result": result, "data": data, "error": error_message}

        # If the lock failed
        return {"result": result, "data": data, "error": error_message}


    def _update_session_with_db(self, username):
        """
        Synchronizes the Flask session data with the current database state for a user.

        This method is called after user profile updates to ensure the session
        reflects the latest user preferences, particularly language settings that
        affect locale and UI behavior.

        Args:
            username (str): The username to fetch updated data for

        Side Effects:
            - Updates Flask session['logged_in_user'] with fresh database values
            - Triggers locale reconfiguration via _set_locale()
        """

        # Fetch the complete user data from database including password hash
        full_user_data = self._get_user_data_with_password(username)

        # Proceed only if user exists in database
        if full_user_data:

            # Extract password hash (not used here but validates user existence)
            stored_hashed_password = full_user_data.get('password', None)

            # Update session with fresh language preferences from database
            session['logged_in_user']['language_id'] = full_user_data['language_id']
            session['logged_in_user']['language_code'] = full_user_data['language_code']

            # Reconfigure system locale based on updated language preference
            # Not needed because after user data update, SESSION RESTORATION MODE will automatically exexuted doing _set_lacale() anyway
            # self._set_locale()


    def get_history(self, card_id=None, limit_days=None, limit_records=None):
        result = False
        data = []
        error_message = "Lock error"

        user_data = session.get('logged_in_user', None)
        if user_data:
            user_id = user_data['user_id']
        else:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:
            try:
                cur = self.conn.cursor()
                        # cur.execute("begin")

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
                records=cur.execute(query, query_parameters).fetchall()

                data = [{key: record[key] for key in record.keys()} for record in records]

                result = True
                #                data = dict(record) if record else record
                error_message = None

            except sqlite3.Error as e:
                error_message = "The operation for user: '{0}' failed because of an error: {1}".format(username, e)
                logging.error(error_message)

            finally:
                #                cur.execute("commit")
                cur.close()
                return {"result": result, "data": data, "error": error_message}

        # If there was a problem with the file lock
        return {"result": result, "data": data, "error": error_message}


    def update_rating(self, card_id, rate=None, skip_continuous_play=None):
        result = False
        data = {}
        error_message = "Lock error"

        user_data = session.get('logged_in_user', None)
        if user_data:
            user_id = user_data['user_id']
            username = user_data['username']
        else:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:

            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                #
                # Verify Rating existence
                #
                # User
                query = '''
                    SELECT
                        COUNT(*) as rating_number
                FROM
                    ''' + SqlDatabase.TABLE_RATING + ''' rating

                WHERE
                    id_user=:user_id
                    AND id_card=:card_id
                '''
                query_parameters = {'user_id': user_id, 'card_id': card_id}
                record=cur.execute(query, query_parameters).fetchone()
                (rating_number, ) = record if record else (0,)

                # there was no rating for this media by this user
                if rating_number == 0:
                    logging.debug("New rating record needed for card: {0} by user: {1}. RATE: {2}, SKIP: {3}".format(card_id, username, rate, skip_continuous_play))

                    insert_list = []
                    insert_list.append("id_card")
                    insert_list.append("id_user")
                    values_list = []
                    values_list.append(":card_id")
                    values_list.append(":user_id")

                    if rate is None:
                        rate = 0
                    if skip_continuous_play is None:
                        skip_continuous_play = 1

                    query = '''
                        INSERT INTO ''' + SqlDatabase.TABLE_RATING + '''
                             (id_card, id_user, rate, skip_continuous_play)
                        VALUES
                            (:card_id, :user_id, :rate, :skip_continuous_play)
                    '''
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'rate': rate, 'skip_continuous_play': skip_continuous_play})
                    record = cur.fetchone()

                # it was was already rated
                else:
                    logging.debug("Rating updates for card: {0} by user: {1}. RATE: {2}, SKIP: {3}".format(card_id, username, rate, skip_continuous_play))

                    set_list = []
                    set_list.append("'id_card' = :card_id")
                    set_list.append("'id_user' = :user_id")
                    if rate is not None:
                        set_list.append("'rate' = :rate")
                    if skip_continuous_play is not None:
                        set_list.append("'skip_continuous_play' = :skip_continuous_play")

                    query = '''
                        UPDATE ''' + SqlDatabase.TABLE_RATING + '''
                        SET
                            ''' + ", ".join(set_list) + '''
                        WHERE
                            id_user = :user_id
                            AND id_card = :card_id
                    '''
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'rate': rate, 'skip_continuous_play': skip_continuous_play})
                    record = cur.fetchone()

                cur.execute("commit")
                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Rating set for card: {0} by user: {1}. RATE: {2}, SKIP: {3} failed! {4}".format(card_id, username, rate, skip_continuous_play, e)
                logging.error(error_message)
                cur.execute("rollback")

            finally:
                cur.close()
                return {"result": result, "data": data, "error": error_message}

        # If there was a problem with the file lock
        return {"result": result, "data": data, "error": error_message}


    def insert_tag(self, card_id, name):
        result = False
        data = {}
        error_message = "Lock error"

        user_data = session.get('logged_in_user', None)
        if user_data:
            user_id = user_data['user_id']
            username = user_data['username']
        else:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:

            try:
                cur = self.conn.cursor()

                #
                # Verify Tag existence
                #
                # User
                query = '''
                    SELECT
                        COUNT(*) as tag_number
                FROM
                    ''' + SqlDatabase.TABLE_TAG + ''' tag

                WHERE
                    id_user=:user_id
                    AND id_card=:card_id
                    AND name=:name
                '''
                query_parameters = {'user_id': user_id, 'card_id': card_id, 'name': name}
                record=cur.execute(query, query_parameters).fetchone()
                (tag_number, ) = record if record else (0,)

                # there was no tag for this media by this user for this card
                if tag_number == 0:
                    logging.debug("Record '{2}' tag for card: {0} by user: {1}".format(card_id, username, name))

                    cur.execute("begin")

                    query = '''
                        INSERT INTO ''' + SqlDatabase.TABLE_TAG + '''
                             (id_card, id_user, name)
                        VALUES
                            (:card_id, :user_id, :name)
                    '''
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'name': name})
                    cur.execute("commit")
                    data["row_id"]=cur.lastrowid
                    data["id_card"]=card_id
                    data["username"]=username
                    data["name"]=name

                # tag already exist
                else:
                    error_message = "The tag already exist"
                    raise sqlite3.Error(error_message)

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Tagging the card: {0} by user: {1} with '{2}' tag failed!\n{3}".format(card_id, username, name, e)
                logging.error(error_message)
                cur.execute("rollback")

            finally:

                cur.close()
                return {"result": result, "data": data, "error": error_message}

        # If there was a problem with the file lock
        return {"result": result, "data": data, "error": error_message}


    def delete_tag(self, card_id, name):
        result = False
        data = {}
        error_message = "Lock error"

        user_data = session.get('logged_in_user', None)
        if user_data:
            user_id = user_data['user_id']
            username = user_data['username']
        else:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:

            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                #
                # Verify Tag existence
                #
                # User
                query = '''
                    SELECT
                        COUNT(*) as tag_number
                FROM
                    ''' + SqlDatabase.TABLE_TAG + ''' tag

                WHERE
                    id_user=:user_id
                    AND id_card=:card_id
                    AND name=:name
                '''
                query_parameters = {'user_id': user_id, 'card_id': card_id, 'name': name}
                record=cur.execute(query, query_parameters).fetchone()
                (tag_number, ) = record if record else (0,)

                # there is (one)s tag for this media by this user for this card
                if tag_number > 0:
                    logging.debug("Tag is about removed from card: {0} by user: {1}. Tag: '{2}'".format(card_id, username, name))

                    query = '''
                        DELETE FROM ''' + SqlDatabase.TABLE_TAG + '''
                        WHERE
                            id_card = :card_id
                            AND id_user = :user_id
                            AND name = :name
                    '''
                    cur.execute(query, {'card_id': card_id, 'user_id': user_id, 'name': name})
                    cur.execute("commit")

                    data["id_card"]=card_id
                    data["username"]=username
                    data["name"]=name

                # tag does not exist
                else:
                    error_message = "The tag does not exist"
                    raise sqlite3.Error(error_message)


                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Deleting the '{2}' tag from the card: {0} by user: {1} failed! {3}".format(card_id, username, name, e)
                logging.error(error_message)
                cur.execute("rollback")
            finally:
                cur.close()
                return {"result": result, "data": data, "error": error_message}

        # If there was a problem with the file lock
        return {"result": result, "data": data, "error": error_message}


    def get_tags(self, category="movie", view_state=None, tags=None, title=None, genres=None, themes=None, directors=None, actors=None, lecturers=None, performers=None, origins=None, decade=None, lang='en', limit=100, json=True):
        result = False
        error_message = "Lock error"

        user_data = session.get('logged_in_user', None)
        if user_data:
            user_id = user_data['user_id']
            username = user_data['username']
        else:
            user_id = -1

        records = []

        with self.lock:

            try:
                history_days = 365
                history_back = int(datetime.now().astimezone().timestamp()) - history_days * 86400

                query = self.get_raw_query_of_lowest_level(category=category, tags=tags, genres=genres, themes=themes, directors=directors, actors=actors, lecturers=lecturers, performers=performers, origins=origins)

                query = '''
                    SELECT Tag.name
                    FROM Tag
                    JOIN ({0}) raw_query ON raw_query.tags IS NOT NULL AND ',' || raw_query.tags || ',' LIKE '%,' || Tag.name || ',%'
                    GROUP BY Tag.name;
                '''.format(query)

                #print(query)

                cur = self.conn.cursor()
                cur.execute("begin")            #Otherwise "no transaction is active"

                level = None
                query_parameters = {'user_id': user_id, 'category': category, 'level': level, 'view_state': view_state, 'history_back': history_back, 'title': title, 'decade': decade, 'lang': lang, 'limit': limit}

                logging.debug("get_lowest_level_cards query: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                records = [{key: record[key] for key in record.keys()} for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching Tags by user: {0} failed! {1}".format(username, e)
                logging.error(error_message)

            finally:
                cur.close()
                return {"result": result, "data": records, "error": error_message}

        return {"result": result, "data": records, "error": error_message}

# ---

    def get_sql_where_condition_from_text_filter(self, text_filter, field_name, start_separator=',', end_separator=','):
        # the separator parameters needed because of some fields, like 'actors' and 'voices' have role, separated by :
        op = None
        if text_filter is None:
            filter_list = []
        elif '_AND_' in text_filter:
            op = 'and'
            filter_list = [] if text_filter is None else text_filter.split('_AND_')
        elif '_OR_' in text_filter:
            op = 'or'
            filter_list = [] if text_filter is None else text_filter.split('_OR_')
        else:
            op = ''
            filter_list = [text_filter]

        filter_in_list =     [] if text_filter == None else [filter for filter in filter_list if not filter.startswith("_NOT_")]
        filter_not_in_list = [] if text_filter == None else [filter.removeprefix("_NOT_") for filter in filter_list if filter.startswith("_NOT_")]

        filter_where =  None if text_filter == None else '(' + (' OR ' if op == 'or' else ' AND ').join([f"'{start_separator}' || " + field_name + " || ',' " + ("NOT " if filter.startswith("_NOT_") else "") + f"LIKE '%{start_separator}" + filter.removeprefix("_NOT_") + f"{end_separator}%'" for filter in filter_list]) + ')'

        # logging.debug("{} IN LIST: {}".format(field_name, filter_in_list))
        # logging.debug("{} NOT IN LIST: {}".format(field_name, filter_not_in_list))
        # logging.debug("{} WHERE: {}".format(field_name, filter_where if filter_where is not None else 'None'))

        return filter_where

    def get_sql_like_where_condition_from_text_filter(self, text_filter, field_name):

        op = None
        if text_filter is None:
            filter_list = []
        elif '_AND_' in text_filter:
            op = 'and'
            filter_list = [] if text_filter is None else text_filter.split('_AND_')
        elif '_OR_' in text_filter:
            op = 'or'
            filter_list = [] if text_filter is None else text_filter.split('_OR_')
        else:
            op = ''
            filter_list = [text_filter]

        filter_in_list =     [] if text_filter == None else [filter for filter in filter_list if not filter.startswith("_NOT_")]
        filter_not_in_list = [] if text_filter == None else [filter.removeprefix("_NOT_") for filter in filter_list if filter.startswith("_NOT_")]
        filter_where =       None if text_filter == None else '(' + (' OR ' if op == 'or' else ' AND ').join(["" + field_name + " " + ("NOT " if filter.startswith("_NOT_") else "") + "LIKE '" + filter.removeprefix("_NOT_") + "'" for filter in filter_list]) + ')'

        logging.debug("{} IN LIST: {}".format(field_name, filter_in_list))
        logging.debug("{} NOT IN LIST: {}".format(field_name, filter_not_in_list))
        logging.debug("{} WHERE: {}".format(field_name, filter_where if filter_where is not None else 'None'))

        return filter_where

    def get_sql_rate_query(self, value):
        return f"rate>={str(value)}" if value else ""

    def get_converted_query_to_json(self, sql_record_list, lang):
        """
        Convert and translate the given SQL card-response
        """

        # TODO: error handling needed !!! media file name with spaces and strange characters causing error, consequently no converting, and fail later where json is expected

        records = [{key: record[key] for key in record.keys()} for record in sql_record_list]

        #if sort:
        #    records = sorted(records, key=lambda arg: locale.strxfrm((arg['title_req'] or arg['title_orig'] or '').lower()))
        #records = sorted([{key: record[key] for key in record.keys()} for record in sql_record_list], key=lambda arg: locale.strxfrm((arg['title_req'] or arg['title_orig'] or '').lower()))

        trans = Translator.getInstance(lang)
        for record in records:

            category = record["category"]

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

            # Recent State (history)
            recent_state_string = record["recent_state"]
            recent_state_dict = {'recent_position':0, 'play_count':0}
            if recent_state_string and record["medium"]:
                var_list = recent_state_string.split(";")
                for var_pair in var_list:
                    (key, value) = var_pair.split("=")
                    recent_state_dict[key] = value
            record["recent_state"] = recent_state_dict

            # Rate
            record["rate"] = record["rate"] if record["rate"] else 0
            record["skip_continuous_play"] = True if record["skip_continuous_play"] else False

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
            actors_play_string = record["actors"]
            actors_list = []
            if actors_play_string:
                actors_play_list = actors_play_string.split(';')
                for actor_string in actors_play_list:
                    (actor, characters_string) = actor_string.split(':')
                    characters = []
                    if characters_string:
                        character_list = characters_string.split(',')
                        for character in character_list:
                            characters.append(character)
                    actors_list.append({actor: characters})
            record["actors"] = actors_list

            # Voices
            voices_play_string = record["voices"]
            voices_list = []
            if voices_play_string:
                voices_play_list = voices_play_string.split(';')
                for voice_string in voices_play_list:
                    (voice, characters_string) = voice_string.split(':')
                    characters = []
                    if characters_string:
                        character_list = characters_string.split(',')
                        for character in character_list:
                            characters.append(character)
                    voices_list.append({voice: characters})
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

            # Tags
            tags_string = record["tags"]
            tags_list = []
            if tags_string:
                tags_list = tags_string.split(',')
            record["tags"] = tags_list
        logging.debug("Converted records: '{0}'".format(records))

        return records

    def login(self, username=None, password=None):
        """
        Handles user authentication with support for both credential-based login
        and session restoration.

        This method supports two login modes:
        1. Credential-based: Validates username/password against database
        2. Session restoration: Restores existing session without credentials

        Args:
            username (str, optional): Username for authentication
            password (str, optional): Plain text password for authentication

        Returns:
            dict: {'result': bool, 'data': dict, 'error': str|None}
                  result: True if login successful
                  data: User profile data (without sensitive information)
                  error: Error message if login failed

        Side Effects:
            - Creates or restores Flask session
            - Sets session as permanent
            - Configures system locale based on user language
            - Clears any existing session before new login
        """

        # Initialize response structure with failure defaults
        error = 'Login failed'
        result = False
        data = {}

        # SESSION RESTORATION MODE: No credentials provided
        # Used by client to restore existing session on page load
        if (username is None and password is None) or (not username and not password):

            if session.get('logged_in_user'):

                # Extract username from existing session
                if 'logged_in_user' in session and 'username' in session['logged_in_user']:

                    username = session['logged_in_user']['username']

                    # Fetch current user data from database
                    data = self._get_publishable_user_data(username)
                    result = True
                    error = None

                    # Apply user's language preference to system locale
                    self._set_locale()

                else:

                    # Fetch NON-user data from database
                    data = self._get_publishable_user_data()
                    result = True
                    error = "Not loggged in"

                    # Apply user's language preference to system locale
                    self._set_locale()

            # user is not logged in
            else:

                # Fetch NON-user data from database
                data = self._get_publishable_user_data()
                result = True
                error = "Not loggged in"

                # Apply user's language preference to system locale
                self._set_locale()


            return {'result': result, 'data':data, 'error': error}

        # CREDENTIAL-BASED LOGIN MODE: Username and password provided

        # Clear any existing session before attempting new login
        self.logout()

        # Note: This hash is not used for comparison (legacy code)
        hashed_password = generate_password_hash(password)

        # Fetch complete user data including stored password hash
        full_user_data = self._get_user_data_with_password(username)

        # Proceed with authentication if user exists in database
        if full_user_data:
            stored_hashed_password = full_user_data.get('password', None)

            # Verify provided password against stored hash
            if check_password_hash(stored_hashed_password, password):

                # Get user data without sensitive information (e.g., password)
                publishable_user_data = self._get_publishable_user_data(username)

                if publishable_user_data:
                    result = True
                    data = publishable_user_data
                    error = None

                    # Make session persistent across browser restarts
                    session.permanent = True

                    # Store essential user information in Flask session
                    session['logged_in_user'] = {
                        'username': username,
                        'user_id': full_user_data['id'],
                        'language_id': full_user_data['language_id'],
                        'language_code': full_user_data['language_code']
                    }

                    # Apply user's language preference to system locale
                    # Not needed because after login, SESSION RESTORATION MODE will automatically exexuted doing _set_lacale() anyway
                    # self._set_locale()

        return {'result': result, 'data':data, 'error': error}

    def logout(self):

        # remove the session
        session.pop('logged_in_user', None)
        return {'result': True, 'data':{}, 'error': None}

    def get_user_id_and_lang(self):

        user_data = None
        if has_request_context():
            user_data = session.get('logged_in_user', None)

        if user_data:
            user_id = user_data['user_id']
            lang = user_data['language_code']
        else:
            user_id = -1
            lang = self.language

        return user_id, lang




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

    def get_list_of_actors(self, category, limit=15, json=True):
        """
        Gives back actor name's list, ordered by the number of the movies they played in
        limited by the given value
        """

        result = False
        error_message = "Lock error"

        records = {}
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    SELECT DISTINCT
                       person.name as actor_name
                    FROM
                       Card card,
                       Card_Actor card_actor,
                       Person person,
                       Category category
                    WHERE
                       ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''
                       AND category.name = :category
                       AND card.id_category = category.id
                       AND card_actor.id_actor = person.id
                       AND card_actor.id_card = card.id
                    ORDER BY person.name
                    LIMIT :limit;
                '''

                query_parameters = {'category': category, 'limit': limit}

                logging.debug("get_list_of_actors: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = [record['actor_name'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the actor list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

    def get_list_of_actors_by_role_count(self, category, minimum=3, limit=15, json=True):
        """
        Gives back actor name's list, ordered by the number of the movies they played in
        limited by the given value
        """

        result = False
        error_message = "Lock error"

        records = {}
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    WITH RECURSIVE
                        rec(actor_name, id, id_higher_card) AS (
                            SELECT
                                person.name AS actor_name,
                                card.id,
                                card.id_higher_card
                            FROM
                                Card card,
                                Card_Actor card_actor,
                                Person person,
                                Category category
                            WHERE
                                ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''
                                AND category.name = :category
                                AND card.id_category = category.id
                                AND card_actor.id_actor = person.id
                                AND card_actor.id_card = card.id

                            UNION ALL

                            SELECT
                                rec.actor_name,
                                card.id,
                                card.id_higher_card
                            FROM
                                rec,
                                Card card
                            WHERE
                                rec.id_higher_card = card.id
                        )
                    SELECT
                        actor_name,
                        COUNT(DISTINCT rec.id) AS movie_count
                    FROM
                        rec
                    WHERE
                        rec.id_higher_card IS NULL
                    GROUP BY
                        actor_name
                    HAVING
                        movie_count >= :minimum
                    ORDER BY
                        movie_count DESC,
                        actor_name
                    LIMIT :limit;
                '''

                query_parameters = {'category': category, 'minimum': minimum, 'limit': limit}

                logging.debug("get_list_of_actors_by_role_count: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    #records = [{key: record[key] for key in record.keys()} for record in records]
                    records = [record['actor_name'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the actor list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

    def get_list_of_voices(self, category, limit=15, json=True):
        """
        Gives back voice name's list, ordered by the number of the movies they played in
        limited by the given value
        """

        result = False
        error_message = "Lock error"

        records = {}
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    SELECT DISTINCT
                       person.name as voice_name
                    FROM
                       Card card,
                       Card_Voice card_voice,
                       Person person,
                       Category category
                    WHERE
                       ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''
                       AND category.name = :category
                       AND card.id_category = category.id
                       AND card_voice.id_voice = person.id
                       AND card_voice.id_card = card.id
                    ORDER BY person.name
                    LIMIT :limit;
                '''

                query_parameters = {'category': category, 'limit': limit}

                logging.debug("get_list_of_voices: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = [record['voice_name'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the voice list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

    def get_list_of_voices_by_role_count(self, category, minimum=3, limit=15, json=True):
        """
        Gives back voice name's list, ordered by the number of the movies they played in
        limited by the given value
        """

        result = False
        error_message = "Lock error"

        records = {}
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    WITH RECURSIVE
                        rec(voice_name, id, id_higher_card) AS (
                            SELECT
                                person.name AS voice_name,
                                card.id,
                                card.id_higher_card
                            FROM
                                Card card,
                                Card_Voice card_voice,
                                Person person,
                                Category category
                            WHERE
                                ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''
                                AND category.name = :category
                                AND card.id_category = category.id
                                AND card_voice.id_voice = person.id
                                AND card_voice.id_card = card.id

                            UNION ALL

                            SELECT
                                rec.voice_name,
                                card.id,
                                card.id_higher_card
                            FROM
                                rec,
                                Card card
                            WHERE
                                rec.id_higher_card = card.id
                        )
                    SELECT
                        voice_name,
                        COUNT(DISTINCT rec.id) AS movie_count
                    FROM
                        rec
                    WHERE
                        rec.id_higher_card IS NULL
                    GROUP BY
                        voice_name
                    HAVING
                        movie_count >= :minimum
                    ORDER BY
                        movie_count DESC,
                        voice_name
                    LIMIT :limit;
                '''

                query_parameters = {'category': category, 'minimum': minimum, 'limit': limit}

                logging.debug("get_list_of_voices_by_role_count: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = [record['voice_name'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the voice list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

    def get_list_of_directors(self, category, limit=15, json=True):
        """
        Gives back director name's list, ordered by the name
        """

        result = False
        error_message = "Lock error"

        records = {}
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    SELECT DISTINCT
                       person.name as director_name
                    FROM
                       Card card,
                       Card_Director card_director,
                       Person person,
                       Category category
                    WHERE
                       ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''
                       AND category.name = :category
                       AND card.id_category = category.id
                       AND card_director.id_director = person.id
                       AND card_director.id_card = card.id
                    ORDER BY person.name
                    LIMIT :limit;
                '''

                query_parameters = {'category': category, 'limit': limit}

                logging.debug("get_list_of_directors: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = [record['director_name'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the director list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

    def get_list_of_directors_by_movie_count(self, category, minimum=3, limit=15, json=True):
        """
        Returns a list of director names, ordered by the number of movies they have directed, limited to the specified maximum count
        """

        result = False
        error_message = "Lock error"

        records = {}
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    WITH RECURSIVE
                        rec(director_name, id, id_higher_card) AS (
                            SELECT
                                person.name AS director_name,
                                card.id,
                                card.id_higher_card
                            FROM
                                Card card,
                                Card_Director card_director,
                                Person person,
                                Category category
                            WHERE
                                ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''
                                AND category.name = :category
                                AND card.id_category = category.id
                                AND card_director.id_director = person.id
                                AND card_director.id_card = card.id

                            UNION ALL

                            SELECT
                                rec.director_name,
                                card.id,
                                card.id_higher_card
                            FROM
                                rec,
                                Card card
                            WHERE
                                rec.id_higher_card = card.id
                        )
                    SELECT
                        director_name,
                        COUNT(DISTINCT rec.id) AS movie_count
                    FROM
                        rec
                    WHERE
                        rec.id_higher_card IS NULL
                    GROUP BY
                        director_name
                    HAVING
                        movie_count >= :minimum
                    ORDER BY
                        movie_count DESC,
                        director_name
                    LIMIT :limit;
                '''

                query_parameters = {'category': category, 'minimum': minimum, 'limit': limit}

                logging.debug("get_list_of_directors_by_movie_count: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    #records = [{key: record[key] for key in record.keys()} for record in records]
                    records = [record['director_name'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the director list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

    def get_list_of_writers(self, category, limit=15, json=True):
        """
        Gives back writers name's list, ordered by the name
        """

        result = False
        error_message = "Lock error"

        records = {}
        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    SELECT DISTINCT
                       person.name as writer_name
                    FROM
                       Card card,
                       Card_Writer card_writer,
                       Person person,
                       Category category
                    WHERE
                       ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''
                       AND category.name = :category
                       AND card.id_category = category.id
                       AND card_writer.id_writer = person.id
                       AND card_writer.id_card = card.id
                    ORDER BY person.name
                    LIMIT :limit;
                '''

                query_parameters = {'category': category, 'limit': limit}

                logging.debug("get_list_of_writers: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = [record['writer_name'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the writer list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

    def get_list_of_tags(self, category, limit=15, json=True):
        """
        Gives back tags for the given category for the user, ordered by the name
        """

        result = False
        error_message = "Lock error"

        records = {}
        user_data = session.get('logged_in_user', None)
        if user_data:
            user_id = user_data['user_id']
        else:
            user_id = -1

        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                # Get Card list
                query = '''
                    SELECT DISTINCT tag.name as tag
                    FROM Tag, Card, Category
                    WHERE
                        tag.id_card=card.id
                        AND category.id=card.id_category
                        AND category.name=:category
                        AND tag.id_user=:user_id
                    ORDER BY tag;
                '''

                query_parameters = {'user_id': user_id, 'category': category, 'limit': limit}

                logging.debug("get_list_of_tags: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = [record['tag'] for record in records]

                result = True
                error_message = None

            except sqlite3.Error as e:
                error_message = "Fetching the tag list failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()

        return {"result": result, "data": records, "error": error_message}

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




    #
    # GET /collect/highest/mixed
    #
    # ✅
    #
    def get_highest_level_cards(self, category, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
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
          - voices
          - writers
          - directors
          - lecturers
          - origins
        """
        records = {}
        user_id, lang = self.get_user_id_and_lang()

        with self.lock:

            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                query = self.get_raw_query_of_highest_level(category=category, tags=tags, title=title, genres=genres, themes=themes, directors=directors, writers=writers, actors=actors, voices=voices, lecturers=lecturers, performers=performers, origins=origins, rate_value=rate_value)

                query_parameters = {'user_id': user_id, 'level': level, 'filter_on': filter_on, 'category': category, 'title': title, 'decade': decade, 'tags': tags, 'lang': lang, 'limit': limit}

                logging.debug("get_highest_level_cards query: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = self.get_converted_query_to_json(records, lang)

            except sqlite3.Error as e:
                error_message = "Fetching the highest level card failed: {0}".format(e)
                logging.error(f'Error in the request process: {error_message}')

            finally:
                cur.close()

                return records
        return records

# ---

    #
    # /collect/next/mixed/
    #
    # ✅
    #
    def get_next_level_cards(self, card_id, category, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
        """
        FULL QUERY for the children cards of the given card
        Returns the next child cards which could be:
          - media card
          - level cards

        Parameters for filtering:
          - category
          - decade
          - language
          - rate

          logical operands (_AND_, _NOT_) in
          - genres
          - themes
          - actors
          - voices
          - directors
          - lecturers
          - origins
          - tags
        """

        records = {}
        user_id, lang = self.get_user_id_and_lang()

        with self.lock:

            try:

                where = ''

                cur = self.conn.cursor()
                cur.execute("begin")

                query = self.get_raw_query_of_next_level(category=category, tags=tags, level=level, filter_on=filter_on, genres=genres, themes=themes, directors=directors, actors=actors, voices=voices, lecturers=lecturers, performers=performers, origins=origins, rate_value=rate_value)

                query_parameters = {'user_id': user_id, 'card_id': card_id, 'category': category, 'level': level, 'filter_on': filter_on, 'title': title, 'decade': decade, 'lang': lang, 'limit': limit}

                logging.debug("get_next_level_cards query: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = self.get_converted_query_to_json(records, lang)

            except sqlite3.Error as e:
                error_message = "Fetching the next level card failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()
                return records
        return records

# ---

    #
    # GET /collect/lowest
    #
    # ✅
    #
    def get_lowest_level_cards(self, category, view_state=None, tags=None, level=None, title=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):

        """
        FULL QUERY for lowest (medium) level list
        Returns only medium level cards level cards
        With filters category/genre/theme/origin/director/actor

        Parameters for view_state:
          - *
          - interrupted
          - last_watched
          - least_watched
          - most_watched

        Parameters for filtering:
          - category
          - level
          - decade
          - language
          - rate

          logical operands (_AND_, _NOT_) in
          - genres
          - themes
          - actors
          - voices
          - directors
          - lecturers
          - origins
          - tags
        """

        records = {}
        user_id, lang = self.get_user_id_and_lang()

        with self.lock:

            try:

                cur = self.conn.cursor()
                cur.execute("begin")

                history_days = 365
                history_back = int(datetime.now().astimezone().timestamp()) - history_days * 86400

                query = self.get_raw_query_of_lowest_level(category=category, tags=tags, genres=genres, themes=themes, directors=directors, actors=actors, voices=voices, lecturers=lecturers, performers=performers, origins=origins, rate_value=rate_value)

                query = '''
                SELECT *
                FROM ({0}) raw_query
                WHERE
                    CASE
                        WHEN :view_state = 'interrupted' THEN
                            raw_query.start_epoch >= :history_back
                            AND raw_query.recent_position < raw_query.net_stop_time
                            AND raw_query.recent_position > raw_query.net_start_time
                        WHEN :view_state = 'last_watched' THEN
                            raw_query.start_epoch >= :history_back
                        WHEN :view_state = 'most_watched' THEN
                            raw_query.start_epoch >= :history_back
                        ELSE 1
                    END
                '''.format(query) + ( 'ORDER BY raw_query.start_epoch DESC' if view_state == 'interrupted' or view_state == 'last_watched' else 'ORDER BY raw_query.play_count DESC' if view_state == 'most_watched' else 'ORDER BY raw_query.ord' ) + '''
                LIMIT :limit;
                '''

                query_parameters = {'user_id': user_id, 'category': category, 'level': level, 'view_state': view_state, 'history_back': history_back, 'title': title, 'decade': decade, 'lang': lang, 'limit': limit}

                logging.debug("get_lowest_level_cards query: '{0}' / {1}".format(query, query_parameters))

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = self.get_converted_query_to_json(records, lang)

            except sqlite3.Error as e:
                error_message = "Fetching the lowest level card failed: {0}".format(e)
                logging.error(error_message)

            finally:
                cur.close()
                return records
        return records

# ---

    #
    # GET /collect/highest/mixed/abc
    #
    # ✅
    #
    def get_highest_level_abc(self, category, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=1000, json=True):

        records = []
        user_id, lang = self.get_user_id_and_lang()

        result = False
        error_message = "Lock error"

        with self.lock:

            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                query = self.get_raw_query_of_highest_level_abc(category=category, tags=tags, title=title, genres=genres, themes=themes, directors=directors, writers=writers, actors=actors, voices=voices, lecturers=lecturers, performers=performers, origins=origins, rate_value=rate_value)

                query_parameters = {'user_id': user_id, 'level': level, 'filter_on': filter_on, 'category': category, 'title': title, 'decade': decade, 'tags': tags, 'lang': lang, 'limit': limit}

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                records = sorted([dict(record) for record in records], key=lambda arg: locale.strxfrm(arg['name']))
                #records = [{key: record[key] for key in record.keys()} for record in records]
                #records = sorted(records, key=lambda arg: locale.strxfrm(arg['name']))

            except sqlite3.Error as e:
                error_message = "Fetching the highest level card failed: {0}".format(e)
                logging.error(f'Error in the request process: {error_message}')
                error_message = e

            finally:
                cur.close()

                result = True
                error_message = None
                return {"result": result, "data": records, "error": error_message}

        return {"result": result, "data": records, "error": error_message}


# ---

    #
    # GET /collect/abc
    #
    # ✅
    #
    def get_abc(self, lang):
        """
        Returns the list of the static ABC
        """
        result = True
        error_message = None

        trans = Translator.getInstance(lang)
        alphabet_string = trans.get_alphabet(case="upper")
        alphabet_list = list(alphabet_string)
        records = [{'name': letter, 'filter': letter + '%'} for letter in alphabet_list]
        records.insert(0, {"filter": "0%_OR_1%_OR_2%_OR_3%_OR_4%_OR_5%_OR_6%_OR_7%_OR_8%_OR_9%", "name": "0-9"})

        return {"result": result, "data": records, "error": error_message}





# RAW Queries

    def get_raw_query_of_highest_level(self, category, tags=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None):
        tags_where = self.get_sql_where_condition_from_text_filter(tags, 'tags')
        genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
        themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
        actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors', start_separator=';', end_separator=':')
        voices_where = self.get_sql_where_condition_from_text_filter(voices, 'voices', start_separator=';', end_separator=':')
        writers_where = self.get_sql_where_condition_from_text_filter(writers, 'writers')
        directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
        lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
        performers_where = self.get_sql_where_condition_from_text_filter(performers, 'performers')
        origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')
        titles_req_where = self.get_sql_like_where_condition_from_text_filter(title, 'ttitle_req')
        titles_orig_where = self.get_sql_like_where_condition_from_text_filter(title, 'ttitle_orig')
        rate_where = self.get_sql_rate_query(rate_value)

        logging.debug(f"rate_where: {rate_where}")

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
                mixed_id_list.full_time,
                mixed_id_list.net_start_time,
                mixed_id_list.net_stop_time,

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

                mixed_id_list.tags,
                mixed_id_list.rate,
                mixed_id_list.skip_continuous_play,


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
                appendix,

                hstr.recent_state
            FROM

                ---------------------------
                --- mixed level id list ---
                ---------------------------
                (
                WITH RECURSIVE
                    rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play,sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, ttitle_req, llang_req, ttitle_orig, llang_orig) AS

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
                            card.full_time,
                            card.net_start_time,
                            card.net_stop_time,

                            themes,
                            genres,
                            origins,
                            directors,
                            actors,
                            lecturers,

                            tags,
                            rate,
                            skip_continuous_play,

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
                            performers,

                            ttitle_req,
                            llang_req,
                            ttitle_orig,
                            llang_orig

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
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as actors,
                                    card_actor.id_card id_card
                                FROM
                                    Person person,
                                    Card_Actor card_actor,
                                    (
                                        SELECT
                                            actor_role.id_actor,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            actor_role
                                        WHERE
                                            actor_role.id_role = role.id
                                        GROUP BY
                                            actor_role.id_actor, role.id_card
                                    ) roles
                                WHERE
                                    card_actor.id_actor = person.id
                                    AND roles.id_actor = person.id
                                    AND roles.id_card = card_actor.id_card
                                GROUP BY
                                    card_actor.id_card
                            ) act
                            ON act.id_card=card.id

                            --------------
                            --- VOICES ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as voices,
                                    card_voice.id_card id_card
                                FROM
                                    Person person,
                                    Card_Voice card_voice,
                                    (
                                        SELECT
                                            voice_role.id_voice,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            voice_role
                                        WHERE
                                            voice_role.id_role = role.id
                                        GROUP BY
                                            voice_role.id_voice, role.id_card
                                    ) roles
                                WHERE
                                    card_voice.id_voice = person.id
                                    AND roles.id_voice = person.id
                                    AND roles.id_card = card_voice.id_card
                                GROUP BY
                                    card_voice.id_card
                            ) vc
                            ON vc.id_card=card.id

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

                            ---------------
                            --- TAGGING ---
                            ---------------
                            LEFT JOIN
                            (
                               SELECT
                                  group_concat(name) tags,
                                  id_card
                               FROM
                                  Tag tag
                               WHERE
                                  id_user=:user_id
                               GROUP BY id_card
                            ) tggng
                            ON tggng.id_card=card.id

                            --------------
                            --- RATING ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT id_card, rate, skip_continuous_play
                                FROM Rating
                                WHERE id_user=:user_id
                            )rtng
                            ON rtng.id_card=card.id

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

                            --------------------------------------------
                            ---         TITLE REQUESTED              ---
                            --- On the requested language, if exists ---
                            --------------------------------------------
                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_req, lang.name llang_req, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name = :lang
                            ) ttlrq
                            ON ttlrq.id_card=card.id

                            ----------------------------------------
                            ---           TITLE ORIG             ---
                            --- Orig if other lang was requested ---
                            ----------------------------------------

                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_orig, lang.name llang_orig, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name <> :lang
                            ) ttlor
                            ON ttlor.id_card=card.id AND ttlor.lang_id=card.id_title_orig

                        ------------------------
                        --- INITIAL WHERE    ---
                        --- the lowest level ---
                        ------------------------

                        WHERE
                            -- card can not be appendix --
                            card.isappendix == 0

                            -- connect card to category --
                            AND category.id=card.id_category

                            -- Find the lowest level --
                            -- AND card.level IS NULL

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

                            ''' + (
                                '''
                                AND CASE
                                    WHEN ttitle_req IS NOT NULL THEN ''' + titles_req_where + '''
                                    ELSE ''' + titles_orig_where + '''
                                END
                                ''' if titles_orig_where else ''' '''
                            ) + '''

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
                            --- WHERE WRITERS - conditional ---
                            AND ''' + writers_where if writers_where else '') + '''

                            ''' + ('''
                            --- WHERE ACTORS - conditional ---
                            AND ''' + actors_where if actors_where else '') + '''

                            ''' + ('''
                            --- WHERE VOICES - conditional ---
                            AND ''' + voices_where if voices_where else '') + '''

                            ''' + ('''
                            --- WHERE ORIGINS - conditional ---
                            AND ''' + origins_where if origins_where else '') + '''

                            ''' + ('''
                            --- WHERE PERFORMERS - conditional ---
                            AND ''' + performers_where if performers_where else '') + '''

                            ''' + ('''
                            --- WHERE LECTURERS - conditional ---
                            AND ''' + lecturers_where if lecturers_where else '') + '''

                            ''' + ('''
                            --- WHERE TAGS - conditional ---
                            AND ''' + tags_where if tags_where else '') + '''

                            ''' + ('''
                            --- WHERE RATE - conditional ---
                            AND ''' + rate_where if rate_where else '') + '''

                            AND CASE

                                -- level: ^ (*, None), filter: v (*, None) => show the HIGHEST level and filter on the LOWEST level on any type => filter LOWEST level
                                -- Genre: Standalone Scifi
                                WHEN (:level IS NULL OR :level = '^') AND (:filter_on IS NULL OR :filter_on = 'v') THEN ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''

                                -- level: ^ (*, None), filter: ^ (-) => show the HIGHEST level and filter on the same (HIGHEST) level on any type => filter HIGHEST level
                                -- Title: Standalone or Series
                                WHEN (:level IS NULL OR :level = '^') AND :filter_on IS not NULL AND :filter_on = '-' THEN card.id_higher_card IS NULL

                                -- level: <level>, filter: v (* None) => show the GIVEN level and filter on the LOWEST level on any type => filter LOWEST level
                                WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND (:filter_on IS NULL OR :filter_on = 'v') THEN ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + ''' AND card.id_higher_card IS not NULL

                                -- level: <level>, filter: - => show the GIVEN level and filter on the same (GIVEN) level on any type => filter GIVEN level
                                WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND :filter_on IS not NULL AND :filter_on = '-' THEN card.level = :level

                                ELSE 0

                            END

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
                            NULL full_time,
                            NULL net_start_time,
                            NULL net_stop_time,

                            NULL themes,
                            NULL genres,
                            NULL origins,
                            NULL directors,
                            NULL actors,
                            NULL lecturers,

                            NULL tags,
                            NULL rate,
                            NULL skip_continuous_play,

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
                            NULL performers,

                            NULL ttitle_req,
                            NULL llang_req,
                            NULL ttitle_orig,
                            NULL llang_orig

                        FROM
                            rec,
                            Card card,
                            Category category
                        WHERE
                            rec.id_higher_card=card.id
                            AND category.id=card.id_category
                    )
                SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers

                FROM
                    rec
                WHERE

                    -------------------
                    -------------------
                    --- Conditional ---
                    ---   filter    ---
                    -------------------
                    -------------------

                    CASE
                        -- level: ^ (*, None), filter: v (*, None) => show the HIGHEST level and filter on the LOWEST level on any type => show HIGHEST level
                        WHEN (:level IS NULL OR :level = '^') AND (:filter_on IS NULL OR :filter_on = 'v') THEN id_higher_card IS NULL

                        -- level: ^ (*, None), filter: - => show the HIGHEST level and filter on the same (HIGHEST) level on any type => show HIGHEST level
                        WHEN (:level IS NULL OR :level = '^') AND :filter_on IS not NULL AND :filter_on = '-' THEN id_higher_card IS NULL

                        -- level: <level>, filter: v (* None) => show the GIVEN level and filter on the LOWEST level on any type => GIVEN level
                        WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND (:filter_on IS NULL OR :filter_on = 'v') THEN level = :level

                        -- level: <level>, filter: - => show the GIVEN level and filter on the same (GIVEN) level on any type => GIVEN level
                        WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND :filter_on IS not NULL AND :filter_on = '-' THEN level = :level

                        ELSE 0
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

                ---------------
                --- HISTORY ---
                ---------------
                LEFT JOIN
                (
                    SELECT
                        ('start_epoch=' || start_epoch || ';recent_epoch=' || recent_epoch || ';recent_position=' || recent_position || ';play_count=' || count(*) ) recent_state,
                        id_card
                    FROM (
                        SELECT id_card, start_epoch, recent_epoch, recent_position
                        FROM History
                        WHERE id_user=:user_id
                        ORDER BY start_epoch DESC
                    )
                    GROUP BY id_card
                )hstr
                ON hstr.id_card=core.id

            WHERE

                mixed_id_list.id=core.id

            ORDER BY CASE
                WHEN sequence IS NULL AND title_req IS NOT NULL THEN LOWER(title_req)
                WHEN sequence IS NULL AND title_orig IS NOT NULL THEN LOWER(title_orig)
                WHEN sequence<0 THEN LOWER(basename)
                WHEN sequence>=0 THEN sequence
            END
            LIMIT :limit; '''

        return query

    def get_raw_query_of_next_level(self, category, tags=None, level=None, filter_on=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None):

        tags_where = self.get_sql_where_condition_from_text_filter(tags, 'tags')
        genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
        themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
        actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors', start_separator=';', end_separator=':')
        voices_where = self.get_sql_where_condition_from_text_filter(voices, 'voices', start_separator=';', end_separator=':')
        directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
        lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
        performers_where = self.get_sql_where_condition_from_text_filter(performers, 'performers')
        origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')

        rate_where = self.get_sql_rate_query(rate_value)

        logging.debug(f"rate_where: {rate_where}")

        lowest_level_where= '''
                           --- WHERE TITLE ---
                            AND CASE
                                WHEN :title IS NOT NULL AND ttitle_req IS NOT NULL THEN ttitle_req LIKE :title
                                WHEN :title IS NOT NULL THEN ttitle_orig LIKE :title
                                ELSE 1
                            END
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
                            --- WHERE VOICES - conditional ---
                            AND ''' + voices_where if voices_where else '') + '''
                            ''' + ('''
                            --- WHERE ORIGINS - conditional ---
                            AND ''' + origins_where if origins_where else '') + '''
                            ''' + ('''
                            --- WHERE LECTURERS - conditional ---
                            AND ''' + lecturers_where if lecturers_where else '') + '''
                            ''' + ('''
                            --- WHERE PERFORMERS - conditional ---
                            AND ''' + performers_where if performers_where else '') + '''
                            ''' + ('''
                            --- WHERE TAGS - conditional ---
                            AND ''' + tags_where if tags_where else '') + '''
                            ''' + ('''
                            --- WHERE RATE - conditional ---
                            AND ''' + rate_where if rate_where else '') + '''
        '''

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
                mixed_id_list.full_time,
                mixed_id_list.net_start_time,
                mixed_id_list.net_stop_time,

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

                mixed_id_list.tags,
                mixed_id_list.rate,
                mixed_id_list.skip_continuous_play,

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
                appendix,

                hstr.recent_state
        --        rtng.rate,
        --        rtng.skip_continuous_play
            FROM

                ---------------------------
                --- mixed level id list ---
                ---------------------------
                (
                WITH RECURSIVE
                    rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, ttitle_req, llang_req, ttitle_orig, llang_orig) AS

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
                            card.full_time,
                            card.net_start_time,
                            card.net_stop_time,

                            themes,
                            genres,
                            origins,
                            directors,
                            actors,
                            lecturers,

                            tags,
                            rate,
                            skip_continuous_play,

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
                            performers,

                            ttitle_req,
                            llang_req,
                            ttitle_orig,
                            llang_orig

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
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as actors,
                                    card_actor.id_card id_card
                                FROM
                                    Person person,
                                    Card_Actor card_actor,
                                    (
                                        SELECT
                                            actor_role.id_actor,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            actor_role
                                        WHERE
                                            actor_role.id_role = role.id
                                        GROUP BY
                                            actor_role.id_actor, role.id_card
                                    ) roles
                                WHERE
                                    card_actor.id_actor = person.id
                                    AND roles.id_actor = person.id
                                    AND roles.id_card = card_actor.id_card
                                GROUP BY
                                    card_actor.id_card
                            ) act
                            ON act.id_card=card.id

                            --------------
                            --- VOICES ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as voices,
                                    card_voice.id_card id_card
                                FROM
                                    Person person,
                                    Card_Voice card_voice,
                                    (
                                        SELECT
                                            voice_role.id_voice,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            voice_role
                                        WHERE
                                            voice_role.id_role = role.id
                                        GROUP BY
                                            voice_role.id_voice, role.id_card
                                    ) roles
                                WHERE
                                    card_voice.id_voice = person.id
                                    AND roles.id_voice = person.id
                                    AND roles.id_card = card_voice.id_card
                                GROUP BY
                                    card_voice.id_card
                            ) vc
                            ON vc.id_card=card.id

                            ----------------
                            --- LECTURER ---
                            ----------------
                            LEFT JOIN
                            (
                                SELECT
                                    group_concat(person.name) lecturers,
                                    card_lecturer.id_card
                                FROM
                                    Person person,
                                    Card_Lecturer card_lecturer
                                WHERE
                                    card_lecturer.id_lecturer = person.id
                                GROUP BY card_lecturer.id_card
                            ) lctr
                            ON lctr.id_card=card.id

                            --- No Filter ---

                            ---------------
                            --- TAGGING ---
                            ---------------
                            LEFT JOIN
                            (
                               SELECT
                                  group_concat(name) tags,
                                  id_card
                               FROM
                                  Tag tag
                               WHERE
                                  id_user=:user_id
                               GROUP BY id_card
                            ) tggng
                            ON tggng.id_card=card.id

                            --------------
                            --- RATING ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT id_card, rate, skip_continuous_play
                                FROM Rating
                                WHERE id_user=:user_id
                            )rtng
                            ON rtng.id_card=card.id

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

                            --------------------------------------------
                            ---         TITLE REQUESTED              ---
                            --- On the requested language, if exists ---
                            --------------------------------------------
                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_req, lang.name llang_req, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name = :lang
                            ) ttlrq
                            ON ttlrq.id_card=card.id

                            ----------------------------------------
                            ---           TITLE ORIG             ---
                            --- Orig if other lang was requested ---
                            ----------------------------------------

                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_orig, lang.name llang_orig, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name <> :lang
                            ) ttlor
                            ON ttlor.id_card=card.id AND ttlor.lang_id=card.id_title_orig

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
                            AND ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''

                            -- Select the given category --
                            AND category.name = :category

                            -------------------
                            -------------------
                            --- Conditional ---
                            ---   filter    ---
                            -------------------
                            -------------------

                            ''' + ('''
                            --- LOWEST FILTER IF NEEDED - conditional ---
                            ''' + lowest_level_where if filter_on is None or filter_on == 'v' else '') + '''

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
                            NULL full_time,
                            NULL net_start_time,
                            NULL net_stop_time,

                            NULL themes,
                            NULL genres,
                            NULL origins,
                            NULL directors,
                            NULL actors,
                            NULL lecturers,

                            NULL tags,
                            NULL rate,
                            NULL skip_continuous_play,

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
                            NULL performers,

                            NULL ttitle_req,
                            NULL llang_req,
                            NULL ttitle_orig,
                            NULL llang_orig

                        FROM
                            rec,
                            Card card,
                            Category category
                        WHERE
                            rec.id_higher_card=card.id
                            AND category.id=card.id_category
                    )
                SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, ttitle_req, llang_req, ttitle_orig, llang_orig

                FROM
                    rec
                WHERE

                    -------------------
                    -------------------
                    --- Conditional ---
                    ---   filter    ---
                    -------------------
                    -------------------

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

                ---------------
                --- HISTORY ---
                ---------------
                LEFT JOIN
                (
                    SELECT
                        ('start_epoch=' || start_epoch || ';recent_epoch=' || recent_epoch || ';recent_position=' || recent_position || ';play_count=' || count(*) ) recent_state,
                        id_card
                    FROM (
                        SELECT id_card, start_epoch, recent_epoch, recent_position
                        FROM History
                        WHERE id_user=:user_id
                        ORDER BY start_epoch DESC
                    )
                    GROUP BY id_card
                )hstr
                ON hstr.id_card=core.id

            --    --------------
            --    --- RATING ---
            --    --------------
            --    LEFT JOIN
            --    (
            --        SELECT id_card, rate, skip_continuous_play
            --        FROM Rating
            --        WHERE id_user=:user_id
            --    )rtng
            --    ON rtng.id_card=core.id

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

        return query

    def get_raw_query_of_lowest_level(self, category, tags=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None):

        tags_where = self.get_sql_where_condition_from_text_filter(tags, 'tags')
        genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
        themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
        actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors', start_separator=';', end_separator=':')
        voices_where = self.get_sql_where_condition_from_text_filter(voices, 'voices', start_separator=';', end_separator=':')
        directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
        lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
        performers_where = self.get_sql_where_condition_from_text_filter(performers, 'performers')
        origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')

        rate_where = self.get_sql_rate_query(rate_value)

        logging.debug(f"rate_where: {rate_where}")

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
                appendix,

                hstr.start_epoch,
                hstr.recent_position,
                hstr.play_count,

                hstr.recent_state recent_state,
                rtng.rate rate,
                rtng.skip_continuous_play skip_continuous_play,
                tggng.tags tags
            FROM
                (
                WITH RECURSIVE
                    rec(id, id_higher_card, level, source_path, title_req, title_orig, lang_orig, lang_req, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, ord) AS

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

                            card.decade,
                            card.date,
                            card.length,
                            card.full_time,
                            card.net_start_time,
                            card.net_stop_time,

                            CASE
                                WHEN sequence IS NULL AND core.title_req IS NOT NULL THEN core.title_req
                                WHEN sequence IS NULL AND core.title_orig IS NOT NULL THEN core.title_orig
                                WHEN sequence<0 THEN basename
                                WHEN sequence>=0 THEN sequence
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
                            card.full_time,
                            card.net_start_time,
                            card.net_stop_time,

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
                SELECT id, id_higher_card, level, source_path, title_req, title_orig, lang_orig, lang_req, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, ord

                FROM
                    rec
                WHERE
        --            (level IS NULL OR level = 'record' OR level = 'episode')
                    ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION.replace('card.', '') + '''

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
                    SELECT
                        GROUP_CONCAT(
                            person.name || ': ' || COALESCE(role_names, ''), ';'
                        ) as actors,
                        card_actor.id_card id_card
                    FROM
                        Person person,
                        Card_Actor card_actor,
                        (
                            SELECT
                                actor_role.id_actor,
                                role.id_card,
                                GROUP_CONCAT(role.name, ',') as role_names
                            FROM
                                role,
                                actor_role
                            WHERE
                                actor_role.id_role = role.id
                            GROUP BY
                                actor_role.id_actor, role.id_card
                        ) roles
                    WHERE
                        card_actor.id_actor = person.id
                        AND roles.id_actor = person.id
                        AND roles.id_card = card_actor.id_card
                    GROUP BY
                        card_actor.id_card
                ) act
                ON act.id_card=card.id

                --------------
                --- VOICES ---
                --------------
                LEFT JOIN
                (
                    SELECT
                        GROUP_CONCAT(
                            person.name || ': ' || COALESCE(role_names, ''), ';'
                        ) as voices,
                        card_voice.id_card id_card
                    FROM
                        Person person,
                        Card_Voice card_voice,
                        (
                            SELECT
                                voice_role.id_voice,
                                role.id_card,
                                GROUP_CONCAT(role.name, ',') as role_names
                            FROM
                                role,
                                voice_role
                            WHERE
                                voice_role.id_role = role.id
                            GROUP BY
                                voice_role.id_voice, role.id_card
                        ) roles
                    WHERE
                        card_voice.id_voice = person.id
                        AND roles.id_voice = person.id
                        AND roles.id_card = card_voice.id_card
                    GROUP BY
                        card_voice.id_card
                ) vc
                ON vc.id_card=card.id

                -----------------
                --- LECTURERS ---
                -----------------
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

                --------------------------------------------
                ---         TITLE REQUESTED              ---
                --- On the requested language, if exists ---
                --------------------------------------------
                LEFT JOIN
                (
                    SELECT tcl.id_card id_card, tcl.text ttitle_req, lang.name llang_req, lang.id lang_id
                    FROM
                        Text_Card_Lang tcl,
                        Language lang
                    WHERE
                        tcl.id_language=lang.id
                        AND tcl.type="T"
                        AND lang.name = :lang
                ) ttlrq
                ON ttlrq.id_card=card.id
                ----------------------------------------
                ---           TITLE ORIG             ---
                --- Orig if other lang was requested ---
                ----------------------------------------
                LEFT JOIN
                (
                    SELECT tcl.id_card id_card, tcl.text ttitle_orig, lang.name llang_orig, lang.id lang_id
                    FROM
                        Text_Card_Lang tcl,
                        Language lang
                    WHERE
                        tcl.id_language=lang.id
                        AND tcl.type="T"
                        AND lang.name <> :lang
                ) ttlor
                ON ttlor.id_card=card.id AND ttlor.lang_id=card.id_title_orig




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

                ---------------
                --- HISTORY ---
                ---------------
                LEFT JOIN
                (
                    SELECT
                        ('start_epoch=' || start_epoch || ';recent_epoch=' || recent_epoch || ';recent_position=' || recent_position || ';play_count=' || count(*) ) recent_state,
                        id_card,
                        start_epoch,
                        recent_position,
                        count(*) play_count
                    FROM (
                        SELECT id_card, start_epoch, recent_epoch, recent_position
                        FROM History
                        WHERE id_user=:user_id
                        ORDER BY start_epoch DESC
                    )
                    GROUP BY id_card
                )hstr
                ON hstr.id_card=card.id

                --------------
                --- RATING ---
                --------------
                LEFT JOIN
                (
                    SELECT id_card, rate, skip_continuous_play
                    FROM Rating
                    WHERE id_user=:user_id
                )rtng
                ON rtng.id_card=card.id

                ---------------
                --- TAGGING ---
                ---------------
                LEFT JOIN
                (
                   SELECT
                      group_concat(name) tags,
                      id_card
                   FROM
                      Tag tag
                   WHERE
                      id_user=:user_id
                   GROUP BY id_card
                ) tggng
                ON tggng.id_card=card.id

            WHERE
                card.id=recursive_list.id
                AND category.id=card.id_category

                -------------------
                -------------------
                --- Conditional ---
                ---   filter    ---
                -------------------
                -------------------

                --- WHERE TITLE ---
                AND CASE
                    WHEN :title IS NOT NULL AND ttitle_req IS NOT NULL THEN ttitle_req LIKE :title
                    WHEN :title IS NOT NULL THEN ttitle_orig LIKE :title
                    ELSE 1
                END

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
                --- WHERE VOICES - conditional ---
                AND ''' + voices_where if voices_where else '') + '''
                ''' + ('''
                --- WHERE ORIGINS - conditional ---
                AND ''' + origins_where if origins_where else '') + '''
                ''' + ('''
                --- WHERE LECTURERS - conditional ---
                AND ''' + lecturers_where if lecturers_where else '') + '''
                ''' + ('''
                --- WHERE PERFORMERS - conditional ---
                AND ''' + performers_where if performers_where else '') + '''
                ''' + ('''
                --- WHERE TAGS - conditional ---
                AND ''' + tags_where if tags_where else '') + '''
               ''' + ('''
                --- WHERE RATE - conditional ---
                AND ''' + rate_where if rate_where else '') + '''
        '''

        return query

    def get_raw_query_of_highest_level_abc(self, category, tags=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None):
        tags_where = self.get_sql_where_condition_from_text_filter(tags, 'tags')
        genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
        themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
        actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors', start_separator=';', end_separator=':')
        voices_where = self.get_sql_where_condition_from_text_filter(voices, 'voices', start_separator=';', end_separator=':')
        writers_where = self.get_sql_where_condition_from_text_filter(writers, 'writers')
        directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
        lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
        performers_where = self.get_sql_where_condition_from_text_filter(performers, 'performers')
        origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')
        titles_req_where = self.get_sql_like_where_condition_from_text_filter(title, 'ttitle_req')
        titles_orig_where = self.get_sql_like_where_condition_from_text_filter(title, 'ttitle_orig')
        rate_where = self.get_sql_rate_query(rate_value)

        query = '''

            SELECT

                CASE
                    WHEN UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    )) IN ('0','1','2','3','4','5','6','7','8','9') THEN '0-9'
                    ELSE UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    ))
                END AS name,
                CASE
                    WHEN UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    )) IN ('0','1','2','3','4','5','6','7','8','9') THEN '0%_OR_1%_OR_2%_OR_3%_OR_4%_OR_5%_OR_6%_OR_7%_OR_8%_OR_9%'
                    ELSE UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    )) || '%'
                END AS filter
            FROM

                ---------------------------
                --- mixed level id list ---
                ---------------------------
                (
                WITH RECURSIVE
                    rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play,sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, ttitle_req, llang_req, ttitle_orig, llang_orig) AS

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
                            card.full_time,
                            card.net_start_time,
                            card.net_stop_time,

                            themes,
                            genres,
                            origins,
                            directors,
                            actors,
                            lecturers,

                            tags,
                            rate,
                            skip_continuous_play,

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
                            performers,

                            ttitle_req,
                            llang_req,
                            ttitle_orig,
                            llang_orig

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
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as actors,
                                    card_actor.id_card id_card
                                FROM
                                    Person person,
                                    Card_Actor card_actor,
                                    (
                                        SELECT
                                            actor_role.id_actor,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            actor_role
                                        WHERE
                                            actor_role.id_role = role.id
                                        GROUP BY
                                            actor_role.id_actor, role.id_card
                                    ) roles
                                WHERE
                                    card_actor.id_actor = person.id
                                    AND roles.id_actor = person.id
                                    AND roles.id_card = card_actor.id_card
                                GROUP BY
                                    card_actor.id_card
                            ) act
                            ON act.id_card=card.id

                            --------------
                            --- VOICES ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as voices,
                                    card_voice.id_card id_card
                                FROM
                                    Person person,
                                    Card_Voice card_voice,
                                    (
                                        SELECT
                                            voice_role.id_voice,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            voice_role
                                        WHERE
                                            voice_role.id_role = role.id
                                        GROUP BY
                                            voice_role.id_voice, role.id_card
                                    ) roles
                                WHERE
                                    card_voice.id_voice = person.id
                                    AND roles.id_voice = person.id
                                    AND roles.id_card = card_voice.id_card
                                GROUP BY
                                    card_voice.id_card
                            ) vc
                            ON vc.id_card=card.id

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

                            ---------------
                            --- TAGGING ---
                            ---------------
                            LEFT JOIN
                            (
                               SELECT
                                  group_concat(name) tags,
                                  id_card
                               FROM
                                  Tag tag
                               WHERE
                                  id_user=:user_id
                               GROUP BY id_card
                            ) tggng
                            ON tggng.id_card=card.id

                            --------------
                            --- RATING ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT id_card, rate, skip_continuous_play
                                FROM Rating
                                WHERE id_user=:user_id
                            )rtng
                            ON rtng.id_card=card.id

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

                            --------------------------------------------
                            ---         TITLE REQUESTED              ---
                            --- On the requested language, if exists ---
                            --------------------------------------------
                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_req, lang.name llang_req, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name = :lang
                            ) ttlrq
                            ON ttlrq.id_card=card.id

                            ----------------------------------------
                            ---           TITLE ORIG             ---
                            --- Orig if other lang was requested ---
                            ----------------------------------------

                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_orig, lang.name llang_orig, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name <> :lang
                            ) ttlor
                            ON ttlor.id_card=card.id AND ttlor.lang_id=card.id_title_orig

                        ------------------------
                        --- INITIAL WHERE    ---
                        --- the lowest level ---
                        ------------------------

                        WHERE
                            -- card can not be appendix --
                            card.isappendix == 0

                            -- connect card to category --
                            AND category.id=card.id_category

                            -- Find the lowest level --
                            -- AND card.level IS NULL

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

                            ''' + (
                                '''
                                AND CASE
                                    WHEN ttitle_req IS NOT NULL THEN ''' + titles_req_where + '''
                                    ELSE ''' + titles_orig_where + '''
                                END
                                ''' if titles_orig_where else ''' '''
                            ) + '''

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
                            --- WHERE WRITERS - conditional ---
                            AND ''' + writers_where if writers_where else '') + '''

                            ''' + ('''
                            --- WHERE ACTORS - conditional ---
                            AND ''' + actors_where if actors_where else '') + '''

                            ''' + ('''
                            --- WHERE VOICES - conditional ---
                            AND ''' + voices_where if voices_where else '') + '''

                            ''' + ('''
                            --- WHERE ORIGINS - conditional ---
                            AND ''' + origins_where if origins_where else '') + '''

                            ''' + ('''
                            --- WHERE PERFORMERS - conditional ---
                            AND ''' + performers_where if performers_where else '') + '''

                            ''' + ('''
                            --- WHERE LECTURERS - conditional ---
                            AND ''' + lecturers_where if lecturers_where else '') + '''

                            ''' + ('''
                            --- WHERE TAGS - conditional ---
                            AND ''' + tags_where if tags_where else '') + '''

                            ''' + ('''
                            --- WHERE RATE - conditional ---
                            AND ''' + rate_where if rate_where else '') + '''

                            AND CASE

                                -- level: ^ (*, None), filter: v (*, None) => show the HIGHEST level and filter on the LOWEST level on any type => filter LOWEST level
                                -- Genre: Standalone Scifi
                                WHEN (:level IS NULL OR :level = '^') AND (:filter_on IS NULL OR :filter_on = 'v') THEN ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''

                                -- level: ^ (*, None), filter: ^ (-) => show the HIGHEST level and filter on the same (HIGHEST) level on any type => filter HIGHEST level
                                -- Title: Standalone or Series
                                WHEN (:level IS NULL OR :level = '^') AND :filter_on IS not NULL AND :filter_on = '-' THEN card.id_higher_card IS NULL

                                -- level: <level>, filter: v (* None) => show the GIVEN level and filter on the LOWEST level on any type => filter LOWEST level
                                WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND (:filter_on IS NULL OR :filter_on = 'v') THEN ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + ''' AND card.id_higher_card IS not NULL

                                -- level: <level>, filter: - => show the GIVEN level and filter on the same (GIVEN) level on any type => filter GIVEN level
                                WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND :filter_on IS not NULL AND :filter_on = '-' THEN card.level = :level

                                ELSE 0

                            END

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
                            NULL full_time,
                            NULL net_start_time,
                            NULL net_stop_time,

                            NULL themes,
                            NULL genres,
                            NULL origins,
                            NULL directors,
                            NULL actors,
                            NULL lecturers,

                            NULL tags,
                            NULL rate,
                            NULL skip_continuous_play,

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
                            NULL performers,

                            NULL ttitle_req,
                            NULL llang_req,
                            NULL ttitle_orig,
                            NULL llang_orig

                        FROM
                            rec,
                            Card card,
                            Category category
                        WHERE
                            rec.id_higher_card=card.id
                            AND category.id=card.id_category
                    )
                SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers

                FROM
                    rec
                WHERE

                    -------------------
                    -------------------
                    --- Conditional ---
                    ---   filter    ---
                    -------------------
                    -------------------

                    CASE
                        -- level: ^ (*, None), filter: v (*, None) => show the HIGHEST level and filter on the LOWEST level on any type => show HIGHEST level
                        WHEN (:level IS NULL OR :level = '^') AND (:filter_on IS NULL OR :filter_on = 'v') THEN id_higher_card IS NULL

                        -- level: ^ (*, None), filter: - => show the HIGHEST level and filter on the same (HIGHEST) level on any type => show HIGHEST level
                        WHEN (:level IS NULL OR :level = '^') AND :filter_on IS not NULL AND :filter_on = '-' THEN id_higher_card IS NULL

                        -- level: <level>, filter: v (* None) => show the GIVEN level and filter on the LOWEST level on any type => GIVEN level
                        WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND (:filter_on IS NULL OR :filter_on = 'v') THEN level = :level

                        -- level: <level>, filter: - => show the GIVEN level and filter on the same (GIVEN) level on any type => GIVEN level
                        WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND :filter_on IS not NULL AND :filter_on = '-' THEN level = :level

                        ELSE 0
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
                    MAX(title_orig) title_orig


                FROM
                    (
                    SELECT
                        card.id id,

                        NULL title_req,
                        tcl.text title_orig
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
                        NULL title_orig
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

                mixed_id_list.id=core.id

            GROUP BY name
            ORDER BY name
            LIMIT :limit; '''

        return query