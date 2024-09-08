import os
import sys
import ruamel.yaml
import re
import logging
from pathlib import Path

class CardManipulator:
    """
    This class is about to generate IDs into the card.
    This class is a fix, so it needs to be run only once to fix the missing IDs
    """
    CARD_FILE_NAME = "card.yaml"
    MEDIA_FOLDER = "media"
    SCREENSHOT_FOLDER = "screenshots"
    THUMBNAIL_FOLDER = "thumbnails"
    APPENDIX_FOLDER = "appendix-"

    def __init__(self, mediaAbsolutePath, mediaRelativePath):

        self.media_absolute_path = Path(mediaAbsolutePath)
        self.media_relative = Path(mediaRelativePath)

        # this keys must be in the dictionary.yaml file 'mediatype' section
        self.media_type_dict = {
            'video':   ['mkv', 'mp4', 'flv', 'divx', 'avi', 'webm', 'mov', 'mpg', 'm4v'],
            'audio':   ['mp3', 'ogg', 'm4a'], 
            'text':    ['txt'], 
            'pdf':     ['pdf'], 
            'ebook':   ['epub', 'mobi', 'azw', 'azw3', 'iba', 'pdf'],
            'doc':     ['doc', 'odt', 'rtf'], 
            'picture': ['jpg', 'jpeg', 'png', 'webp', 'avif'], 
            'code':    ['c', 'java', 'py', 'ino', 'yaml'],
            'archive': ['tar', 'gz', 'zip', 'deb'],
        }

    def getPatternImage(self):
        return re.compile( '^image[.](jp(eg|g)|png)$' )

    def getPatternCard(self):
        return re.compile( '^' + CardManipulator.CARD_FILE_NAME + '$' )

    def collectCardsFromFileSystem(self, actualDir):
        """ _________________________________________________________________
            Recursive analysis on the the file system
            _________________________________________________________________
        """
        # Collect files and and dirs in the current directory
        file_list = [f for f in os.listdir(actualDir) if os.path.isfile(os.path.join(actualDir, f)) and self.getPatternCard().match( f )] if os.path.exists(actualDir) else []
        dir_list = [d for d in os.listdir(actualDir) if os.path.isdir(os.path.join(actualDir, d)) and d != CardManipulator.MEDIA_FOLDER and d != CardManipulator.SCREENSHOT_FOLDER and d != CardManipulator.THUMBNAIL_FOLDER] if os.path.exists(actualDir) else []

        media_dir = os.path.join(actualDir, CardManipulator.MEDIA_FOLDER)        
        media_list = [f for f in os.listdir(media_dir) if os.path.isfile(os.path.join(media_dir, f))] if os.path.exists(media_dir) else []

        basename = os.path.basename(actualDir)

        # we are in an appendix- folder
        is_appendix = True if basename.startswith(CardManipulator.APPENDIX_FOLDER) else False

        source_path = None
        card_path = None
        card_file_name = None
        image_file_name = None

        yaml = ruamel.yaml.YAML()
        yaml.preseve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)

        # check the source path in the actual directory
        for file_name in file_list:

            # find the Card
            if self.getPatternCard().match( file_name ):
                card_path = os.path.join(actualDir, file_name)
                card_file_name = file_name
                source_path=os.path.join(self.media_relative, str(Path(actualDir).relative_to(self.media_absolute_path)))
                break

        # If there is CARD in the actual directory
        if card_path:

            data = None
            with open(card_path, "r", encoding="utf-8") as file_object:
                data = yaml.load(file_object)

            try:
                primary_mediatype = data['primarymediatype']
            except:
                primary_mediatype = None

            try:
                title_orig = data['title']['orig']
            except:
                title_orig = None
            try:
                titles = data['title']['titles']
            except:
                titles = []

            media_dict = {}

            for file_name in media_list:
                if primary_mediatype in self.media_type_dict:
                    extension_list = self.media_type_dict[primary_mediatype]
                    compile_string = ".+\\." + "(" + "|".join(extension_list) + ")$"
                    if re.compile(compile_string).match(file_name):
                        if not primary_mediatype in media_dict:
                            media_dict[primary_mediatype] = []
                        media_dict[primary_mediatype].append(file_name)

            # filter out empty titles
            titles=dict((language, title) for language, title in titles.items() if title)

            # This is the lowest level
#            if media_dict and not is_appendix:

                # delete the tag keys, if there is any
                # data.pop("tag", None)

            # convert negative value to positive
            id_hash = hash(actualDir) & ((1<<sys.hash_info.width)-1)
            #id = id_hash>>1
#            id_str=str(id_hash)[-18:]
            id_str=str(id_hash)[0:18]
            id = int(id_str)
            print( "{0}, {1}, {2}, {3}".format(id, titles, actualDir, id_hash))
            data['id'] = id
            with open(card_path, "w", encoding="utf-8") as file_object:
                yaml.dump(data, file_object)

        for name in dir_list:
            subfolder_path_os = os.path.join(actualDir, name)
            val = self.collectCardsFromFileSystem( subfolder_path_os)

        return


# I need this section to have the same seed for hash all the time to generate the same ID for the same media whenever you run this code
my_hashseed = '13'
hashseed = os.getenv('PYTHONHASHSEED')
if hashseed != my_hashseed or not hashseed:
    os.environ['PYTHONHASHSEED'] = my_hashseed
    os.execv(sys.executable, [sys.executable] + sys.argv)

absolute_path= "/media/akoel/vegyes/MEDIA"
#absolute_path= "/media/akoel/vegyes/MEDIA/03.Radioplay"
relative_path= "MEDIA"

cardManipulator = CardManipulator(absolute_path, relative_path)
cardManipulator.collectCardsFromFileSystem(absolute_path )
