import os
import configparser
from pathlib import Path
import logging

from playem.property.property import Property

class Translator( Property ):

    DEFAULT_LANGUAGE = "en"
    DEFAULT_FILE_NAME = "dictionary"
    EXTENSION = ".yaml"

    __instance = None

    def __new__(cls):
        if cls.__instance == None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def getInstance(cls, language=None):
        inst = cls.__new__(cls)
        cls.__init__(cls.__instance, language)
        return inst

    def __init__(self, language):

        self.language = Translator.DEFAULT_LANGUAGE
        if language is not None:
            self.language = language

        default_file_name = Translator.DEFAULT_FILE_NAME + Translator.EXTENSION
        default_file_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), default_file_name)

        expected_file_name = Translator.DEFAULT_FILE_NAME + "_" + self.language + Translator.EXTENSION
        expected_file_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), expected_file_name)
            
        try:
            super().__init__( expected_file_full_path)
            self.actual_dictionary = self.getDict()
        except FileNotFoundError:
            logging.error("Wanted to use '{0}' dictionary file, but the file was not found. We fall back to the default dictionary: '{1}'".format(expected_file_full_path, default_file_full_path))
            super().__init__( default_file_full_path)
            self.actual_dictionary = self.getDict()
            self.language = Translator.DEFAULT_LANGUAGE
 
    def get_actual_language_code(self):
        return self.language

    def translate_genre(self, category, genre):
        try:
            tr = self.actual_dictionary['genre'][category][genre]
        except KeyError:
            tr = genre
        return tr

    def translate_theme(self, theme):
        try:        
            tr = self.actual_dictionary['theme'][theme]
        except KeyError:
            tr = theme
        return tr

    def translate_mtype(self, mtype):
        try:        
            tr = self.actual_dictionary['mtype'][mtype]
        except KeyError:
            tr = mtype
        return tr

    def translate_language_short(self, text):
        try:
            tr = self.actual_dictionary['language']['short'][text]
        except KeyError:
            tr = text
        return tr

    def translate_language_long(self, text):
        try:
            tr = self.actual_dictionary['language']['long'][text]
        except KeyError:
            tr = text
        return tr

    def translate_country_short(self, text):
        try:
            tr = self.actual_dictionary['country']['short'][text]
        except KeyError:
            tr = text
        return tr

    def translate_country_long(self, text):
        try:
            tr = self.actual_dictionary['country']['long'][text]
        except KeyError:
            tr = text
        return tr

# ---

    def get_all_category_codes(self):
        category_list = []
        category_dict=self.actual_dictionary['categroy']
        for category in category_dict:
            category_list.append(category)
        return category_list

    def get_all_language_codes(self):
        lang_list = []
        lang_dict=self.actual_dictionary['language']['short']
        for lang in lang_dict:
            lang_list.append(lang)
        return lang_list

    def get_all_country_codes(self):
        country_list = []
        country_dict=self.actual_dictionary['country']['short']
        for country in country_dict:
            country_list.append(country)
        return country_list

    def get_all_genre_codes(self):
        genre_list = []
        category_list = self.get_all_category_codes()
        for category in category_list:
            genre_dict=self.actual_dictionary['genre'][category]
            for genre in genre_dict:
                genre_list.append(genre)
        return list(set(genre_list))

    def get_all_theme_codes(self):
        theme_list = []
        theme_dict=self.actual_dictionary['theme']
        for theme in theme_dict:
            theme_list.append(theme)
        return theme_list

    def get_all_mtype_codes(self):
        mtype_list = []
        mtype_dict=self.actual_dictionary['mtype']
        for mtype in mtype_dict:
            mtype_list.append(mtype)
        return mtype_list

    def get_all_category_codes(self):
        category_list = []
        category_dict=self.actual_dictionary['category']
        for category in category_dict:
            category_list.append(category)
        return category_list
