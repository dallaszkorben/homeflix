import os
import yaml
import re
import logging
from pathlib import Path

class CardHandle:

    CARD_FILE_NAME = "card.yaml"
    MEDIA_FOLDER = "media"
    SCREENSHOT_FOLDER = "screenshots"
    THUMBNAIL_FOLDER = "thumbnails"
    APPENDIX_FOLDER = "appendix-"

    def __init__(self, web_base):

        self.web_base = web_base
        self.media_absolute_path = Path(web_base.mediaAbsolutePath)
        self.media_relative = Path(web_base.mediaRelativePath)

        # this keys must be in the dictionary.yaml file 'mediatype' section
        self.media_type_dict = {
            'video':   ['mkv', 'mp4', 'flv', 'divx', 'avi', 'webm', 'mov', 'mpg', 'm4v'],
            'audio':   ['mp3', 'ogg', 'm4a'], 
            'text':    ['txt'], 
            'pdf':     ['pdf'], 
            'ebook':   ['epub', 'mobi', 'azw', 'azw3', 'iba'],
            'doc':     ['doc', 'odt', 'rtf'], 
            'picture': ['jpg', 'jpeg', 'png'], 
            'code':    ['c', 'java', 'py', 'ino'], 
        }

    def getPatternImage(self):
        return re.compile( '^image[.](jp(eg|g)|png)$' )

    def getPatternCard(self):
        return re.compile( '^' + CardHandle.CARD_FILE_NAME + '$' )

    def getPatternDate(self):
        return re.compile( r'^\d{4}(([-|\.])\d{2}\2\d{2})?$' )

    def getPatternDecade(self):
        return re.compile( r'^\d{2}(\d{2})*s$' )

    def getPatternLength(self):
        return re.compile( r'^(\d{1,2}:\d{2}:\d{2})?$' )

    def collectCardsFromFileSystem(self, actualDir, db, higher_card_id=None ):
        """ _________________________________________________________________
            Recursive analysis on the the file system
            _________________________________________________________________
        """
        # Collect files and and dirs in the current directory
        file_list = [f for f in os.listdir(actualDir) if os.path.isfile(os.path.join(actualDir, f)) and self.getPatternCard().match( f )] if os.path.exists(actualDir) else []
        dir_list = [d for d in os.listdir(actualDir) if os.path.isdir(os.path.join(actualDir, d)) and d != CardHandle.MEDIA_FOLDER and d != CardHandle.SCREENSHOT_FOLDER and d != CardHandle.THUMBNAIL_FOLDER] if os.path.exists(actualDir) else []
        
        media_dir = os.path.join(actualDir, CardHandle.MEDIA_FOLDER)        
        media_list = [f for f in os.listdir(media_dir) if os.path.isfile(os.path.join(media_dir, f))] if os.path.exists(media_dir) else []

        basename = os.path.basename(actualDir)

        # we are in an appendix- folder
        is_appendix = True if basename.startswith(CardHandle.APPENDIX_FOLDER) else False

        source_path = None
        card_path = None
        card_file_name = None    
        image_file_name = None

        card_id = None

        # check the source path in the actual directory
        for file_name in file_list:
        
            # find the Card
            if self.getPatternCard().match( file_name ):
                card_path = os.path.join(actualDir, file_name)
                card_file_name = file_name
                source_path=os.path.join(self.media_relative, str(Path(actualDir).relative_to(self.media_absolute_path)))
                
                logging.debug("SOURCE path: '{0}'".format(source_path))

                break

        # If there is CARD in the actual directory
        if card_path:
            data = None
            with open(card_path, "r", encoding="utf-8") as file_object:
                # data=yaml.load(file_object, Loader=yaml.SafeLoader) # convert string to number if it is possible
                data=yaml.load(file_object, Loader=yaml.BaseLoader)  # every value loaded as string

            try:
                category = data['category']
            except:
                category = None

            try:
                primary_mediatype = data['primarymediatype']
            except:
                primary_mediatype = None

            try:
                level = data['level']
            except:
                level = None
            try:
                title_on_thumbnail = 1 if data['title']['onthumbnail'] in ['yes', 'Yes', 'true', 'True', 'y', 1] else 0
            except:
                title_on_thumbnail = 1

            try:
                show = 1 if data['show'] in ['yes', 'Yes', 'true', 'True', 'y', 1] else 0
            except:
                show = 1

            try:
                download = 1 if data['download'] in ['yes', 'Yes', 'true', 'True', 'y', 1] else 0
            except:
                download = 0

            # try:
            #     destination = data['destination'] if data['destination'] in ['show','download'] and is_appendix else None
            # except:
            #     destination = None


            try:
                title_show_sequence = data['title']['showsequence']
            except:
                title_show_sequence = ''

            try:
                title_orig = data['title']['orig']
            except:
                title_orig = None
            try:            
                titles = data['title']['titles']
            except:
                titles = []
            try:
                storylines = data['storylines']
            except:
                storylines = {}
            try:
                lyrics = data['lyrics']
            except:
                lyrics = {}
            try:
                decade = data['decade']
            except:
                decade = None
            try:
                date = data['date']
            except:
                date = None
            try:
                directors = data['directors']
            except:
                directors = []
            try:
                writers = data['writers']
            except:
                writers = []

            # Temprary solution for actors
            # TODO: Add "Role" "Role_Actor" tables
            try:
                actors = []
                for actor in data['actors']:
                    actors.append(actor)
                #actors = data['actors']
            except:
                actors = []
            try:       
                stars = data['stars']
            except:
                stars = []                
            try:       
                voices = data['voices']
            except:
                voices = []                
            try:
                hosts = data['hosts']
            except:
                hosts = []
            try:
                guests = data['guests']
            except:
                guests = []
            try:
                interviewers = data['interviewers']
            except:
                interviewers = []
            try:
                interviewees = data['interviewees']
            except:
                interviewees = []
            try:
                presenters = data['presenters']
            except:
                presenters = []
            try:
                lecturers = data['lecturers']
            except:
                lecturers = []
            try:
                performer = data['performer']
                performers = [performer]
            except:
                performers = []
            try:
                if not performers:
                    performers = data['performers']
            except:
                performers = []

            try:
                length = data['length']
            except:
                length = None
            try:
                sounds = data['sounds']
            except:
                sounds = []
            try:
                subs = data['subs']
            except:
                subs = []
            try:
                genres = data['genres']
            except:
                genres = []
            try:
                themes = data['themes']
            except:
                themes = []
            try:
                origins = data['origins']
            except:
                origins = []
            try:
                sequence = data['sequence']
                if not sequence:
                    sequence = None
            except:
                sequence = None

            # primary_mediatype
            # collect media files now, because at this point the category is known
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

            # filter out empty storylines
            storylines=dict((language, storyline) for language, storyline in storylines.items() if storylines)

            card_error = False

# ---
            # ---------------------------------------
            # filter out wrong cards in general case
            # ---------------------------------------
            if not title_orig:
                logging.error( "CARD - No original language set for title in {0}".format(card_path))
                card_error = True
       
            if title_orig not in titles:
                logging.error( "CARD - No title set for original language  in {0}".format(card_path))
                card_error = True

            if title_orig not in db.language_name_id_dict:
                logging.error( "CARD - Original language ({1}) set for title in {0} is unknown".format(card_path, title_orig))
                card_error = True

            if not primary_mediatype and not level:
                logging.error( "CARD - There is NO mediatype nor level configured in in {0}. At least one of them should be there".format(card_path))
                card_error = True

            if not primary_mediatype and level and not dir_list:
                logging.error( "CARD - There is level ({1}) and no mediatype configured for the card in {0} which means, it should be in the higher hierarchy. But there are NO subdirectories in the folder".format(card_path, level ))
                card_error = True

            if category not in db.category_name_id_dict:
                logging.error( "CARD - Category ({1}) is unknown in {0}".format(card_path, category))
                card_error = True

            for genre in genres:
                if genre not in db.genre_name_id_dict:
                    logging.error( "CARD - Genre ({1}) is unknown in {0}".format(card_path, genre))
                    card_error = True

            for origin in origins:
                if origin not in db.country_name_id_dict:
                    logging.error( "CARD - Origin ({1}) is unknown in {0}".format(card_path, origin))
                    card_error = True

            if decade and not self.getPatternDecade().match( decade ):
                logging.error( "CARD - Decade ({1}) is in unknown form in {0}".format(card_path, decade))
                card_error = True

 # ---




            # this is a level in the hierarchy / not a media
            # if not media and not card_error:
            if not media_dict and not card_error and not is_appendix:                

                # create a new Level record + get back the id
                card_id=db.append_hierarchy(
                    card_path=card_path,
                    title_orig=title_orig,
                    titles=titles,
                    title_on_thumbnail=title_on_thumbnail,
                    title_show_sequence=title_show_sequence,
                    isappendix=is_appendix,
                    show=show,
                    download=download,
                    date=date,
                    decade=decade,
                    category=category,
                    level=level,
                    genres=genres, 
                    themes=themes, 
                    origins=origins,
                    basename=basename,
                    source_path=source_path,
                    sequence=sequence,
                    higher_card_id=higher_card_id                
                )


            # this must be the lowest level or a simple card or appendix
            elif not card_error:
#            elif not card_error and media_dict:
       
                #logging.error( "checking appendix: '{0}', destination: '{1}'".format(is_appendix, destination))

#                if is_appendix and not destination:
#                    logging.error( "CARD - No destination set for card in {0}".format(card_path))
#                    card_error = True

                for lang, text in storylines.items():
                    if lang not in db.language_name_id_dict:
                        logging.error( "CARD - Storyline language ({1}) is unknown in {0}".format(card_path, lang))
                        card_error = True

                if date and not self.getPatternDate().match( date ):
                    logging.error( "CARD - Date ({1}) is missing or in unknown form in {0}".format(card_path, date))
                    card_error = True

                if length and not self.getPatternLength().match(length):
                    logging.error( "CARD - Length ({1}) is unknown form in {0}".format(card_path, length))
                    card_error = True

                for lang in subs:
                    if lang not in db.language_name_id_dict:
                        logging.error( "CARD - Sub language ({1}) is unknown in {0}".format(card_path, lang))
                        card_error = True

                for lang in sounds:
                    if lang not in db.language_name_id_dict:
                        logging.error( "CARD - Sound language ({1}) is unknown in {0}".format(card_path, lang))
                        card_error = True

                for theme in themes:
                    if theme not in db.theme_name_id_dict:
                        logging.error( "CARD - Theme ({1}) is unknown in {0}".format(card_path, theme))
                        card_error = True

                if not card_error:
                    card_id=db.append_card_media(
                        card_path=card_path,
                        title_orig=title_orig, 
                        titles=titles,
                        title_on_thumbnail=title_on_thumbnail,
                        title_show_sequence=title_show_sequence,
#                        destination=destination,
                        isappendix=is_appendix,
                        show=show,
                        download=download,
                        category=category,
                        storylines=storylines,
                        lyrics=lyrics,                        
                        decade=decade,
                        date=date, 
                        length=length,
                        sounds=sounds, 
                        subs=subs, 
                        genres=genres, 
                        themes=themes, 
                        origins=origins,
                        writers=writers,
                        directors=directors,
                        actors=actors,
                        stars=stars,
                        voices=voices,
                        hosts=hosts,
                        guests=guests,
                        interviewers=interviewers,
                        interviewees=interviewees,
                        presenters=presenters,
                        lecturers=lecturers,
                        performers=performers,

                        media=media_dict,

                        basename=basename,
                        source_path=source_path,

                        sequence=sequence,
                        higher_card_id=higher_card_id,
                    )        

#        logging.error( "TEST - higher_card: {0} for the {1}. dir_list: {2}".format(higher_card_id, card_path, dir_list))

        for name in dir_list:
            subfolder_path_os = os.path.join(actualDir, name)
            val = self.collectCardsFromFileSystem( subfolder_path_os, db, higher_card_id=card_id )

        return