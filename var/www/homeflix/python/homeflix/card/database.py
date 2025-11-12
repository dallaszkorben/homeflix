import os
import sqlite3
import logging
import hashlib
import time

from flask import session

from threading import Lock
from sqlite3 import Error
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

# SQLAlchemy imports
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Import SQLAlchemy models
from homeflix.card.models import Base, User, Category, Genre, Language, Country, Theme, MediaType, Person, Card, Tag, History, Rating
from homeflix.card.models import card_actor_table, card_voice_table, card_director_table, card_writer_table
from sqlalchemy.exc import SQLAlchemyError

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
            SqlDatabase.TABLE_VOICE_ROLE,
        ]

        self.table_personal_list = [
            SqlDatabase.TABLE_USER,
            SqlDatabase.TABLE_HISTORY,
            SqlDatabase.TABLE_RATING,
            SqlDatabase.TABLE_TAG,
        ]

        self.lock = Lock()

        # Query cache infrastructure
        self._cache = {}
        self._cache_timestamps = {}

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

        # SQLAlchemy setup (coexisting with existing SQLite)
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            poolclass=StaticPool,
            connect_args={'check_same_thread': False},
            echo=False  # Set to True for SQL debugging
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.Base = Base  # Use imported Base from models

        # check if the static databases are corrupted/not existed
        if not self.is_static_dbs_ok():
            self.recreate_static_dbs()

        self.fill_up_constant_dicts()

        # check if the personal databases are corrupted/not existed
        if not self.is_personal_dbs_ok():
            self.recreate_personal_dbs()


    def __del__(self):
        self.conn.close()

    def _get_cached_or_execute(self, cache_key, cache_duration_seconds, func, *args, **kwargs):
        """Get cached result or execute function and cache the result"""
        now = time.time()

        # Check if we have a valid cached result
        if (cache_key in self._cache and
            cache_key in self._cache_timestamps and
            now - self._cache_timestamps[cache_key] < cache_duration_seconds):
            age = now - self._cache_timestamps[cache_key]
            logging.info(f"🚀 CACHE HIT: {cache_key} (age: {age:.1f}s, expires in: {cache_duration_seconds - age:.1f}s)")
            return self._cache[cache_key]

        # Execute function and cache result
        logging.info(f"💾 CACHE MISS: {cache_key} - executing function and caching result")
        result = func(*args, **kwargs)
        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = now
        logging.info(f"✅ CACHED: {cache_key} (expires in: {cache_duration_seconds}s)")
        return result

    def _invalidate_cache(self, pattern=None):
        """Invalidate cache entries matching pattern or all if pattern is None"""
        if pattern is None:
            cache_count = len(self._cache)
            self._cache.clear()
            self._cache_timestamps.clear()
            logging.info(f"💥 CACHE CLEARED: All {cache_count} entries invalidated")
        else:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
            logging.info(f"💥 CACHE INVALIDATED: {len(keys_to_remove)} entries matching '{pattern}'")

    def get_sqlalchemy_session(self):
        """Get SQLAlchemy session for new operations"""
        return self.SessionLocal()
















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

        # Clear all cache since database was completely rebuilt
        self._invalidate_cache()






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
        """SQLAlchemy version of fill_up_user_table"""
        with self.get_sqlalchemy_session() as session:
            try:
                # admin user
                admin_id = self.append_user(
                    session, 'admin',
                    generate_password_hash('admin'),
                    is_admin=True,
                    user_id=1234,
                    language_code='en',
                    descriptor_color='rgb(0, 117, 104)',
                    show_original_title=True,
                    show_lyrics_anyway=True,
                    show_storyline_anyway=True,
                    play_continuously=True,
                    history_days=365
                )

                # default user
                default_id = self.append_user(
                    session, 'default',
                    generate_password_hash('default'),
                    is_admin=False,
                    user_id=1235,
                    language_code='en',
                    descriptor_color='rgb(69, 113, 144)',
                    show_original_title=True,
                    show_lyrics_anyway=True,
                    show_storyline_anyway=True,
                    play_continuously=True,
                    history_days=365
                )

                session.commit()
                logging.info(f"SQLAlchemy: Created users - admin: {admin_id}, default: {default_id}")

            except Exception as e:
                session.rollback()
                logging.error(f"SQLAlchemy fill_up_user_table failed: {e}")
                raise


    def fill_up_user_table_legacy(self):

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

                id = self.append_user_legacy(cur, username, password=hashed_password, is_admin=is_admin, user_id=user_id, language_code=language_code, descriptor_color=descriptor_color, show_original_title=show_original_title, show_lyrics_anyway=show_lyrics_anyway, show_storyline_anyway=show_storyline_anyway, play_continuously=play_continuously, history_days=history_days)

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

                id = self.append_user_legacy(cur, username, password=hashed_password, is_admin=is_admin, user_id=user_id, language_code=language_code, descriptor_color=descriptor_color, show_original_title=show_original_title, show_lyrics_anyway=show_lyrics_anyway, show_storyline_anyway=show_storyline_anyway, play_continuously=play_continuously, history_days=history_days)

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
        with self.get_sqlalchemy_session() as session:
            self.category_name_id_dict = {}
            self.category_id_name_dict = {}
            category_list = self.translator.get_all_category_codes()
            for category in category_list:
                id = self.append_category(session, category)
                self.category_name_id_dict[category] = id
                self.category_id_name_dict[id] = category
            session.commit()




    def fill_up_genre_table_from_dict(self):
        with self.get_sqlalchemy_session() as session:
            self.genre_name_id_dict = {}
            self.genre_id_name_dict = {}
            genre_list = self.translator.get_all_genre_codes()
            for genre in genre_list:
                id = self.append_genre(session, genre)
                self.genre_name_id_dict[genre] = id
                self.genre_id_name_dict[id] = genre
            session.commit()


    def fill_up_mediatype_table_from_dict(self):
        with self.get_sqlalchemy_session() as session:
            self.mediatype_name_id_dict = {}
            self.mediatype_id_name_dict = {}
            mediatype_list = self.translator.get_all_mediatype_codes()
            for mediatype in mediatype_list:
                id = self.append_mediatype(session, mediatype)
                self.mediatype_name_id_dict[mediatype] = id
                self.mediatype_id_name_dict[id] = mediatype
            session.commit()


    def fill_up_theme_table_from_dict(self):
        with self.get_sqlalchemy_session() as session:
            self.theme_name_id_dict = {}
            self.theme_id_name_dict = {}
            theme_list = self.translator.get_all_theme_codes()
            for theme in theme_list:
                id = self.append_theme(session, theme)
                self.theme_name_id_dict[theme] = id
                self.theme_id_name_dict[id] = theme
            session.commit()


    def fill_up_language_table_from_dict(self):
        with self.get_sqlalchemy_session() as session:
            self.language_name_id_dict = {}
            self.language_id_name_dict = {}
            lang_list = self.translator.get_all_language_codes()
            for lang in lang_list:
                id = self.append_language(session, lang)
                self.language_name_id_dict[lang] = id
                self.language_id_name_dict[id] = lang
            session.commit()


    def fill_up_country_table_from_dict(self):
        with self.get_sqlalchemy_session() as session:
            self.country_name_id_dict = {}
            self.country_id_name_dict = {}
            country_list = self.translator.get_all_country_codes()
            for country in country_list:
                id = self.append_country(session, country)
                self.country_name_id_dict[country] = id
                self.country_id_name_dict[id] = country
            session.commit()


    def append_user_legacy(self, cur, username, password, is_admin=False, user_id=None, language_code='en', descriptor_color='rgb(69,113,144)', show_original_title=True, show_lyrics_anyway=True, show_storyline_anyway=True, play_continuously=True, history_days=365):
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

    def append_user(self, session, username, password, is_admin=False, user_id=None, language_code='en', descriptor_color='rgb(69,113,144)', show_original_title=True, show_lyrics_anyway=True, show_storyline_anyway=True, play_continuously=True, history_days=365):
        """SQLAlchemy version of append_user"""
        try:
            # Get language ID
            language = session.query(Language).filter(Language.name == language_code).first()
            if not language:
                logging.error(f"Language '{language_code}' not found")
                return None

            created_epoch = int(datetime.now().timestamp())

            new_user = User(
                name=username,
                password=password,
                is_admin=is_admin,
                id_language=language.id,
                descriptor_color=descriptor_color,
                show_original_title=show_original_title,
                show_lyrics_anyway=show_lyrics_anyway,
                show_storyline_anyway=show_storyline_anyway,
                play_continuously=play_continuously,
                history_days=history_days,
                created_epoch=created_epoch
            )

            if user_id:
                new_user.id = user_id

            session.add(new_user)
            session.flush()
            return new_user.id

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_user failed: {e}")
            return None


    def append_category(self, session, category):
        """SQLAlchemy version of append_category"""
        try:
            # Check if category already exists
            existing = session.query(Category).filter(Category.name == category).first()
            if existing:
                return existing.id

            # Create new category
            new_category = Category(name=category)
            session.add(new_category)
            session.flush()  # Get the ID without committing
            return new_category.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_category failed: {e}")
            return None


    def append_language(self, session, language_name):
        """SQLAlchemy version of append_language"""
        try:
            existing = session.query(Language).filter(Language.name == language_name).first()
            if existing:
                return existing.id
            new_language = Language(name=language_name)
            session.add(new_language)
            session.flush()
            return new_language.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_language failed: {e}")
            return None


    def append_country(self, session, country_name):
        """SQLAlchemy version of append_country"""
        try:
            new_country = Country(name=country_name)
            session.add(new_country)
            session.flush()
            return new_country.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_country failed: {e}")
            return None


    def append_genre(self, session, genre_name):
        """SQLAlchemy version of append_genre"""
        try:
            existing = session.query(Genre).filter(Genre.name == genre_name).first()
            if existing:
                return existing.id
            new_genre = Genre(name=genre_name)
            session.add(new_genre)
            session.flush()
            return new_genre.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_genre failed: {e}")
            return None


    def append_theme(self, session, theme_name):
        """SQLAlchemy version of append_theme"""
        try:
            new_theme = Theme(name=theme_name)
            session.add(new_theme)
            session.flush()
            return new_theme.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_theme failed: {e}")
            return None


    def append_mediatype(self, session, mediatype_name):
        """SQLAlchemy version of append_mediatype"""
        try:
            new_mediatype = MediaType(name=mediatype_name)
            session.add(new_mediatype)
            session.flush()
            return new_mediatype.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_mediatype failed: {e}")
            return None

    def append_person(self, session, person_name):
        """SQLAlchemy version for Person table"""
        try:
            new_person = Person(name=person_name)
            session.add(new_person)
            session.flush()
            return new_person.id
        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_person failed: {e}")
            return None

    def append_card_media(self, card_path, title_orig, category, titles={}, level=None, card_id=None, isappendix=0, show=1, download=0, title_on_thumbnail=1, title_show_sequence='', storylines={}, lyrics={}, decade=None, date=None, length=None, full_time=None, net_start_time=None, net_stop_time=None, sounds=[], subs=[], genres=[], themes=[], origins=[], writers=[], actors=[], stars=[], directors=[], voices=[], hosts=[], guests=[], interviewers=[], interviewees=[], presenters=[], lecturers=[], performers=[], reporters=[], media={}, basename=None, source_path=None, sequence=None, higher_card_id=None):
        """SQLAlchemy version of append_card_media"""
        try:
            with self.get_sqlalchemy_session() as session:
                language = session.query(Language).filter(Language.name == title_orig).first()
                if not language:
                    return None

                category_obj = session.query(Category).filter(Category.name == category).first()
                if not category_obj:
                    return None

                if card_id is None:
                    hasher = hashlib.md5()
                    hasher.update(card_path.encode('utf-8'))
                    card_id = hasher.hexdigest()

                new_card = Card(
                    id=card_id,
                    level=level,
                    show=show,
                    download=download,
                    isappendix=isappendix,
                    id_title_orig=language.id,
                    title_on_thumbnail=title_on_thumbnail,
                    title_show_sequence=title_show_sequence,
                    id_category=category_obj.id,
                    decade=decade,
                    date=date,
                    length=length,
                    full_time=full_time,
                    net_start_time=net_start_time,
                    net_stop_time=net_stop_time,
                    basename=basename,
                    source_path=source_path,
                    id_higher_card=higher_card_id,
                    sequence=sequence
                )

                session.add(new_card)
                session.flush()

                # Add titles
                for lang, title in titles.items():
                    self.add_card_text(session, new_card.id, lang, title, "T")

                # Add storylines
                for lang, storyline in storylines.items():
                    self.add_card_text(session, new_card.id, lang, storyline, "S")

                # Add lyrics
                for lang, lyric in lyrics.items():
                    self.add_card_text(session, new_card.id, lang, lyric, "L")

                # Add genres
                for genre in genres:
                    self.add_card_genre(session, new_card.id, genre)

                # Add themes
                for theme in themes:
                    self.add_card_theme(session, new_card.id, theme)

                # Add origins
                for origin in origins:
                    self.add_card_origin(session, new_card.id, origin)

                # Add sounds
                for sound in sounds:
                    self.add_card_sound(session, new_card.id, sound)

                # Add subtitles
                for sub in subs:
                    self.add_card_subtitle(session, new_card.id, sub)

                # Add writers
                for writer in writers:
                    if writer:
                        person = session.query(Person).filter(Person.name == writer).first()
                        if not person:
                            person = Person(name=writer)
                            session.add(person)
                            session.flush()
                        if person not in new_card.writers:
                            new_card.writers.append(person)

                # Add actors (can be list or dict with roles)
                if isinstance(actors, list):
                    for actor in actors:
                        if actor:
                            self.add_card_actor(session, new_card.id, actor)
                else:
                    for actor, role in actors.items():
                        if actor:
                            self.add_card_actor(session, new_card.id, actor)
                            # TODO: Handle roles - requires Role table implementation

                # Add directors
                for director in directors:
                    if director:
                        person = session.query(Person).filter(Person.name == director).first()
                        if not person:
                            person = Person(name=director)
                            session.add(person)
                            session.flush()
                        if person not in new_card.directors:
                            new_card.directors.append(person)

                # Add voices (can be list or dict with roles)
                if isinstance(voices, list):
                    for voice in voices:
                        if voice:
                            person = session.query(Person).filter(Person.name == voice).first()
                            if not person:
                                person = Person(name=voice)
                                session.add(person)
                                session.flush()
                            if person not in new_card.voices:
                                new_card.voices.append(person)
                else:
                    for voice, role in voices.items():
                        if voice:
                            person = session.query(Person).filter(Person.name == voice).first()
                            if not person:
                                person = Person(name=voice)
                                session.add(person)
                                session.flush()
                            if person not in new_card.voices:
                                new_card.voices.append(person)
                            # TODO: Handle roles - requires Role table implementation

                # Add media files
                for media_type, media_list in media.items():
                    for medium in media_list:
                        self.add_card_media(session, new_card.id, medium, media_type)

                # Invalidate relevant caches when new media is added
#                logging.info(f"🎬 NEW MEDIA ADDED: Invalidating all caches for card {new_card.id}")
#                self._invalidate_cache("actors_")
#                self._invalidate_cache("directors_")
#                self._invalidate_cache("writers_")
#                self._invalidate_cache("highest_cards_")
#                self._invalidate_cache("next_cards_")
#                self._invalidate_cache("lowest_cards_")

                session.commit()
                return new_card.id

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy append_card_media failed: {e}")
            return None

    def append_hierarchy(self, card_path, title_orig, category, titles, level=None, card_id=None, show=1, download=0, isappendix=0, title_on_thumbnail=1, title_show_sequence='', storylines={}, date=None, decade=None, genres=None, themes=None, origins=None, basename=None, source_path=None, sequence=None, higher_card_id=None):
        """SQLAlchemy version of append_hierarchy"""
        try:
            with self.get_sqlalchemy_session() as session:
                language = session.query(Language).filter(Language.name == title_orig).first()
                if not language:
                    return None

                category_obj = session.query(Category).filter(Category.name == category).first()
                if not category_obj:
                    return None

                if card_id is None:
                    hasher = hashlib.md5()
                    hasher.update(card_path.encode('utf-8'))
                    card_id = hasher.hexdigest()

                new_card = Card(
                    id=card_id,
                    level=level,
                    show=show,
                    download=download,
                    isappendix=isappendix,
                    id_title_orig=language.id,
                    title_on_thumbnail=title_on_thumbnail,
                    title_show_sequence=title_show_sequence,
                    id_category=category_obj.id,
                    decade=decade,
                    date=date,
                    basename=basename,
                    source_path=source_path,
                    id_higher_card=higher_card_id,
                    sequence=sequence
                )

                session.add(new_card)
                session.flush()

                # Add titles
                for lang, title in titles.items():
                    self.add_card_text(session, new_card.id, lang, title, "T")

                # Add storylines
                for lang, storyline in storylines.items():
                    self.add_card_text(session, new_card.id, lang, storyline, "S")

                # Add genres
                if genres:
                    for genre in genres:
                        self.add_card_genre(session, new_card.id, genre)

                # Add themes
                if themes:
                    for theme in themes:
                        self.add_card_theme(session, new_card.id, theme)

                # Add origins
                if origins:
                    for origin in origins:
                        self.add_card_origin(session, new_card.id, origin)

                # Invalidate relevant caches when new hierarchy is added
#                logging.info(f"🏗️ NEW HIERARCHY ADDED: Invalidating all caches for card {new_card.id}")
#                self._invalidate_cache("actors_")
#                self._invalidate_cache("directors_")
#                self._invalidate_cache("writers_")
#                self._invalidate_cache("highest_cards_")
#                self._invalidate_cache("next_cards_")
#                self._invalidate_cache("lowest_cards_")

                session.commit()
                return new_card.id

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy append_hierarchy failed: {e}")
            return None


    def get_card_by_id(self, session, card_id):
        """SQLAlchemy version to get card by ID"""
        try:
            return session.query(Card).filter(Card.id == card_id).first()
        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy get_card_by_id failed: {e}")
            return None


    def add_card_text(self, session, card_id, language_code, text, text_type):
        """SQLAlchemy version to add text to card"""
        try:
            from homeflix.card.models import TextCardLang

            language = session.query(Language).filter(Language.name == language_code).first()
            if not language:
                return False

            # Check if text already exists
            existing = session.query(TextCardLang).filter(
                TextCardLang.id_card == card_id,
                TextCardLang.id_language == language.id,
                TextCardLang.type == text_type
            ).first()

            if existing:
                # Update existing text
                existing.text = text
                session.flush()
                return True
            else:
                # Create new text
                text_card = TextCardLang(
                    id_card=card_id,
                    id_language=language.id,
                    text=text,
                    type=text_type
                )

                session.add(text_card)
                session.flush()
                return True

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy add_card_text failed: {e}")
            return False


    def add_card_media(self, session, card_id, media_name, media_type_name):
        """SQLAlchemy version to add media to card"""
        try:
            from homeflix.card.models import CardMedia

            media_type = session.query(MediaType).filter(MediaType.name == media_type_name).first()
            if not media_type:
                return False

            card_media = CardMedia(
                id_card=card_id,
                name=media_name,
                id_mediatype=media_type.id
            )

            session.add(card_media)
            session.flush()
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"SQLAlchemy add_card_media failed: {e}")
            return False


    def get_card_texts(self, session, card_id, text_type=None):
        """SQLAlchemy version to get card texts"""
        try:
            from homeflix.card.models import TextCardLang

            query = session.query(TextCardLang).filter(TextCardLang.id_card == card_id)
            if text_type:
                query = query.filter(TextCardLang.type == text_type)

            return query.all()

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy get_card_texts failed: {e}")
            return []


    def get_card_media(self, session, card_id):
        """SQLAlchemy version to get card media"""
        try:
            from homeflix.card.models import CardMedia

            return session.query(CardMedia).filter(CardMedia.id_card == card_id).all()

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy get_card_media failed: {e}")
            return []


    def add_card_genre(self, session, card_id, genre_name):
        """SQLAlchemy version to add genre to card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            genre = session.query(Genre).filter(Genre.name == genre_name).first()

            if card and genre and genre not in card.genres:
                card.genres.append(genre)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy add_card_genre failed: {e}")
            return False


    def add_card_theme(self, session, card_id, theme_name):
        """SQLAlchemy version to add theme to card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            theme = session.query(Theme).filter(Theme.name == theme_name).first()

            if card and theme and theme not in card.themes:
                card.themes.append(theme)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy add_card_theme failed: {e}")
            return False


    def add_card_sound(self, session, card_id, language_name):
        """SQLAlchemy version to add sound language to card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            language = session.query(Language).filter(Language.name == language_name).first()

            if card and language and language not in card.sounds:
                card.sounds.append(language)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy add_card_sound failed: {e}")
            return False


    def add_card_subtitle(self, session, card_id, language_name):
        """SQLAlchemy version to add subtitle language to card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            language = session.query(Language).filter(Language.name == language_name).first()

            if card and language and language not in card.subs:
                card.subs.append(language)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy add_card_subtitle failed: {e}")
            return False


    def add_card_origin(self, session, card_id, country_name):
        """SQLAlchemy version to add origin country to card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            country = session.query(Country).filter(Country.name == country_name).first()

            if card and country and country not in card.origins:
                card.origins.append(country)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy add_card_origin failed: {e}")
            return False


    def add_card_actor(self, session, card_id, person_name):
        """SQLAlchemy version to add actor to card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            person = session.query(Person).filter(Person.name == person_name).first()

            if not person:
                person = Person(name=person_name)
                session.add(person)
                session.flush()

            if card and person and person not in card.actors:
                card.actors.append(person)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy add_card_actor failed: {e}")
            return False


    def remove_card_genre(self, session, card_id, genre_name):
        """SQLAlchemy version to remove genre from card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            genre = session.query(Genre).filter(Genre.name == genre_name).first()

            if card and genre and genre in card.genres:
                card.genres.remove(genre)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy remove_card_genre failed: {e}")
            return False


    def remove_card_actor(self, session, card_id, person_name):
        """SQLAlchemy version to remove actor from card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            person = session.query(Person).filter(Person.name == person_name).first()

            if card and person and person in card.actors:
                card.actors.remove(person)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy remove_card_actor failed: {e}")
            return False


    def remove_card_sound(self, session, card_id, language_name):
        """SQLAlchemy version to remove sound language from card"""
        try:
            card = session.query(Card).filter(Card.id == card_id).first()
            language = session.query(Language).filter(Language.name == language_name).first()

            if card and language and language in card.sounds:
                card.sounds.remove(language)
                session.flush()
                return True
            return False

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy remove_card_sound failed: {e}")
            return False

    # Step 11: Simple List Methods - SQLAlchemy versions


    def get_list_of_actors_by_role_count(self, category, minimum=3, limit=15, json=True):
        """SQLAlchemy version of get_list_of_actors_by_role_count"""
        # This is a complex recursive query - for now, delegate to the original method
        # TODO: Convert to proper SQLAlchemy recursive CTE in future
        return self.get_list_of_actors_by_role_count(category, minimum, limit, json)



    def get_list_of_voices_by_role_count(self, category, minimum=3, limit=15, json=True):
        """SQLAlchemy version of get_list_of_voices_by_role_count"""
        # This is a complex recursive query - for now, delegate to the original method
        # TODO: Convert to proper SQLAlchemy recursive CTE in future
        return self.get_list_of_voices_by_role_count(category, minimum, limit, json)



    def get_list_of_directors_by_movie_count(self, category, minimum=3, limit=15, json=True):
        """SQLAlchemy version of get_list_of_directors_by_movie_count"""
        # This is a complex recursive query - for now, delegate to the original method
        # TODO: Convert to proper SQLAlchemy recursive CTE in future
        return self.get_list_of_directors_by_movie_count(category, minimum, limit, json)



    def get_list_of_tags(self, category, limit=15, json=True):
        """SQLAlchemy version of get_list_of_tags"""
        result = False
        error_message = "Lock error"
        records = {}

        try:
            from flask import session as flask_session
            user_data = flask_session.get('logged_in_user', None)
            if user_data:
                user_id = user_data['user_id']
            else:
                user_id = -1
        except RuntimeError:
            # Working outside of request context - use default user_id
            user_id = -1

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as db_session:
                    # Query for distinct tag names for given category and user
                    query = db_session.query(Tag.name.label('tag')).distinct()\
                        .join(Card, Tag.id_card == Card.id)\
                        .join(Category, Card.id_category == Category.id)\
                        .filter(Category.name == category)\
                        .filter(Tag.id_user == user_id)\
                        .order_by(Tag.name)\
                        .limit(limit)

                    records = query.all()

                    if json:
                        records = [record.tag for record in records]

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"Fetching the tag list failed: {e}"
                logging.error(error_message)

        return {"result": result, "data": records, "error": error_message}


    def append_card_media_legacy(self, card_path, title_orig, titles={}, title_on_thumbnail=1, title_show_sequence='', card_id=None, isappendix=0, show=1, download=0, category=None,  level=None, storylines={}, lyrics={}, decade=None, date=None, length=None, full_time=None, net_start_time=None, net_stop_time=None, sounds=[], subs=[], genres=[], themes=[], origins=[], writers=[], actors=[], stars=[], directors=[], voices=[], hosts=[], guests=[], interviewers=[], interviewees=[], presenters=[], lecturers=[], performers=[], reporters=[], media={}, basename=None, source_path=None, sequence=None, higher_card_id=None):

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


    # ================
    #
    # === requests ===
    #
    # ================


    def get_logged_in_user_data(self):
        """SQLAlchemy version of get_logged_in_user_data"""
        result = False
        data = {}
        error_message = "Lock error"

        user_data = session.get('logged_in_user', None)
        if user_data:
            username = user_data['username']
        else:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as session:
                    user = session.query(User).filter(User.name == username).first()

                    if user:
                        result = True
                        data = {
                            'is_admin': user.is_admin,
                            'name': user.name,
                            'language_code': user.language.name if user.language else None,
                            'show_original_title': user.show_original_title,
                            'show_lyrics_anyway': user.show_lyrics_anyway,
                            'show_storyline_anyway': user.show_storyline_anyway,
                            'play_continuously': user.play_continuously
                        }
                        error_message = None
                    else:
                        data = {}
                        error_message = "Not logged in"

            except SQLAlchemyError as e:
                error_message = f"The operation for user: '{username}' failed because of an error: {e}"
                logging.error(error_message)

            return {"result": result, "data": data, "error": error_message}

        # If the lock failed
        return {"result": result, "data": data, "error": error_message}


    def _get_user_data_with_password(self, username):
        """SQLAlchemy version of _get_user_data_with_password"""
        data = {}

        try:
            with self.get_sqlalchemy_session() as session:
                user = session.query(User).filter(User.name == username).first()

                if user:
                    data = {
                        'id': user.id,
                        'password': user.password,
                        'is_admin': user.is_admin,
                        'name': user.name,
                        'language_code': user.language.name if user.language else None,
                        'language_id': user.id_language,
                        'descriptor_color': user.descriptor_color,
                        'show_original_title': user.show_original_title,
                        'show_lyrics_anyway': user.show_lyrics_anyway,
                        'show_storyline_anyway': user.show_storyline_anyway,
                        'play_continuously': user.play_continuously
                    }

        except SQLAlchemyError as e:
            logging.error(f"The SELECTION in the database for user: '{username}' failed because of an error: {e}")

        return data


    def update_user_data(self, password=None, language_code=None, descriptor_color=None, show_original_title=None, show_lyrics_anyway=None, show_storyline_anyway=None, play_continuously=None, history_days=None):
        """SQLAlchemy version of update_user_data"""
        result = False
        data = {}
        error_message = "Lock error"

        user_data = session.get('logged_in_user', None)
        if user_data:
            username = user_data['username']
        else:
            return {'result': result, 'data': data, 'error': 'Not logged in'}

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as session:
                    user = session.query(User).filter(User.name == username).first()

                    if not user:
                        error_message = f"The requested username({username}) does NOT exist"
                        return {"result": result, "data": data, "error": error_message}

                    # Update fields if provided
                    if language_code:
                        language = session.query(Language).filter(Language.name == language_code).first()
                        if not language:
                            error_message = f"The requested language_code({language_code}) does NOT exist"
                            return {"result": result, "data": data, "error": error_message}
                        user.id_language = language.id

                    if password is not None:
                        user.password = generate_password_hash(password)

                    if descriptor_color is not None:
                        user.descriptor_color = descriptor_color

                    if show_original_title is not None:
                        user.show_original_title = show_original_title

                    if show_lyrics_anyway is not None:
                        user.show_lyrics_anyway = show_lyrics_anyway

                    if show_storyline_anyway is not None:
                        user.show_storyline_anyway = show_storyline_anyway

                    if play_continuously is not None:
                        user.play_continuously = play_continuously

                    if history_days is not None:
                        user.history_days = history_days

                    session.commit()
                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"The User update for user: '{username}' failed because of an error: {e}"
                logging.error(error_message)

            return {"result": result, "data": data, "error": error_message}

        # If the lock failed
        return {"result": result, "data": data, "error": error_message}


    def update_rating(self, card_id, rate=None, skip_continuous_play=None):
        """Update or create rating for a card with SQLAlchemy"""
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
                with self.get_sqlalchemy_session() as db_session:
                    # Check if rating exists
                    rating_record = db_session.query(Rating).filter(
                        Rating.id_user == user_id,
                        Rating.id_card == card_id
                    ).first()

                    # Create new rating
                    if not rating_record:
                        logging.debug(f"New rating record needed for card: {card_id} by user: {username}. RATE: {rate}, SKIP: {skip_continuous_play}")

                        if rate is None:
                            rate = 0
                        if skip_continuous_play is None:
                            skip_continuous_play = 1

                        new_rating = Rating(
                            id_card=card_id,
                            id_user=user_id,
                            rate=rate,
                            skip_continuous_play=skip_continuous_play
                        )

                        db_session.add(new_rating)
                        db_session.commit()

                    # Update existing rating
                    else:
                        logging.debug(f"Rating updates for card: {card_id} by user: {username}. RATE: {rate}, SKIP: {skip_continuous_play}")

                        if rate is not None:
                            rating_record.rate = rate
                        if skip_continuous_play is not None:
                            rating_record.skip_continuous_play = skip_continuous_play

                        db_session.commit()

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"Rating set for card: {card_id} by user: {username}. RATE: {rate}, SKIP: {skip_continuous_play} failed! {e}"
                logging.error(error_message)

            return {"result": result, "data": data, "error": error_message}

        return {"result": result, "data": data, "error": error_message}


    def insert_tag(self, card_id, name):
        """Insert a new tag for a card with SQLAlchemy"""
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
                with self.get_sqlalchemy_session() as db_session:
                    # Check if tag already exists
                    existing_tag = db_session.query(Tag).filter(
                        Tag.id_user == user_id,
                        Tag.id_card == card_id,
                        Tag.name == name
                    ).first()

                    if not existing_tag:
                        logging.debug(f"Record '{name}' tag for card: {card_id} by user: {username}")

                        new_tag = Tag(
                            id_card=card_id,
                            id_user=user_id,
                            name=name
                        )

                        db_session.add(new_tag)
                        db_session.commit()

                        data["id_card"] = card_id
                        data["username"] = username
                        data["name"] = name

                        result = True
                        error_message = None
                    else:
                        error_message = "The tag already exist"

            except SQLAlchemyError as e:
                error_message = f"Tagging the card: {card_id} by user: {username} with '{name}' tag failed!\n{e}"
                logging.error(error_message)

            return {"result": result, "data": data, "error": error_message}

        return {"result": result, "data": data, "error": error_message}

    def delete_tag(self, card_id, name):
        """Delete a tag from a card with SQLAlchemy"""
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
                with self.get_sqlalchemy_session() as db_session:
                    # Find and delete the tag
                    tag_to_delete = db_session.query(Tag).filter(
                        Tag.id_user == user_id,
                        Tag.id_card == card_id,
                        Tag.name == name
                    ).first()

                    if tag_to_delete:
                        logging.debug(f"Tag is about removed from card: {card_id} by user: {username}. Tag: '{name}'")

                        db_session.delete(tag_to_delete)
                        db_session.commit()

                        data["id_card"] = card_id
                        data["username"] = username
                        data["name"] = name

                        result = True
                        error_message = None
                    else:
                        error_message = "The tag does not exist"

            except SQLAlchemyError as e:
                error_message = f"Deleting the '{name}' tag from the card: {card_id} by user: {username} failed! {e}"
                logging.error(error_message)

            return {"result": result, "data": data, "error": error_message}

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


    def get_sql_where_condition_from_text_filter(self, text_filter, field_name, start_separator=',', end_separator=','):
        # LEGACY: the separator parameters needed because of some fields, like 'actors' and 'voices' have role, separated by :
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


    def get_converted_query_to_json(self, sql_record_list, category, lang):
        """
        Convert and translate the given SQL card-response
        """

        records = [{key: record[key] for key in record.keys()} for record in sql_record_list]

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
        """SQLAlchemy version of login"""
        error = 'Login failed'
        result = False
        data = {}

        # Login without credentials - session restoration
        if (username is None and password is None) or (not username and not password):
            if session.get('logged_in_user'):
                if 'logged_in_user' in session and 'username' in session['logged_in_user']:
                    username = session['logged_in_user']['username']
                    data = self._get_publishable_user_data(username)
                    if data:
                        result = True
                        error = None
            return {'result': result, 'data':data, 'error': error}

        # LOGIN means a LOGOUT before
        self.logout()

        try:
            with self.get_sqlalchemy_session() as db_session:
                user = db_session.query(User).filter(User.name == username).first()

                if user and check_password_hash(user.password, password):
                    # Get publishable user data
                    publishable_data = {
                        'is_admin': user.is_admin,
                        'name': user.name,
                        'language_code': user.language.name if user.language else None,
                        'descriptor_color': user.descriptor_color,
                        'show_original_title': user.show_original_title,
                        'show_lyrics_anyway': user.show_lyrics_anyway,
                        'show_storyline_anyway': user.show_storyline_anyway,
                        'play_continuously': user.play_continuously
                    }

                    if publishable_data:
                        result = True
                        data = publishable_data
                        error = None

                        # make the session permanent
                        session.permanent = True

                        # store the user session data
                        session['logged_in_user'] = {
                            'username': username,
                            'user_id': user.id,
                            'language_id': user.id_language
                        }

        except SQLAlchemyError as e:
            logging.error(f"SQLAlchemy login failed: {e}")

        return {'result': result, 'data':data, 'error': error}

    def _get_publishable_user_data(self, username):
        """SQLAlchemy version of _get_publishable_user_data"""
        data = {}

        try:
            with self.get_sqlalchemy_session() as session:
                user = session.query(User).filter(User.name == username).first()

                if user:
                    data = {
                        'is_admin': user.is_admin,
                        'name': user.name,
                        'language_code': user.language.name if user.language else None,
                        'descriptor_color': user.descriptor_color,
                        'show_original_title': user.show_original_title,
                        'show_lyrics_anyway': user.show_lyrics_anyway,
                        'show_storyline_anyway': user.show_storyline_anyway,
                        'play_continuously': user.play_continuously
                    }

        except SQLAlchemyError as e:
            logging.error(f"The SELECTION in the database for user: '{username}' failed because of an error: {e}")

        return data

    def logout(self):

        # remove the session
        session.pop('logged_in_user', None)
        return {'result': True, 'data':{}, 'error': None}

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
        """SQLAlchemy version of get_list_of_actors with caching"""
        cache_key = f"actors_{category}_{limit}_{json}"
        return self._get_cached_or_execute(
            cache_key, 1800,  # 30 minutes cache
            self._get_list_of_actors_uncached, category, limit, json
        )

    def _get_list_of_actors_uncached(self, category, limit=15, json=True):
        """Uncached version of get_list_of_actors"""
        result = False
        error_message = "Lock error"
        records = {}

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as session:
                    # Query for distinct actor names in media cards of given category
                    query = session.query(Person.name.label('actor_name')).distinct()\
                        .join(card_actor_table, Person.id == card_actor_table.c.id_actor)\
                        .join(Card, card_actor_table.c.id_card == Card.id)\
                        .join(Category, Card.id_category == Category.id)\
                        .filter(Category.name == category)\
                        .filter(
                            (Card.level == None) |
                            (Card.level == 'record') |
                            (Card.level == 'episode')
                        )\
                        .order_by(Person.name)\
                        .limit(limit)

                    records = query.all()

                    if json:
                        records = [record.actor_name for record in records]

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"Fetching the actor list failed: {e}"
                logging.error(error_message)

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
        """SQLAlchemy version of get_list_of_voices"""
        result = False
        error_message = "Lock error"
        records = {}

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as session:
                    # Query for distinct voice names in media cards of given category
                    query = session.query(Person.name.label('voice_name')).distinct()\
                        .join(card_voice_table, Person.id == card_voice_table.c.id_voice)\
                        .join(Card, card_voice_table.c.id_card == Card.id)\
                        .join(Category, Card.id_category == Category.id)\
                        .filter(Category.name == category)\
                        .filter(
                            (Card.level == None) |
                            (Card.level == 'record') |
                            (Card.level == 'episode')
                        )\
                        .order_by(Person.name)\
                        .limit(limit)

                    records = query.all()

                    if json:
                        records = [record.voice_name for record in records]

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"Fetching the voice list failed: {e}"
                logging.error(error_message)

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
        """SQLAlchemy version of get_list_of_directors with caching"""
        cache_key = f"directors_{category}_{limit}_{json}"
        return self._get_cached_or_execute(
            cache_key, 1800,  # 30 minutes cache
            self._get_list_of_directors_uncached, category, limit, json
        )

    def _get_list_of_directors_uncached(self, category, limit=15, json=True):
        """Uncached version of get_list_of_directors"""
        result = False
        error_message = "Lock error"
        records = {}

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as session:
                    # Query for distinct director names in media cards of given category
                    query = session.query(Person.name.label('director_name')).distinct()\
                        .join(card_director_table, Person.id == card_director_table.c.id_director)\
                        .join(Card, card_director_table.c.id_card == Card.id)\
                        .join(Category, Card.id_category == Category.id)\
                        .filter(Category.name == category)\
                        .filter(
                            (Card.level == None) |
                            (Card.level == 'record') |
                            (Card.level == 'episode')
                        )\
                        .order_by(Person.name)\
                        .limit(limit)

                    records = query.all()

                    if json:
                        records = [record.director_name for record in records]

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"Fetching the director list failed: {e}"
                logging.error(error_message)

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
        """SQLAlchemy version of get_list_of_writers with caching"""
        cache_key = f"writers_{category}_{limit}_{json}"
        return self._get_cached_or_execute(
            cache_key, 1800,  # 30 minutes cache
            self._get_list_of_writers_uncached, category, limit, json
        )

    def _get_list_of_writers_uncached(self, category, limit=15, json=True):
        """Uncached version of get_list_of_writers"""
        result = False
        error_message = "Lock error"
        records = {}

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as session:
                    # Query for distinct writer names in media cards of given category
                    query = session.query(Person.name.label('writer_name')).distinct()\
                        .join(card_writer_table, Person.id == card_writer_table.c.id_writer)\
                        .join(Card, card_writer_table.c.id_card == Card.id)\
                        .join(Category, Card.id_category == Category.id)\
                        .filter(Category.name == category)\
                        .filter(
                            (Card.level == None) |
                            (Card.level == 'record') |
                            (Card.level == 'episode')
                        )\
                        .order_by(Person.name)\
                        .limit(limit)

                    records = query.all()

                    if json:
                        records = [record.writer_name for record in records]

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"Fetching the writer list failed: {e}"
                logging.error(error_message)

        return {"result": result, "data": records, "error": error_message}


    def get_list_of_tags(self, category, limit=15, json=True):
        """SQLAlchemy version of get_list_of_tags"""
        result = False
        error_message = "Lock error"
        records = {}

        try:
            from flask import session as flask_session
            user_data = flask_session.get('logged_in_user', None)
            if user_data:
                user_id = user_data['user_id']
            else:
                user_id = -1
        except RuntimeError:
            # Working outside of request context - use default user_id
            user_id = -1

        with self.lock:
            try:
                with self.get_sqlalchemy_session() as db_session:
                    # Query for distinct tag names for given category and user
                    query = db_session.query(Tag.name.label('tag')).distinct()\
                        .join(Card, Tag.id_card == Card.id)\
                        .join(Category, Card.id_category == Category.id)\
                        .filter(Category.name == category)\
                        .filter(Tag.id_user == user_id)\
                        .order_by(Tag.name)\
                        .limit(limit)

                    records = query.all()

                    if json:
                        records = [record.tag for record in records]

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"Fetching the tag list failed: {e}"
                logging.error(error_message)

        return {"result": result, "data": records, "error": error_message}

    def get_abc_of_movie_title(self, category, maximum, lang):
        """Returns the list of the ABC of the movie titles on the highest level with caching"""
        cache_key = f"abc_titles_{category}_{lang}"
#        return self._get_cached_or_execute(
#            cache_key, 86400,  # 24 hours cache
#            self._get_abc_of_movie_title_uncached, category, maximum, lang
#        )
        self._get_abc_of_movie_title_uncached(category, maximum, lang)

    def _get_abc_of_movie_title_uncached(self, category, maximum, lang):
        """Uncached version of get_abc_of_movie_title"""
        result = True
        error_message = None

        trans = Translator.getInstance(lang)
        alphabet_string = trans.get_alphabet(case="upper")
        alphabet_list = list(alphabet_string)
        records = [{'name': letter, 'filter': letter + '%'} for letter in alphabet_list]
        records.insert(0, {"filter": "0%_OR_1%_OR_2%_OR_3%_OR_4%_OR_5%_OR_6%_OR_7%_OR_8%_OR_9%", "name": "0-9"})

        return {"result": result, "data": records, "error": error_message}


    #
    # GET /collect/highest/mixed
    #
    # ✅
    #
    def get_highest_level_cards(self, category, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
        """Returns highest level cards using raw SQL query for complex hierarchical operations with caching"""
        # Create cache key from all parameters that affect the result
        cache_params = f"{category}_{view_state}_{tags}_{level}_{filter_on}_{title}_{genres}_{themes}_{directors}_{writers}_{actors}_{voices}_{lecturers}_{performers}_{origins}_{rate_value}_{decade}_{lang}_{limit}_{json}"
        cache_key = f"highest_cards_{hash(cache_params) % 1000000}"

        return self._get_cached_or_execute(
            cache_key, 3600,  # 60 minutes cache for card queries
            self._get_highest_level_cards_uncached, category, view_state, tags, level, filter_on, title, genres, themes, directors, writers, actors, voices, lecturers, performers, origins, rate_value, decade, lang, limit, json
        )

    def _get_highest_level_cards_uncached(self, category, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
        """Uncached version of get_highest_level_cards"""
        records = []

        try:
            from flask import session as flask_session
            user_data = flask_session.get('logged_in_user', None)
            if user_data:
                user_id = user_data['user_id']
            else:
                user_id = -1
        except RuntimeError:
            user_id = -1

        with self.lock:

            try:

                cur = self.conn.cursor()

                query = self.get_raw_query_of_highest_level(
                    category=category, tags=tags, title=title, genres=genres,
                    themes=themes, directors=directors, writers=writers,
                    actors=actors, voices=voices, lecturers=lecturers,
                    performers=performers, origins=origins, rate_value=rate_value
                )

                query_parameters = {
                    'user_id': user_id, 'level': level, 'filter_on': filter_on,
                    'category': category, 'title': title, 'decade': decade,
                    'tags': tags, 'lang': lang, 'limit': limit
                }

                logging.debug(f"get_highest_level_cards query: '{query}' / {query_parameters}")

                records = cur.execute(query, query_parameters).fetchall()

                if json:
                    records = self.get_converted_query_to_json(records, category, lang)

            except sqlite3.Error as e:
                error_message = f"Fetching the highest level card failed: {e}"
                logging.error(error_message)
                records = []

            finally:
                cur.close()
                return records

        return records


    #
    # /collect/next/mixed/
    #
    # ✅
    def get_next_level_cards(self, card_id, category, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
        """Returns next level cards using raw SQL query for complex hierarchical operations with caching"""
        # Create cache key from all parameters that affect the result
        cache_params = f"{card_id}_{category}_{view_state}_{tags}_{level}_{filter_on}_{title}_{genres}_{themes}_{directors}_{writers}_{actors}_{voices}_{lecturers}_{performers}_{origins}_{rate_value}_{decade}_{lang}_{limit}_{json}"
        cache_key = f"next_cards_{hash(cache_params) % 1000000}"

        return self._get_cached_or_execute(
            cache_key, 3600,  # 60 minutes cache for card queries
            self._get_next_level_cards_uncached, card_id, category, view_state, tags, level, filter_on, title, genres, themes, directors, writers, actors, voices, lecturers, performers, origins, rate_value, decade, lang, limit, json
        )

    def _get_next_level_cards_uncached(self, card_id, category, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
        """Uncached version of get_next_level_cards"""
        records = []

        try:
            from flask import session as flask_session
            user_data = flask_session.get('logged_in_user', None)
            if user_data:
                user_id = user_data['user_id']
            else:
                user_id = -1
        except RuntimeError:
            user_id = -1

        with self.lock:
            try:
                cur = self.conn.cursor()

                query = self.get_raw_query_of_next_level(
                    category=category, tags=tags, level=level, filter_on=filter_on,
                    genres=genres, themes=themes, directors=directors, actors=actors,
                    voices=voices, lecturers=lecturers, performers=performers,
                    origins=origins, rate_value=rate_value
                )

                query_parameters = {
                    'user_id': user_id, 'card_id': card_id, 'category': category,
                    'level': level, 'filter_on': filter_on, 'title': title,
                    'decade': decade, 'lang': lang, 'limit': limit
                }

                logging.debug(f"get_next_level_cards query: '{query}' / {query_parameters}")

                records = cur.execute(query, query_parameters).fetchall()

                if json:
                    records = self.get_converted_query_to_json(records, category, lang)

            except sqlite3.Error as e:
                error_message = f"Fetching the next level card failed: {e}"
                logging.error(error_message)
                records = []

            finally:
                cur.close()
                return records

        return records


    #
    # GET /collect/lowest
    #
    # ✅
    def get_lowest_level_cards(self, category, view_state=None, tags=None, level=None, title=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
        """Returns lowest level cards using raw SQL query for complex hierarchical operations with caching"""
        # Create cache key from all parameters that affect the result
        cache_params = f"{category}_{view_state}_{tags}_{level}_{title}_{genres}_{themes}_{directors}_{actors}_{voices}_{lecturers}_{performers}_{origins}_{rate_value}_{decade}_{lang}_{limit}_{json}"
        cache_key = f"lowest_cards_{hash(cache_params) % 1000000}"

        return self._get_cached_or_execute(
            cache_key, 3600,  # 60 minutes cache for card queries
            self._get_lowest_level_cards_uncached, category, view_state, tags, level, title, genres, themes, directors, actors, voices, lecturers, performers, origins, rate_value, decade, lang, limit, json
        )

    def _get_lowest_level_cards_uncached(self, category, view_state=None, tags=None, level=None, title=None, genres=None, themes=None, directors=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=100, json=True):
        """Uncached version of get_lowest_level_cards"""
        records = []

        try:
            from flask import session as flask_session
            user_data = flask_session.get('logged_in_user', None)
            if user_data:
                user_id = user_data['user_id']
            else:
                user_id = -1
        except RuntimeError:
            user_id = -1

        with self.lock:
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                history_days = 365
                history_back = int(datetime.now().astimezone().timestamp()) - history_days * 86400

                query = self.get_raw_query_of_lowest_level(
                    category=category, tags=tags, genres=genres, themes=themes,
                    directors=directors, actors=actors, voices=voices,
                    lecturers=lecturers, performers=performers, origins=origins,
                    rate_value=rate_value
                )

                # Add view_state filtering and ordering
                query = f'''
                SELECT *
                FROM ({query}) raw_query
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
                ''' + (
                    'ORDER BY raw_query.start_epoch DESC' if view_state == 'interrupted' or view_state == 'last_watched'
                    else 'ORDER BY raw_query.play_count DESC' if view_state == 'most_watched'
                    else 'ORDER BY raw_query.ord'
                ) + '''
                LIMIT :limit;
                '''

                query_parameters = {
                    'user_id': user_id, 'category': category, 'level': level,
                    'view_state': view_state, 'history_back': history_back,
                    'title': title, 'decade': decade, 'lang': lang, 'limit': limit
                }

                logging.debug(f"get_lowest_level_cards_sqlalchemy query: '{query}' / {query_parameters}")

                records = cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")

                if json:
                    records = self.get_converted_query_to_json(records, category, lang)

            except sqlite3.Error as e:
                error_message = f"Fetching the lowest level card failed: {e}"
                logging.error(f'Error in SQLAlchemy version: {error_message}')
                records = []

            finally:
                cur.close()
                return records

        return records


    def get_history(self, card_id=None, limit_days=None, limit_records=None):
        """Get user's playback history with optional filtering"""
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
                with self.get_sqlalchemy_session() as db_session:
                    query = db_session.query(History).filter(History.id_user == user_id)

                    if card_id:
                        query = query.filter(History.id_card == card_id)

                    if limit_days:
                        limit_epoch = int((datetime.now() + timedelta(days=limit_days)).timestamp())
                        query = query.filter(History.start_epoch <= limit_epoch)

                    query = query.order_by(History.start_epoch.desc())

                    if limit_records:
                        query = query.limit(limit_records)

                    records = query.all()

                    data = [{
                        'start_epoch': record.start_epoch,
                        'recent_epoch': record.recent_epoch,
                        'recent_position': float(record.recent_position),
                        'id_card': record.id_card,
                        'id_user': record.id_user
                    } for record in records]

                    result = True
                    error_message = None

            except SQLAlchemyError as e:
                error_message = f"The operation for user: '{user_id}' failed because of an error: {e}"
                logging.error(error_message)

            return {"result": result, "data": data, "error": error_message}

        return {"result": result, "data": data, "error": error_message}


    def update_play_position(self, card_id, recent_position, start_epoch=None):
        """Update player's position for a movie with SQLAlchemy"""
        with self.lock:
            result = False
            data = {}
            error_message = "Lock error"

            try:
                user_data = session.get('logged_in_user')
                if user_data:
                    user_id = user_data["user_id"]
                else:
                    error_message = 'Not logged in'
                    return {"result": result, "data": data, "error": error_message}

                with self.get_sqlalchemy_session() as db_session:
                    # Verify user existence
                    user = db_session.query(User).filter(User.id == user_id).first()
                    if not user:
                        error_message = f"The requested user_id({user_id}) does NOT exist"
                        logging.error(error_message)
                        return {"result": result, "data": data, "error": error_message}

                    # Verify card existence
                    card = db_session.query(Card).filter(Card.id == card_id).first()
                    if not card:
                        error_message = f"The requested card_id({card_id}) does NOT exist"
                        logging.error(error_message)
                        return {"result": result, "data": data, "error": error_message}

                    # Check if history record exists
                    history_record = None
                    if start_epoch:
                        history_record = db_session.query(History).filter(
                            History.id_card == card_id,
                            History.id_user == user_id,
                            History.start_epoch == start_epoch
                        ).first()

                    # New history - INSERT
                    if not history_record and not start_epoch:
                        start_epoch = int(datetime.now().timestamp())
                        recent_epoch = start_epoch

                        new_history = History(
                            id_card=card_id,
                            id_user=user_id,
                            start_epoch=start_epoch,
                            recent_epoch=recent_epoch,
                            recent_position=recent_position
                        )

                        db_session.add(new_history)
                        db_session.commit()
                        logging.debug(f"The registered new history of card_id: {card_id} has 'start_epoch': {start_epoch}")

                    # Update existing history
                    elif history_record and start_epoch:
                        recent_epoch = int(datetime.now().timestamp())
                        history_record.recent_epoch = recent_epoch
                        history_record.recent_position = recent_position
                        db_session.commit()

                    # Something went wrong
                    else:
                        error_message = f"Something went wrong. The parameter 'start_epoch'={start_epoch} but history record exists: {bool(history_record)}"
                        logging.error(error_message)
                        return {"result": result, "data": data, "error": error_message}

                    result = True
                    data['start_epoch'] = int(start_epoch)
                    error_message = None

            except SQLAlchemyError as e:
                error_message = str(e)
                logging.error(error_message)

            return {"result": result, "data": data, "error": error_message}

        return {"result": result, "data": data, "error": error_message}




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
