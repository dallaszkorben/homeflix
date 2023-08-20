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
    TABLE_MEDIUM = "Medium"
    TABLE_CARD = "Card"
    TABLE_HIERARCHY = "Hierarchy"

    TABLE_CARD_GENRE = "Card_Genre"
    TABLE_CARD_THEME = "Card_Theme"
    TABLE_CARD_MEDIATYPE = "Card_MediaType"
    TABLE_CARD_SOUND = "Card_Sound"
    TABLE_CARD_SUB = "Card_Sub"
    TABLE_CARD_ORIGIN = "Card_Origin"
    TABLE_CARD_ACTOR = "Card_Actor"
    TABLE_CARD_WRITER = "Card_Writer"
    TABLE_CARD_DIRECTOR = "Card_Director"
    TABLE_CARD_VOICE = "Card_Voice"
    TABLE_TEXT_CARD_LANG = "Text_Card_Lang"
    TABLE_HIERARCHY_TITLE_LANG = "Hierarchy_Title_Lang"

    def __init__(self):
        config = getConfig()
        self.db_path = os.path.join(config["path"], config['card-db-name'])
        self.translator = Translator.getInstance("en")

        self.language = self.translator.get_actual_language_code()

        self.table_list = [
                SqlDatabase.TABLE_HIERARCHY_TITLE_LANG,
                SqlDatabase.TABLE_TEXT_CARD_LANG,
                SqlDatabase.TABLE_MEDIUM,
                SqlDatabase.TABLE_CARD_VOICE,
                SqlDatabase.TABLE_CARD_WRITER,
                SqlDatabase.TABLE_CARD_DIRECTOR,
                SqlDatabase.TABLE_CARD_ACTOR,
                SqlDatabase.TABLE_CARD_ORIGIN,
                SqlDatabase.TABLE_CARD_GENRE,
                SqlDatabase.TABLE_CARD_THEME,
                SqlDatabase.TABLE_CARD_SOUND,
                SqlDatabase.TABLE_CARD_SUB,
                SqlDatabase.TABLE_CARD_MEDIATYPE,

                SqlDatabase.TABLE_CARD,

                SqlDatabase.TABLE_COUNTRY,
                SqlDatabase.TABLE_LANGUAGE,

                SqlDatabase.TABLE_GENRE,
                SqlDatabase.TABLE_THEME,
                SqlDatabase.TABLE_PERSON,
                SqlDatabase.TABLE_MEDIATYPE,
                SqlDatabase.TABLE_CATEGORY,

                SqlDatabase.TABLE_HIERARCHY
            ]

        self.lock = Lock()

        # create connection
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
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
            CREATE TABLE ''' + SqlDatabase.TABLE_HIERARCHY + '''(
                id                  INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                level               TEXT       NOT NULL,
                id_higher_hierarchy INTEGER,
                id_title_orig       INTEGER    NOT NULL,
                id_category         INTEGER    NOT NULL,
                basename            TEXT       NOT NULL,
                source_path         TEXT       NOT NULL,
                sequence            INTEGER,
                FOREIGN KEY (id_category)     REFERENCES ''' + SqlDatabase.TABLE_CATEGORY + ''' (id),
                FOREIGN KEY (id_title_orig)   REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                FOREIGN KEY (id_higher_hierarchy) REFERENCES ''' + SqlDatabase.TABLE_HIERARCHY + ''' (id)
            );
        ''')

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
                date                TEXT        NOT NULL,
                length              TEXT,
                source_path         TEXT        NOT NULL,
                basename            TEXT        NOT NULL,
                sequence            INTEGER,
                id_higher_hierarchy INTEGER,
                level               TEXT,
                FOREIGN KEY (id_title_orig) REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                FOREIGN KEY (id_higher_hierarchy) REFERENCES ''' + SqlDatabase.TABLE_HIERARCHY + ''' (id) 
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
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_MEDIATYPE + '''(
                id_card INTEGER      NOT NULL,
                id_mediatype INTEGER      NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_mediatype) REFERENCES ''' + SqlDatabase.TABLE_MEDIATYPE + ''' (id),
                PRIMARY KEY (id_card, id_mediatype) 
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
            CREATE TABLE ''' + SqlDatabase.TABLE_HIERARCHY_TITLE_LANG + '''(
                text         TEXT     NOT NULL,
                id_language  INTEGER  NOT NULL,
                id_hierarchy INTEGER  NOT NULL,
                FOREIGN KEY (id_language)  REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id),
                FOREIGN KEY (id_hierarchy) REFERENCES ''' + SqlDatabase.TABLE_HIERARCHY + ''' (id),
                PRIMARY KEY (id_hierarchy, id_language)
            );
        ''' )

        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_MEDIUM + '''(
                name         TEXT     NOT NULL,
                id_card      INTEGER  NOT NULL,
                FOREIGN KEY (id_card)      REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id), 
                PRIMARY KEY (id_card, name)
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

    def append_card_movie(self, title_orig, titles={}, category=None, mediatypes={}, storylines={}, date=None, length=None, sounds=[], subs=[], genres=[], themes=[], origins=[], media=[], basename=None, source_path=None, sequence=None, higher_hierarchy_id=None):

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            title_orig_id = self.language_name_id_dict[title_orig]
            category_id = self.category_name_id_dict[category]

            #
            # INSERT into CARD
            #
            if higher_hierarchy_id:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                    (id_title_orig, id_category, date, length, basename, source_path, id_higher_hierarchy, sequence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    RETURNING id;
                '''
                cur.execute(query, (title_orig_id, category_id, date, length, basename, source_path, higher_hierarchy_id, sequence))
            else:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                    (id_title_orig, id_category, date, length, basename, source_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                    RETURNING id;
                '''
                cur.execute(query, (title_orig_id, category_id, date, length, basename, source_path))
            record = cur.fetchone()
            (card_id, ) = record if record else (None,)

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
            # INSERT into TABLE_CARD_MEDIATYPE
            #
            for mediatype in mediatypes:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_MEDIATYPE + '''
                    (id_mediatype, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.mediatype_name_id_dict[mediatype], card_id))

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
            # INSERT into TABLE_MEDIUM
            #
            for medium in media:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_MEDIUM + '''
                    (name, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (medium, card_id))   

        except sqlite3.Error as e:
            logging.error("To append media failed with: '{0}' while inserting record".format(e))
            cur.execute("rollback")

        # close the insert transaction
        cur.execute("commit")

    def append_hierarchy(self, title_orig, titles, category, level, basename, source_path, sequence=None, higher_hierarchy_id=None):

        cur = self.conn.cursor()
        cur.execute("begin")

        try:

            category_id = self.category_name_id_dict[category]
            title_orig_id = self.language_name_id_dict[title_orig]

            #
            # INSERT into Level
            #
            if higher_hierarchy_id:                
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_HIERARCHY + '''
                    (level, id_title_orig, id_category, id_higher_hierarchy, basename, source_path, sequence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    RETURNING id;
                '''
                cur.execute(query, (level, title_orig_id, category_id, higher_hierarchy_id, basename, source_path, sequence))
            else:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_HIERARCHY + '''
                    (level, id_title_orig, id_category, basename, source_path, sequence)
                    VALUES (?, ?, ?, ?, ?, ?)
                    RETURNING id;
                '''
                cur.execute(query, (level, title_orig_id, category_id, basename, source_path, sequence))
            record = cur.fetchone()
            (hierarchy_id, ) = record if record else (None,)

            #
            # INSERT into TABLE_HIERARCHY_TITLE_LANG
            #
            for lang, title in titles.items():
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_HIERARCHY_TITLE_LANG + '''
                    (id_language, id_hierarchy, text)
                    VALUES (?, ?, ?);
                '''
                cur.execute(query, (self.language_name_id_dict[lang], hierarchy_id, title))    

        except sqlite3.Error as e:
            logging.error("To append hierarchy failed with: '{0}' while inserting record. Level: {1}".format(e, level))
            cur.execute("rollback")

        cur.execute("commit")
        return hierarchy_id

    # === requests ===


    # def get_all_series_fast(self, lang):
    #     """
    #     It returns the series id, title on the requested language, or if it does not exist then the title on the original language
    #     Return fields:
    #         id:         series ID
    #         title:      title
    #         source_path:source path to the series
    #         lang:       language of the title
    #         orig,       original language
    #     """
    #     cur = self.conn.cursor()
    #     cur.execute("begin")

    #     return_records = {}

    #     # Get Card list
    #     query = '''
    #         SELECT 
    #             level.id id, 
    #             ltl.text title, 
    #             level.source_path source_path, 
    #             lang.name lang, 
    #             orig.name orig,
    #             ROW_NUMBER() OVER (
    #                 PARTITION BY level.id 
    #                 ORDER BY 
    #                     CASE 
    #                         WHEN lang.name=? THEN 0 
    #                         WHEN lang.name=orig.name THEN 1 
    #                         ELSE 2 END, text
    #                 ) AS rn
    #         FROM 
    #             ''' + SqlDatabase.TABLE_HIERARCHY + ''' hierarchy, 
    #             ''' + SqlDatabase.TABLE_HIERARCHY_TITLE_LANG + ''' ltl, 
    #             ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang, 
    #             ''' + SqlDatabase.TABLE_LANGUAGE + ''' orig
    #         WHERE 
    #             level.name='series' AND
    #             ltl.id_level=level.id AND
    #             ltl.id_language=lang.id AND
    #             level.id_title_orig=orig.id AND
    #             (lang.name=? OR level.id_title_orig=lang.id)
    #         GROUP BY level.id                
    #     '''
    #     return_records=cur.execute(query, (lang,lang)).fetchall()

    #     cur.execute("commit")

    #     return return_records



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


    def get_all_bands(self, lang, limit=100, json=True):
        return self.get_all_level('band', 'music', lang, limit, json)

    def get_all_series_of_movies(self, lang, limit=100, json=True):
        return self.get_all_series('movie', lang, limit, json)

    def get_all_series(self, category, lang, limit=100, json=True):
        return self.get_all_level('series', category, lang, limit, json)

    def get_all_level(self, level, category, lang, limit=100, json=True):
        """
        It returns a list of series with id, title on the required language and title on the original language.
        If the requested language is the original language, then only the title with requested language will be returned
        If the the title does not exist on the requested language, only the title with the original language will be returned
        Return fields:
            id:         series ID
            title_req:  tile on the requested language
            lang_req:   requested language
            title_orig: title on the original language
            lang_orig:  original language of the title
            source_path:source path to the series
        Example:
            records=db.get_all_level(level="series", category="movie", lang="it")
            for record in records:
                if record["title_req"]:
                    orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
                    print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
                else:
                    print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))
                print("              Source: {0}".format(record["source_path"]))
        Output:
            Id: 1, Title: (Original [en]) The IT Crowd
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek
            Id: 6, Title: (Original [hu]) Psyché és Nárcisz
                          Source: /media/akoel/vegyes/MEDIA/01.Movie/03.Series/PsycheEsNarcisz-1980
        """
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            # Get Card list
            query = '''
            SELECT 
                id, 
                MAX(title_req) title_req, 
                MAX(lang_req) lang_req, 
                MAX(title_orig) title_orig, 
                MAX(lang_orig) lang_orig,
                source_path
            FROM (
                SELECT 
                    hrchy.id id, 
                    NULL title_req, 
                    NULL lang_req, 
                    htl.text title_orig, 
                    lang.name lang_orig,
                    hrchy.source_path source_path,
                    hrchy.sequence sequence,
                    hrchy.basename
                FROM 
                    ''' + SqlDatabase.TABLE_HIERARCHY + ''' hrchy, 
                    ''' + SqlDatabase.TABLE_HIERARCHY_TITLE_LANG + ''' htl,
                    ''' + SqlDatabase.TABLE_CATEGORY + ''' cat,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    hrchy.level=:level AND
                    hrchy.id_category=cat.id AND
                    cat.name=:category AND
                    htl.id_hierarchy=hrchy.id AND
                    htl.id_language=lang.id AND
                    hrchy.id_title_orig=lang.id AND
                    lang.name <> :lang

                UNION

                SELECT 
                    hrchy.id id, 
                    htl.text title_req, 
                    lang.name lang_req, 
                    NULL title_orig, 
                    NULL lang_orig,
                    hrchy.source_path source_path,
                    hrchy.sequence sequence,
                    hrchy.basename
                FROM 
                    ''' + SqlDatabase.TABLE_HIERARCHY + ''' hrchy, 
                    ''' + SqlDatabase.TABLE_HIERARCHY_TITLE_LANG + ''' htl,
                    ''' + SqlDatabase.TABLE_CATEGORY + ''' cat,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    hrchy.level=:level AND
                    hrchy.id_category=cat.id AND
                    cat.name=:category AND
                    htl.id_hierarchy=hrchy.id AND
                    htl.id_language=lang.id AND
                    lang.name=:lang
            )
            GROUP BY id
            ORDER BY CASE 
                WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
                WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
                WHEN sequence<0 THEN basename
                WHEN sequence>=0 THEN sequence
            END
            LIMIT :limit;
            '''
            records=cur.execute(query, {'level': level, 'category': category, 'lang':lang, 'limit':limit}).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]
        
            return records


    def get_child_hierarchy_or_card(self, hierarchy_id, lang, json=True):
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
            SELECT id, level, title_req, title_orig, sequence, source_path
            FROM (
                SELECT id, level, MAX(title_req) title_req, MAX(title_orig) title_orig, sequence, basename, source_path
                FROM (
                    SELECT hrchy.id id, hrchy.level level, NULL title_req, htl.text title_orig, sequence, basename, source_path
                    FROM 
                        Hierarchy hrchy, 
                        Hierarchy_Title_Lang htl,
                        Category cat,
                        Language lang
                    WHERE
                        hrchy.id_higher_hierarchy=:hierarchy_id AND
                        htl.id_hierarchy=hrchy.id AND
                        htl.id_language=lang.id AND
                        hrchy.id_title_orig=lang.id AND
                        hrchy.id_category=cat.id AND
                        lang.name <> :lang

                    UNION

                    SELECT hrchy.id id, hrchy.level level, htl.text title_req, NULL title_orig, sequence, basename, source_path
                    FROM 
                        Hierarchy hrchy, 
                        Hierarchy_Title_Lang htl, 
                        Category cat,
                        Language lang 
                    WHERE
                        hrchy.id_higher_hierarchy=:hierarchy_id AND
                        htl.id_hierarchy=hrchy.id AND
                        htl.id_language=lang.id AND
                        hrchy.id_category=cat.id AND
                        lang.name=:lang
                )
                GROUP BY id

                UNION

                SELECT id, NULL level, MAX(title_req) title_req, MAX(title_orig) title_orig, sequence, basename, source_path
                FROM (
                    SELECT card.id id, NULL title_req, tcl.text title_orig, sequence, basename, source_path
                    FROM 
                        Card card, 
                        Text_Card_Lang tcl, 
                        Category cat,
                        Language lang
                    WHERE
                        card.id_higher_hierarchy=:hierarchy_id AND
                        tcl.id_card=card.id AND
                        tcl.id_language=lang.id AND
                        tcl.type="T" AND
                        card.id_title_orig=lang.id AND
                        lang.name <> :lang

                    UNION

                    SELECT card.id id, tcl.text title_req, NULL title_orig, sequence, basename, source_path
                    FROM 
                        Card card, 
                        Text_Card_Lang tcl, 
                        Category cat,
                        Language lang 
                    WHERE
                        card.id_higher_hierarchy=:hierarchy_id AND
                        tcl.id_card=card.id AND
                        tcl.id_language=lang.id AND
                        tcl.type="T" AND                       
                        lang.name=:lang
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
            records=cur.execute(query, {'hierarchy_id': hierarchy_id, 'lang':lang}).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

            return records


#    def get_card_




    def get_standalone_movies_by_genre(self, genre, lang, limit=100, json=True):

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
                    ''' + SqlDatabase.TABLE_GENRE + ''' genre, 
                    ''' + SqlDatabase.TABLE_CARD_GENRE + ''' cg, 

                    ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                    ''' + SqlDatabase.TABLE_CATEGORY + ''' cat,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    card.id_higher_hierarchy IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND

                    cg.id_card=card.id AND
                    cg.id_genre=genre.id AND
                    genre.name=:genre AND

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
                    ''' + SqlDatabase.TABLE_GENRE + ''' genre, 
                    ''' + SqlDatabase.TABLE_CARD_GENRE + ''' cg, 

                    ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' tcl, 
                    ''' + SqlDatabase.TABLE_CATEGORY + ''' cat,
                    ''' + SqlDatabase.TABLE_LANGUAGE + ''' lang
                WHERE
                    card.id_higher_hierarchy IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND

                    cg.id_card=card.id AND
                    cg.id_genre=genre.id AND
                    genre.name=:genre AND

                    --card.id_title_orig=lang.id AND
                    card.id_category=cat.id AND
                    cat.name = :category AND
                    lang.name=:lang)
            GROUP BY id
            ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
            LIMIT :limit;
            '''
            records=cur.execute(query, {'category': 'movie', 'genre': genre, 'lang':lang, 'limit':limit}).fetchall()
            cur.execute("commit")

            if json:
                records = [{key: record[key] for key in record.keys()} for record in records]

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
                    card.id_higher_hierarchy IS NULL AND
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
                    card.id_higher_hierarchy IS NULL AND
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
            card_id:    card ID
            file_name:  name of the media file
        Example:
            records=db.get_mediaum_path_list(card_id=33, limit=100)
        Output:
            [{"card_id": 33, "file_name": "PsycheEsNarcisz-1-1980.m4v"}] 
        """
        with self.lock:

            cur = self.conn.cursor()
            cur.execute("begin")

            records = {}

            query = '''
                SELECT 
                    card.id card_id, 
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








    # # should filter like by series/category/genre
    # def get_all_cards(self):

    #     cur = self.conn.cursor()
    #     cur.execute("begin")

    #     return_records = {}

    #     # Get Card list
    #     query = '''SELECT card.*, category.name as c_name, title_orig.name as t_name
    #     FROM ''' + SqlDatabase.TABLE_CARD + ''' card, ''' + SqlDatabase.TABLE_CATEGORY + ''' category, ''' + SqlDatabase.TABLE_LANGUAGE + ''' title_orig 
    #     WHERE card.id_category=category.id AND card.id_title_orig=title_orig.id;'''
    #     records=cur.execute(query).fetchall()

    #     for record in records:
    #         card_id = record['id']

    #         category = record['c_name']
    #         source_path = record['source_path']
    #         date = record['date']
    #         length = record['length']
    #         title_orig_name = record['t_name']
            
    #         # Get Sound list
    #         sound_long_list = []
    #         query = '''
    #             SELECT sound.name 
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' sound, ''' + SqlDatabase.TABLE_CARD_SOUND + ''' cs 
    #             WHERE card.id=? AND cs.id_card=card.id AND cs.id_sound=sound.id '''
    #         for row in cur.execute(query, (card_id,)).fetchall():
    #             sound_long_list.append(self.translator.translate_language_long(row[0]))

    #         # Get Sub list
    #         sub_long_list = []
    #         query = '''
    #             SELECT sub.name 
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' sub, ''' + SqlDatabase.TABLE_CARD_SUB + ''' cs 
    #             WHERE card.id=? AND cs.id_card=card.id AND cs.id_sub=sub.id '''
    #         for row in cur.execute(query, (card_id,)).fetchall():
    #             sub_long_list.append(self.translator.translate_language_long(row[0]))

    #         # Get Genre list
    #         genre_list = []
    #         query = '''
    #             SELECT genre.name 
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_GENRE + ''' genre, ''' + SqlDatabase.TABLE_CARD_GENRE + ''' cg 
    #             WHERE card.id=? AND cg.id_card=card.id AND cg.id_genre=genre.id '''
    #         for row in cur.execute(query, (card_id,)).fetchall():
    #             genre_list.append(self.translator.translate_genre('movie', row[0]))

    #         # Get Theme list
    #         theme_list = []
    #         query = '''
    #             SELECT theme.name 
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_THEME + ''' theme, ''' + SqlDatabase.TABLE_CARD_THEME + ''' ct
    #             WHERE card.id=? AND ct.id_card=card.id AND ct.id_theme=theme.id '''
    #         for row in cur.execute(query, (card_id,)).fetchall():
    #             theme_list.append(self.translator.translate_theme(row[0]))

    #         # Get MediaType list
    #         mediatype_list = []
    #         query = '''
    #             SELECT mediatype.name 
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_MEDIATYPE + ''' mediatype, ''' + SqlDatabase.TABLE_CARD_MEDIATYPE + ''' cmt
    #             WHERE card.id=? AND cmt.id_card=card.id AND cmt.id_mediatype=mediatype.id '''
    #         for row in cur.execute(query, (card_id,)).fetchall():
    #             mediatype_list.append(self.translator.translate_mediatype(row[0]))

    #         # Get Origin list
    #         origin_long_list = []
    #         query = '''
    #             SELECT origin.name 
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_COUNTRY + ''' origin, ''' + SqlDatabase.TABLE_CARD_ORIGIN + ''' co
    #             WHERE card.id=? AND co.id_card=card.id AND co.id_origin=origin.id '''
    #         for row in cur.execute(query, (card_id,)).fetchall():
    #             origin_long_list.append(self.translator.translate_country_long(row[0]))

    #         # Get Original Title
    #         original_title = ""
    #         if title_orig_name != self.language:
    #             query = '''
    #                 SELECT title.text
    #                 FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' language, ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' title
    #                 WHERE card.id=? AND title.id_card=card.id AND title.id_language=language.id AND title.type=? AND language.name=?'''
    #             row = cur.execute(query, (card_id, "T", title_orig_name)).fetchone()
    #             original_title = row[0]

    #         # Get Title
    #         title = ""
    #         query = '''
    #             SELECT title.text
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' language, ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' title
    #             WHERE card.id=? AND title.id_card=card.id AND title.id_language=language.id AND title.type=? AND language.name=?'''
    #         row = cur.execute(query, (card_id, "T", self.language)).fetchone()
    #         if row is not None:
    #             title = row[0]
    #         else:
    #             title = original_title



    #         # Get Storyline
    #         storyline = ""
    #         query = '''
    #             SELECT storyline.text
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' language, ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' storyline
    #             WHERE card.id=? AND storyline.id_card=card.id AND storyline.id_language=language.id AND storyline.type=? AND language.name=?'''
    #         row = cur.execute(query, (card_id, "S", self.language)).fetchone()
    #         if row is not None:
    #             storyline = row[0]

    #         # Get media list
    #         media_list = []
    #         query = '''
    #             SELECT name
    #             FROM ''' + SqlDatabase.TABLE_CARD + ''' card, ''' + SqlDatabase.TABLE_MEDIUM + ''' medium
    #             WHERE card.id=? AND medium.id_card=card.id'''
    #         for row in cur.execute(query, (card_id,)).fetchall():
    #             media_list.append(row[0])

    #         return_records[card_id] = {}
    #         return_records[card_id]['category'] = category
    #         return_records[card_id]['date'] = date
    #         return_records[card_id]['length'] = length
    #         return_records[card_id]['original_title'] = original_title
    #         return_records[card_id]['title'] = title
    #         return_records[card_id]['storyline'] = storyline

    #         return_records[card_id]['sounds'] = sound_long_list
    #         return_records[card_id]['subs'] = sub_long_list
    #         return_records[card_id]['genres'] = genre_list
    #         return_records[card_id]['themes'] = theme_list
    #         return_records[card_id]['origins'] = origin_long_list          
    #         return_records[card_id]['mediatypes'] = mediatype_list
    #         return_records[card_id]['media'] = media_list
    #         return_records[card_id]['source_path'] = source_path

    #         # return_records[card_id]['level'] = level
    #         # return_records[card_id]['sequence'] = sequence

    #     # close the insert transaction
    #     cur.execute("commit")

    #     return return_records
