#!env/bin/python

from playem.config.config import Config
from playem.translator.translator import Translator

trans = Translator.getInstance("hu")
print("Actual language: {0}".format(trans.translate_language_long(trans.get_actual_language_code())))
res=trans.translate_genre("movie", "drama")
print("In Movie 'drama' means: {0}".format(res))
lang_list = trans.get_all_language_codes()
print("Translatable language code list: {0}".format(lang_list))

print("---")
trans = Translator.getInstance("en")
print("Actual language: {0}".format(trans.translate_language_long(trans.get_actual_language_code())))
print("Not existing translation: {0}".format(trans.translate_genre("movie", "blabla")))

