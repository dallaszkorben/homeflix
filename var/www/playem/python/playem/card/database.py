import os
import sqlite3
import logging
from sqlite3 import Error

from playem.config.config import getConfig
from playem.translator.translator import Translator

class SqlDatabase:

    TABLE_CATEGORY = "category"
    TABLE_PERSON = "person"
    TABLE_COUNTRY = "country"
    TABLE_LANGUAGE = "language"
    TABLE_GENRE = "genre"
    TABLE_THEME = "theme"
    TABLE_MTYPE = "mtype"
    TABLE_CARD = "card"
    TABLE_CARD_GENRE = "card_genre"
    TABLE_CARD_THEME = "card_theme"
    TABLE_CARD_MTYPE = "card_mtype"
    TABLE_CARD_SOUND = "card_sound"
    TABLE_CARD_SUB = "card_sub"
    TABLE_CARD_ORIGIN = "card_origin"
    TABLE_CARD_ACTOR = "card_actor"
    TABLE_CARD_WRITER = "card_writer"
    TABLE_CARD_DIRECTOR = "card_director"
    TABLE_CARD_VOICE = "card_voice"
    TABLE_TEXT_CARD_LANG = "text_card_lang"
    TABLE_MEDIUM = "medium"

    def __init__(self):
        config = getConfig()
        self.db_path = os.path.join(config["path"], config['card-db-name'])
        self.translator = Translator.getInstance("en")

        self.language = self.translator.get_actual_language_code()

        # create connection
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path)
            logging.debug( "Connection to {0} SQLite was successful".format(self.db_path))
            self.conn.row_factory = sqlite3.Row 
        except Error as e:
            logging.error( "Connection to {0} SQLite failed. Error: {1}".format(self.db_path, e))
            # TODO: handle this case
            exit()

        self.fill_up_constant_dicts()

    def delete_tables(self):

        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_TEXT_CARD_LANG + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_MEDIUM + ";")

        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_VOICE + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_WRITER + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_DIRECTOR + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_ACTOR + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_ORIGIN + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_GENRE + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_THEME + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_SOUND + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_SUB + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD_MTYPE + ";")

        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_TITLE_CARD + ";")

        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CARD + ";")

        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_COUNTRY + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_LANGUAGE + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_GENRE + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_THEME + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_PERSON + ";")
        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_MTYPE + ";")

        self.conn.execute("DELETE FROM " + SqlDatabase.TABLE_CATEGORY + ";")

    def drop_tables(self):

        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_TEXT_CARD_LANG + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_TEXT_CARD_LANG, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_MEDIUM + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_MEDIUM, e))

        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_WRITER + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_WRITER, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_DIRECTOR + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_DIRECTOR, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_VOICE + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_VOICE, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_ACTOR + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_ACTOR, e))

        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_ORIGIN + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_ORIGIN, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_GENRE + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_GENRE, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_THEME + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_THEME, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_SOUND + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_SOUND, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_SUB + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_SUB, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD_MTYPE + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD_MTYPE, e))



        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CARD + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CARD, e))




        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_COUNTRY + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_COUNTRY, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_LANGUAGE + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_LANGUAGE, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_GENRE + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_GENRE, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_THEME + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_THEME, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_PERSON + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_PERSON, e))
        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_MTYPE + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_MTYPE, e))

        try:
            self.conn.execute("DROP TABLE " + SqlDatabase.TABLE_CATEGORY + ";")
        except sqlite3.OperationalError as e:
            logging.error("Wanted to Drop '{0}' table, but error happened: {1}".format(SqlDatabase.TABLE_CATEGORY, e))

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
            CREATE TABLE ''' + SqlDatabase.TABLE_MTYPE + '''(
                id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                name  TEXT  NOT NULL,
                UNIQUE(name)
            );
        ''')




        self.conn.execute('''
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD + '''(
                id             INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL,
                id_title_orig  INTEGER     NOT NULL,
                id_category    INTEGER     NOT NULL,
                date           TEXT        NOT NULL,
                length         TEXT,
                source_path    TEXT        NOT NULL,
                FOREIGN KEY (id_title_orig) REFERENCES ''' + SqlDatabase.TABLE_LANGUAGE + ''' (id)
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
            CREATE TABLE ''' + SqlDatabase.TABLE_CARD_MTYPE + '''(
                id_card INTEGER      NOT NULL,
                id_mtype INTEGER      NOT NULL,
                FOREIGN KEY (id_card) REFERENCES ''' + SqlDatabase.TABLE_CARD + ''' (id),
                FOREIGN KEY (id_mtype) REFERENCES ''' + SqlDatabase.TABLE_MTYPE + ''' (id),
                PRIMARY KEY (id_card, id_mtype) 
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
        self.fill_up_mtype_table_from_dict()

    def fill_up_constant_dicts(self):
        self.category_name_id_dict = {}
        self.genre_name_id_dict = {}
        self.theme_name_id_dict = {}
        self.language_name_id_dict = {}
        self.country_name_id_dict = {}
        self.mtype_name_id_dict = {}

        self.category_id_name_dict = {}
        self.genre_id_name_dict = {}
        self.theme_id_name_dict = {}
        self.language_id_name_dict = {}
        self.country_id_name_dict = {}
        self.mtype_id_name_dict = {}

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

        query = 'SELECT name, id FROM ' + SqlDatabase.TABLE_MTYPE + ' ORDER BY name;'
        records = cur.execute(query).fetchall()
        for pair in records:
            self.mtype_name_id_dict[pair[0]] = pair[1]
            self.mtype_id_name_dict[pair[1]] = pair[0]

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

    def fill_up_mtype_table_from_dict(self):
        cur = self.conn.cursor()
        cur.execute("begin")
        self.mtype_name_id_dict = {}
        self.mtype_id_name_dict = {}
        mtype_list = self.translator.get_all_mtype_codes()
        for mtype in mtype_list:
            id = self.append_mtype(cur, mtype)
            self.mtype_name_id_dict[mtype] = id
            self.mtype_id_name_dict[id] = mtype

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

    def append_mtype(self, cur, mtype):
        cur.execute('INSERT INTO ' + SqlDatabase.TABLE_MTYPE + ' (name) VALUES (?) RETURNING id', (mtype,))
        record = cur.fetchone()
        (mtype_id, ) = record if record else (None,)
        return mtype_id

    def append_card_movie(self, title_orig, titles={}, category=None, mtypes={}, storylines={}, date=None, length=None, sounds=[], subs=[], genres=[], themes=[], origins=[], source_path=None, media=[]):

        try:
            cur = self.conn.cursor()
            cur.execute("begin")

            title_orig_id = self.language_name_id_dict[title_orig]
            category_id = self.category_name_id_dict[category]
            #
            # INSERT into CARD
            #
            query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD + '''
                (id_title_orig, id_category, date, length, source_path)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id;
            '''

            cur.execute(query, (title_orig_id, category_id, date, length, source_path))
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
            # INSERT into TABLE_CARD_MTYPE
            #
            for mtype in mtypes:
                query = '''INSERT INTO ''' + SqlDatabase.TABLE_CARD_MTYPE + '''
                    (id_mtype, id_card)
                    VALUES (?, ?);
                '''
                cur.execute(query, (self.mtype_name_id_dict[mtype], card_id))

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

            # close the insert transaction
            cur.execute("commit")

        except sqlite3.Error as e:
            logging.error("To append media failed with: '{0}' while inserting record".format(e))
            cur.execute("rollback")



    def get_all_cards(self):

        cur = self.conn.cursor()
        cur.execute("begin")

        return_records = {}

        # Get Card list
        query = '''SELECT card.*, category.name as c_name, title_orig.name as t_name
        FROM ''' + SqlDatabase.TABLE_CARD + ''' card, ''' + SqlDatabase.TABLE_CATEGORY + ''' category, ''' + SqlDatabase.TABLE_LANGUAGE + ''' title_orig 
        WHERE card.id_category=category.id AND card.id_title_orig=title_orig.id;'''
        records=cur.execute(query).fetchall()

        for record in records:
            card_id = record['id']

            category = record['c_name']
            source_path = record['source_path']
            date = record['date']
            length = record['length']
            title_orig_name = record['t_name']
            
            # Get Sound list
            sound_long_list = []
            query = '''
                SELECT sound.name 
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' sound, ''' + SqlDatabase.TABLE_CARD_SOUND + ''' cs 
                WHERE card.id=? AND cs.id_card=card.id AND cs.id_sound=sound.id '''
            for row in cur.execute(query, (card_id,)).fetchall():
                sound_long_list.append(self.translator.translate_language_long(row[0]))

            # Get Sub list
            sub_long_list = []
            query = '''
                SELECT sub.name 
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' sub, ''' + SqlDatabase.TABLE_CARD_SUB + ''' cs 
                WHERE card.id=? AND cs.id_card=card.id AND cs.id_sub=sub.id '''
            for row in cur.execute(query, (card_id,)).fetchall():
                sub_long_list.append(self.translator.translate_language_long(row[0]))

            # Get Genre list
            genre_list = []
            query = '''
                SELECT genre.name 
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_GENRE + ''' genre, ''' + SqlDatabase.TABLE_CARD_GENRE + ''' cg 
                WHERE card.id=? AND cg.id_card=card.id AND cg.id_genre=genre.id '''
            for row in cur.execute(query, (card_id,)).fetchall():
                genre_list.append(self.translator.translate_genre('movie', row[0]))

            # Get Theme list
            theme_list = []
            query = '''
                SELECT theme.name 
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_THEME + ''' theme, ''' + SqlDatabase.TABLE_CARD_THEME + ''' ct
                WHERE card.id=? AND ct.id_card=card.id AND ct.id_theme=theme.id '''
            for row in cur.execute(query, (card_id,)).fetchall():
                theme_list.append(self.translator.translate_theme(row[0]))

            # Get Mtype list
            mtype_list = []
            query = '''
                SELECT mtype.name 
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_MTYPE + ''' mtype, ''' + SqlDatabase.TABLE_CARD_MTYPE + ''' cmt
                WHERE card.id=? AND cmt.id_card=card.id AND cmt.id_mtype=mtype.id '''
            for row in cur.execute(query, (card_id,)).fetchall():
                mtype_list.append(self.translator.translate_mtype(row[0]))

            # Get Origin list
            origin_long_list = []
            query = '''
                SELECT origin.name 
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_COUNTRY + ''' origin, ''' + SqlDatabase.TABLE_CARD_ORIGIN + ''' co
                WHERE card.id=? AND co.id_card=card.id AND co.id_origin=origin.id '''
            for row in cur.execute(query, (card_id,)).fetchall():
                origin_long_list.append(self.translator.translate_country_long(row[0]))

            # Get Original Title
            original_title = ""
            if title_orig_name != self.language:
                query = '''
                    SELECT title.text
                    FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' language, ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' title
                    WHERE card.id=? AND title.id_card=card.id AND title.id_language=language.id AND title.type=? AND language.name=?'''
                row = cur.execute(query, (card_id, "T", title_orig_name)).fetchone()
                original_title = row[0]

            # Get Title
            title = ""
            query = '''
                SELECT title.text
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' language, ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' title
                WHERE card.id=? AND title.id_card=card.id AND title.id_language=language.id AND title.type=? AND language.name=?'''
            row = cur.execute(query, (card_id, "T", self.language)).fetchone()
            if row is not None:
                title = row[0]
            else:
                title = original_title

            # Get Storyline
            storyline = ""
            query = '''
                SELECT storyline.text
                FROM ''' + SqlDatabase.TABLE_CARD + ''', ''' + SqlDatabase.TABLE_LANGUAGE + ''' language, ''' + SqlDatabase.TABLE_TEXT_CARD_LANG + ''' storyline
                WHERE card.id=? AND storyline.id_card=card.id AND storyline.id_language=language.id AND storyline.type=? AND language.name=?'''
            row = cur.execute(query, (card_id, "S", self.language)).fetchone()
            if row is not None:
                storyline = row[0]

            # Get media list
            media_list = []
            query = '''
                SELECT name
                FROM ''' + SqlDatabase.TABLE_CARD + ''' card, ''' + SqlDatabase.TABLE_MEDIUM + ''' medium
                WHERE card.id=? AND medium.id_card=card.id'''
            for row in cur.execute(query, (card_id,)).fetchall():
                media_list.append(row[0])

            return_records[card_id] = {}
            return_records[card_id]['category'] = category
            return_records[card_id]['date'] = date
            return_records[card_id]['length'] = length
            return_records[card_id]['original_title'] = original_title
            return_records[card_id]['title'] = title
            return_records[card_id]['storyline'] = storyline

            return_records[card_id]['sounds'] = sound_long_list
            return_records[card_id]['subs'] = sub_long_list
            return_records[card_id]['genres'] = genre_list
            return_records[card_id]['themes'] = theme_list
            return_records[card_id]['origins'] = origin_long_list          
            return_records[card_id]['mtypes'] = mtype_list
            return_records[card_id]['media'] = media_list
            return_records[card_id]['source_path'] = source_path


        # close the insert transaction
        cur.execute("commit")

        return return_records
