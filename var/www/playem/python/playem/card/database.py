import os
import sqlite3
import logging
from threading import Lock
from sqlite3 import Error

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
    TABLE_TEXT_CARD_LANG = "Text_Card_Lang"

    def __init__(self):
        config = getConfig()
        self.db_path = os.path.join(config["path"], config['card-db-name'])
        self.translator = Translator.getInstance("en")

        self.language = self.translator.get_actual_language_code()

        self.table_list = [
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

        # check if the databases are correct
        if not self.is_dbs_ok():            
            self.recreate_dbs()

        self.fill_up_constant_dicts()

    def __del__(self):
        self.conn.close()

    def is_dbs_ok(self):
        error_code = 1001
        cur = self.conn.cursor()
        cur.execute("begin")        

        try:
            for table in self.table_list:
                query ="SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{0}' ".format(table)
                records = cur.execute(query).fetchone()                
                if records[0] != 1:
                    raise NotExistingTable("{0} table does not exist. All tables must be recreated".format(table), error_code)

        except NotExistingTable as e:
            logging.debug(e.message)            
            return False

        finally:
            cur.execute("commit")
        return True

    def recreate_dbs(self):
        self.drop_all_existing_tables()
        logging.debug("All tables are dropped")            
        self.create_tables()
        logging.debug("All tables are recreated")            

    def drop_all_existing_tables(self):
        cur = self.conn.cursor()
        cur.execute("begin")    
        tables = list(cur.execute("SELECT name FROM sqlite_master WHERE type is 'table'"))
        cur.execute("commit")

        for table in tables:
            try:
                self.conn.execute("DROP TABLE {0}".format(table[0]))
            except sqlite3.OperationalError as e:
                print(e)

    def drop_tables(self):

        for table in self.table_list:
            try:
                self.conn.execute("DROP TABLE {0};".format(table))
            except sqlite3.OperationalError as e:
                logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(table, e))

#        self.conn.create_function('translate_method', 2, translate)

    def create_tables(self):

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
                decade              TEXT,
                date                TEXT,
                length              TEXT,
                source_path         TEXT        NOT NULL,
                basename            TEXT        NOT NULL,
                sequence            INTEGER,
                id_higher_card      INTEGER,
                level               TEXT,
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
                id_card  INTEGER       NOT NULL,
                id_actor INTEGER       NOT NULL,
                FOREIGN KEY (id_card)  REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_actor) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_actor) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_STAR + '''(
                id_card  INTEGER       NOT NULL,
                id_star INTEGER       NOT NULL,
                FOREIGN KEY (id_card)  REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_star) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_star) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_VOICE + '''(
                id_card  INTEGER       NOT NULL,
                id_voice INTEGER       NOT NULL,
                FOREIGN KEY (id_card)  REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_voice) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_voice) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_DIRECTOR + '''(
                id_card  INTEGER          NOT NULL,
                id_director INTEGER       NOT NULL,
                FOREIGN KEY (id_card)     REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_director) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_director) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_WRITER + '''(
                id_card   INTEGER        NOT NULL,
                id_writer INTEGER        NOT NULL,
                FOREIGN KEY (id_card)    REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_writer)  REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_writer) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_HOST + '''(
                id_card   INTEGER        NOT NULL,
                id_host INTEGER          NOT NULL,
                FOREIGN KEY (id_card)    REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_host)    REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_host) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_GUEST + '''(
                id_card   INTEGER        NOT NULL,
                id_guest INTEGER         NOT NULL,
                FOREIGN KEY (id_card)    REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_guest)   REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_guest) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_INTERVIEWER + '''(
                id_card   INTEGER            NOT NULL,
                id_interviewer INTEGER       NOT NULL,
                FOREIGN KEY (id_card)        REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_interviewer) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_interviewer) 
            );
        ''')

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_INTERVIEWEE + '''(
                id_card   INTEGER            NOT NULL,
                id_interviewee INTEGER       NOT NULL,
                FOREIGN KEY (id_card)        REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_interviewee) REFERENCES ''' + SqlDatabase.TABLE_PERSON + ''' (id),
                PRIMARY KEY (id_card, id_interviewee) 
            );
        ''')


        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + '''(
                text         TEXT     NOT NULL,
                id_language  INTEGER  NOT NULL,
                id_card      INTEGER  NOT NULL,
                type         TEXT     NOT NULL,
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

    def append_card_movie(self, title_orig, titles={}, category=None, storylines={}, lyrics={}, decade=None, date=None, length=None, sounds=[], subs=[], genres=[], themes=[], origins=[], writers=[], actors=[], stars=[], directors=[], voices=[], hosts=[], guests=[], interviewers=[], interviewees=[], media={}, basename=None, source_path=None, sequence=None, higher_card_id=None):

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            title_orig_id = self.language_name_id_dict[title_orig]
            category_id = self.category_name_id_dict[category]

            #
            # INSERT into CARD
            #
            # if higher_card_id:             

            query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                    (id_title_orig, id_category, decade, date, length, basename, source_path, id_higher_card, sequence)
                    VALUES (:id_title_orig, :id_category, :decade, :date, :length, :basename, :source_path, :id_higher_card, :sequence)
                    RETURNING id;
            '''
            cur.execute(query, {'id_title_orig': title_orig_id, 'id_category': category_id, 'decade': decade, 'date': date, 'length': length, 'basename': basename, 'source_path': source_path, 'id_higher_card': higher_card_id, 'sequence': sequence})

            # else:
            #     query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
            #         (id_title_orig, id_category, decade, date, length, basename, source_path)
            #         VALUES (:id_title_orig, :id_category, :decade, :date, :length, :basename, :source_path)
            #         RETURNING id;
            #     '''
            #     cur.execute(query, {'id_title_orig': title_orig_id, 'id_category': category_id, 'decade': decade, 'date': date, 'length': length, 'basename': basename, 'source_path': source_path})
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
            for actor in actors:

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
            logging.error("To append media failed with: '{0}' while inserting record".format(e))
            cur.execute("rollback")

        # close the insert transaction
        cur.execute("commit")

    def append_hierarchy(self, title_orig, titles, date, decade, category, level, genres, themes, origins, basename, source_path, sequence=None, higher_card_id=None):

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            category_id = self.category_name_id_dict[category]
            title_orig_id = self.language_name_id_dict[title_orig]

            #
            # INSERT into Level
            #

            # if higher_card_id:

            query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                    (level, id_title_orig, date, decade, id_category, basename, source_path, id_higher_card, sequence)
                    VALUES (:level, :id_title_orig, :date, :decade, :id_category, :basename, :source_path, :id_higher_card, :sequence)
                    RETURNING id;
            '''
            cur.execute(query, {'level': level, 'id_title_orig': title_orig_id, 'date': date, 'decade': decade, 'id_category': category_id, 'basename': basename, 'source_path': source_path, 'id_higher_card': higher_card_id, 'sequence': sequence})
            # else:
            #     query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
            #         (level, id_title_orig, decade, id_category, basename, source_path, sequence)
            #         VALUES (:level, :id_title_orig, :decade, :id_category, :basename, :source_path, :sequence)
            #         RETURNING id;
            #     '''
            #     cur.execute(query, {'level': level, 'id_title_orig': title_orig_id, 'decade': decade, 'id_category': category_id, 'basename': basename, 'source_path': source_path, 'sequence': sequence})
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

        except sqlite3.Error as e:
            logging.error("To append hierarchy failed with: '{0}' while inserting record. Level: {1}".format(e, level))
            cur.execute("rollback")

        cur.execute("commit")

        #logging.error("TEST returns {0} with id: {1}".format(titles, hierarchy_id))
        return hierarchy_id


    # ================
    #
    # === requests ===
    #
    # ================


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
    def get_general_level(self, level, category, genre=None, theme=None, origin=None, not_origin=None, decade=None, lang='en', limit=100, json=True):
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
                   
                    MAX(title_req) title_req, 
                    MAX(lang_req) lang_req, 
                    MAX(title_orig) title_orig, 
                    MAX(lang_orig) lang_orig,
                    source_path
                FROM (
                    SELECT 
                        card.id id,
                        card.id_category id_category,
                        card.decade decade,
                        NULL title_req, 
                        NULL lang_req, 
                        htl.text title_orig, 
                        lang.name lang_orig,
                        card.source_path source_path,
                        card.sequence sequence,
                        card.basename
                    FROM

                        ''' + SqlDatabase.TABLE_CARD + ''' card,
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' htl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
                    WHERE
                        card.level=:level AND
                        htl.id_card=card.id AND
                        htl.id_language=lang.id AND
                        card.id_title_orig=lang.id AND
                        lang.name <> :lang 
    
                    UNION
    
                    SELECT 
                        card.id id,
                        card.id_category id_category,
                        card.decade decade,
                        htl.text title_req, 
                        lang.name lang_req, 
                        NULL title_orig, 
                        NULL lang_orig,
                        card.source_path source_path,
                        card.sequence sequence,
                        card.basename
                    FROM 

                        ''' + SqlDatabase.TABLE_CARD + ''' card,
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' htl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
                    WHERE
                        card.level=:level AND
                        htl.id_card=card.id AND
                        htl.id_language=lang.id AND
                        lang.name = :lang
                    ) merged,
            ''' + ('''
                    --- origin or not_origin ---
                    ''' + SqlDatabase.TABLE_COUNTRY + ''' country,
                    ''' + SqlDatabase.TABLE_CARD_ORIGIN + ''' co,                    
            ''' if origin or not_origin else '') + ('''

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
            ''' if origin or not_origin else '') + ('''
            
                    AND country.name = :origin
            ''' if origin else '') + ('''

                    AND country.name != :not_origin
            ''' if not_origin else '') +  ('''

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

            logging.debug("TEST query: '{0}'".format(query))

            records=cur.execute(query, {'level': level, 'decade': decade, 'category': category, 'genre': genre, 'theme': theme, 'origin': origin, 'not_origin': not_origin, 'lang': lang, 'limit':limit}).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]
        
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
            SELECT id, level, title_req, title_orig, lang_req, lang_orig, sequence, source_path, date
            FROM (
                --- all cards connected to higher card ---
                SELECT id, level level, MAX(title_req) title_req, MAX(title_orig) title_orig, MAX(lang_orig) lang_orig, MAX(lang_req) lang_req, sequence, basename, source_path, date
                FROM (

                    --- requested language not the original ---
                    SELECT 
                        card.id id, 
                        card.level level, 
                        NULL title_req,
                        NULL lang_req,
                        lang.name lang_orig,
                        tcl.text title_orig, 
                        sequence, 
                        basename, 
                        source_path,
                        date
                    FROM
                        ''' + SqlDatabase.TABLE_CARD + ''' card, 
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                    WHERE
                        card.id_higher_card=:higher_card_id AND
                        tcl.id_card=card.id AND
                        tcl.id_language=lang.id AND
                        tcl.type="T" AND
                        card.id_title_orig=lang.id AND
                        lang.name <> :lang

                    UNION    
                        
                    --- requested language is any existing language ---
                    SELECT 
                        card.id id, 
                        card.level level, 
                        tcl.text title_req,
                        lang.name lang_req, 
                        NULL title_orig,
                        NULL lang_orig,
                        sequence, 
                        basename, 
                        source_path,
                        date
                    FROM 
                        ''' + SqlDatabase.TABLE_CARD + ''' card, 
                        ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                        ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                    WHERE
                        card.id_higher_card=:higher_card_id AND
                        tcl.id_card=card.id AND
                        tcl.id_language=lang.id AND
                        tcl.type="T" AND                        
                        lang.name = :lang
                )
                GROUP BY id
            )
            ORDER BY CASE 
                WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
                WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
                WHEN sequence<0 THEN basename
                WHEN sequence>=0 THEN sequence
            END
            '''

            logging.debug("TEST query: '{0}'".format(query))

            records=cur.execute(query, {'higher_card_id': higher_card_id, 'lang':lang}).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

            return records


    #
    # --- Movie queries ---
    #
    def get_standalone_movies_by_genre(self, genre, lang, limit=100, json=True):
        return self.get_general_standalone(category='movie', genre=genre, lang=lang, limit=limit, json=json)

    # reviewed
    #
    #
    # Only for standalone media search
    #
    #
    def get_general_standalone(self, category, genre=None, theme=None, origin=None, not_origin=None, decade=None, lang='en', limit=100, json=True):
             
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            query = '''
            SELECT 
                merged.id, 
                MAX(title_req) title_req, 
                MAX(title_orig) title_orig, 
                MAX(lang_orig) lang_orig,
                MAX(lang_req) lang_req,
                source_path
            FROM (
                SELECT 
                    card.id id, 
                    card.id_category id_category,
                    NULL title_req, 
                    NULL lang_req, 
                    tcl.text title_orig, 
                    lang.name lang_orig,
                    card.source_path source_path,
                    card.decade decade
                FROM 
                    
                    ''' + SqlDatabase.TABLE_CARD + ''' card,
                    ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
                WHERE
                
                    card.id_higher_card IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND
                    card.level IS NULL AND

                    lang.name <> :lang

                UNION

                SELECT 
                    card.id id,
                    card.id_category id_category,
                    tcl.text title_req, 
                    lang.name lang_req, 
                    NULL title_orig, 
                    NULL lang_orig,
                    card.source_path source_path,
                    card.decade decade
                FROM 
               
                    ''' + SqlDatabase.TABLE_CARD + ''' card,
                    ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang                    
                WHERE
               
                    card.id_higher_card IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND
                    card.level IS NULL AND
 
                    lang.name=:lang
            ) merged,
            ''' + ('''
                    --- origin or not_origin ---
                    ''' + SqlDatabase.TABLE_COUNTRY + ''' country,
                    ''' + SqlDatabase.TABLE_CARD_ORIGIN + ''' co,
            ''' if origin or not_origin else '') + ('''

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
                    --- category --- 
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
            ''' if origin or not_origin else '') + ('''
            
                    AND country.name = :origin
            ''' if origin else '') + ('''

                    AND country.name != :not_origin
            ''' if not_origin else '') +  ('''

                    --- decade ---
                    AND merged.decade = :decade
            ''' if decade else '') +  '''

            GROUP BY merged.id
            ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
            LIMIT :limit;
            '''
            
            logging.debug("TEST query: '{0}'".format(query))

            records=cur.execute(query, {'category': category, 'decade': decade, 'genre': genre, 'theme': theme, 'origin': origin, 'not_origin': not_origin, 'lang': lang, 'limit': limit}).fetchall()
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

            return records




    # 
    #
    #
    # Detailed Card for any movie with card id
    #
    #

    # TODO: DB name should be replaced by variables

    def get_standalone_movie_by_card_id(self, card_id, lang, limit=100, json=True):
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
                medium,
                storyline,
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
                interviewees
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
                Card card,
                Category category
            WHERE
                card.id = :card_id  AND
                card.id_category = category.id

            LIMIT :limit;
            '''
            records=cur.execute(query, {'card_id': card_id, 'lang':lang, 'limit':limit}).fetchall()
            cur.execute("commit")

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
    # Detailed Card for any audio music with card id
    #
    #

    def get_standalone_music_audio_by_card_id(self, card_id, lang, limit=100, json=True):
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
                medium,
                lyrics,
                sounds,
                subs,
                origins,
                genres,                
---                themes,
---                directors,
                writers
---                voices,
---                stars,
---                actors
--                performer
            FROM
                (SELECT group_concat( mt.name || "=" || m.name) medium

                    FROM 
                        Card_Media m,
                        MediaType mt
                    WHERE
                        m.id_card= :card_id AND
                        m.id_mediatype = mt.id
                ),
            
                (SELECT group_concat(tcl.text) lyrics
                    FROM 
                        Text_Card_Lang tcl,
                        Language language
                    WHERE 
                        tcl.type = "L" AND
                        tcl.id_card = :card_id AND
                        tcl.id_language = language.id AND
                        language.name = :lang
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
                   
---                (SELECT group_concat(person.name) directors
---                    FROM 
---                        Person person,
---                        Card_Director cd
---                    WHERE 
---                        cd.id_director = person.id AND
---                        cd.id_card = :card_id
---                ),
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
                Card card,
                Category category
            WHERE
                card.id = :card_id  AND
                card.id_category = category.id

            LIMIT :limit;
            '''
            records=cur.execute(query, {'card_id': card_id, 'lang':lang, 'limit':limit}).fetchall()
            cur.execute("commit")

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

                # # Directors
                # directors_string = records[0]["directors"]
                # directors_list = []
                # if directors_string:
                #     directors_list = directors_string.split(',')
                # records[0]["directors"] = directors_list

                # # Stars
                # stars_string = records[0]["stars"]
                # stars_list = []
                # if stars_string:
                #     stars_list = stars_string.split(',')
                # records[0]["stars"] = stars_list

                # # Actors
                # actors_string = records[0]["actors"]
                # actors_list = []
                # if actors_string:
                #     actors_list = actors_string.split(',')
                # records[0]["actors"] = actors_list

                # # Voices
                # voices_string = records[0]["voices"]
                # voices_list = []
                # if voices_string:
                #     voices_list = voices_string.split(',')
                # records[0]["voices"] = voices_list

                # Genre
                genres_string = records[0]["genres"]
                genres_list = []
                if genres_string:
                    genres_list = genres_string.split(',')
                    genres_list = [trans.translate_genre(category=category, genre=genre) for genre in genres_list]
                records[0]["genres"] = genres_list

                # # Theme
                # themes_string = records[0]["themes"]
                # themes_list = []
                # if themes_string:
                #     themes_list = themes_string.split(',')
                #     themes_list = [trans.translate_theme(theme=theme) for theme in themes_list]
                # records[0]["themes"] = themes_list

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
    # Detailed Card for any video music with card id
    #
    #

    def get_standalone_music_video_by_card_id(self, card_id, lang, limit=100, json=True):
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
                medium,
                lyrics,
                sounds,
                subs,
                origins,
                genres,                
---                themes,
                directors,
                writers
---                voices,
---                stars,
---                actors
---                performer
            FROM
                (SELECT group_concat( mt.name || "=" || m.name) medium

                    FROM 
                        Card_Media m,
                        MediaType mt
                    WHERE
                        m.id_card= :card_id AND
                        m.id_mediatype = mt.id
                ),
            
                (SELECT group_concat(tcl.text) lyrics
                    FROM 
                        Text_Card_Lang tcl,
                        Language language
                    WHERE 
                        tcl.type = "L" AND
                        tcl.id_card = :card_id AND
                        tcl.id_language = language.id AND
                        language.name = :lang
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
                Card card,
                Category category
            WHERE
                card.id = :card_id  AND
                card.id_category = category.id

            LIMIT :limit;
            '''
            records=cur.execute(query, {'card_id': card_id, 'lang':lang, 'limit':limit}).fetchall()
            cur.execute("commit")

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

                # # Directors
                # directors_string = records[0]["directors"]
                # directors_list = []
                # if directors_string:
                #     directors_list = directors_string.split(',')
                # records[0]["directors"] = directors_list

                # # Stars
                # stars_string = records[0]["stars"]
                # stars_list = []
                # if stars_string:
                #     stars_list = stars_string.split(',')
                # records[0]["stars"] = stars_list

                # # Actors
                # actors_string = records[0]["actors"]
                # actors_list = []
                # if actors_string:
                #     actors_list = actors_string.split(',')
                # records[0]["actors"] = actors_list

                # Voices
                # voices_string = records[0]["voices"]
                # voices_list = []
                # if voices_string:
                #     voices_list = voices_string.split(',')
                # records[0]["voices"] = voices_list

                # Genre
                genres_string = records[0]["genres"]
                genres_list = []
                if genres_string:
                    genres_list = genres_string.split(',')
                    genres_list = [trans.translate_genre(category=category, genre=genre) for genre in genres_list]
                records[0]["genres"] = genres_list

                # # Theme
                # themes_string = records[0]["themes"]
                # themes_list = []
                # if themes_string:
                #     themes_list = themes_string.split(',')
                #     themes_list = [trans.translate_theme(theme=theme) for theme in themes_list]
                # records[0]["themes"] = themes_list

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























    def get_all_standalone_movies(self, lang, limit=100, json=True):
        """
        It returns a list of standalone movies with card id, title on the required language and title on the original language and the source path.
        If the requested language is the original language, then only the title with requested language will be returned
        If the the title does not exist on the requested language, only the title with the original language will be returned
        Return fields:
            id:         card ID
            title_req:  tile on the requested language
            lang_req:   requested language
            title_orig: title on the original language
            lang_orig:  original language of the title
            source_path:source path to the series
        Example:
            records=db.get_all_standalone_movie(lang=lang, limit=100)
            for record in records:
                if record["title_req"]:
                    orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
                    print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
                else:
                    print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))
                print("              Source: {0}".format(record["source_path"]))
        Output:
            Id: 1, Title: A kenguru 
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/01.Standalone/A.Kenguru-1976
            Id: 3, Title: Büvös vadász 
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/01.Standalone/Buvos.Vadasz-1994
            Id: 4, Title: Diorissimo 
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/01.Standalone/Diorissimo-1980
            Id: 5, Title: Eszkimó asszony fázik 
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/01.Standalone/EszkimoAsszonyFazik-1984
            Id: 2, Title: (Original [fr]) Le professionnel
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/01.Standalone/A.Profi-1981
            Id: 6, Title: Régi idők focija 
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/01.Standalone/RegiIdokFocija-1973
        """
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            # Get Card list
            query = '''
            SELECT 
                id, 
                MAX(text_req) title_req, 
                MAX(text_orig) title_orig, 
                MAX(lang_orig) lang_orig,
                source_path
            FROM (
                SELECT 
                    card.id id, 
                    NULL text_req, 
                    -- NULL lang_req, 
                    tcl.text text_orig, 
                    lang.name lang_orig,
                    card.source_path source_path
                FROM 
                    ''' + SqlDatabase.TABLE_CARD + ''' card, 
                    ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                    ''' + SqlDatabase.TABLE_CATEGORY + ''' cat,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    card.id_higher_card IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND
                    card.id_title_orig=lang.id AND
                    cat.name = :category AND
                    lang.name <> :lang

                UNION

                SELECT 
                    card.id id, 
                    tcl.text text_req, 
                    -- lang.name lang_req, 
                    NULL text_orig, 
                    NULL lang_orig,
                    card.source_path source_path
                FROM 
                    ''' + SqlDatabase.TABLE_CARD + ''' card, 
                    ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                    ''' + SqlDatabase.TABLE_CATEGORY + ''' cat,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    card.id_higher_card IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND
                    --card.id_title_orig=lang.id AND
                    card.id_category=cat.id AND
                    cat.name = :category AND
                    lang.name=:lang)
            GROUP BY id
            ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
            LIMIT :limit;
            '''
            records=cur.execute(query, {'category': 'movie', 'lang':lang, 'limit':limit}).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

            return records


    def get_medium_by_card_id(self, card_id, limit=100, json=True):
        """
        It returns a list of medium by the card id.
        Return fields:
            card_id:     card ID
            file_name:   name of the media file
            source_path: source path of the media file
        Example:
            records=db.get_mediaum_path_list(card_id=33, limit=100)
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
  






 