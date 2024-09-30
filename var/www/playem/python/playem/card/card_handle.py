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

    COLOR_RESET = "\x1b[0m"

    COLOR_GREEN = "\033[0;32m"
    COLOR_YELLOW = "\033[0;33m"
    COLOR_BLUE = "\033[0;34m"
    COLOR_RED = "\033[0;31m"
    COLOR_PURPLE = "\033[0;35m"
    COLOR_CYAN = "\033[0;36m"
    COLOR_WHITE = "\033[0;37m"

    COLOR_BOLD_GREEN = "\033[1;32m"
    COLOR_BOLD_YELLOW = "\033[1;33m"
    COLOR_BOLD_BLUE = "\033[1;34m"
    COLOR_BOLD_RED = "\033[1;31m"
    COLOR_BOLD_PURPLE = "\033[1;35m"
    COLOR_BOLD_CYAN = "\033[1;36m"
    COLOR_BOLD_WHITE = "\033[1;37m"

    COLOR_HIGH_GREEN = "\033[0;92m"
    COLOR_HIGH_YELLOW = "\033[0;93m"
    COLOR_HIGH_BLUE = "\033[0;94m"
    COLOR_HIGH_RED = "\033[0;91m"
    COLOR_HIGH_PURPLE = "\033[0;95m"
    COLOR_HIGH_CYAN = "\033[0;96m"
    COLOR_HIGH_WHITE = "\033[0;97m"

    COLOR_HIGH_BOLD_GREEN = "\033[0;92m"
    COLOR_HIGH_BOLD_YELLOW = "\033[0;93m"
    COLOR_HIGH_BOLD_BLUE = "\033[0;94m"
    COLOR_HIGH_BOLD_RED = "\033[0;91m"
    COLOR_HIGH_BOLD_PURPLE = "\033[0;95m"
    COLOR_HIGH_BOLD_CYAN = "\033[0;96m"
    COLOR_HIGH_BOLD_WHITE = "\033[0;97m"


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
            'ebook':   ['epub', 'mobi', 'azw', 'azw3', 'iba', 'pdf'],
            'doc':     ['doc', 'odt', 'rtf'], 
            'picture': ['jpg', 'jpeg', 'png', 'webp', 'avif'], 
            'code':    ['c', 'java', 'py', 'ino', 'yaml'],
            'archive': ['tar', 'gz', 'zip', 'deb'],
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

    def format_time_code_to_seconds(self, time_code):
        try:
            # Split the time code by ':' and ensure there are 3 parts (hh, mm, ss)
            parts = time_code.split(':')
            if len(parts) != 3:
                return 0

            # Convert to integers
            hours, minutes, seconds = map(int, parts)

            # Calculate total seconds
            total_seconds = (hours * 3600) + (minutes * 60) + seconds
            return total_seconds
        except ValueError:

            # If conversion to integer fails or any other error occurs, return None
            return None

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
        card_type = "--v--"

        # check the source path in the actual directory
        for file_name in file_list:

            # find the Card
            if self.getPatternCard().match( file_name ):
                card_path = os.path.join(actualDir, file_name)
                card_file_name = file_name
                source_path=os.path.join(self.media_relative, str(Path(actualDir).relative_to(self.media_absolute_path)))
#
#                logging.debug("SOURCE path: '{0}'".format(source_path))

                break

        # If there is CARD in the actual directory
        if card_path:

            try:

                card_error = None
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
                    #actors = []
                    #for actor in data['actors']:
                    #    actors.append(actor)
                    actors = data['actors']
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
                    reporter = data['reporter']
                    reporters = [reporter]
                except:
                    reporters = []
                try:
                    if not reporters:
                        reporters = data['reporters']
                except:
                    reporters = []
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

                # TODO: Makers, Contributors     

                try:
                    full_length = data['length']
                    full_time = self.format_time_code_to_seconds(full_length)
                except:
                    full_length = None
                    full_time = None
                try:
                    net_start = data['netstart']
                    net_start_time = self.format_time_code_to_seconds(net_start)
                except:
                    net_start = None
                    net_start_time = 0
                try:
                    if full_length:
                        net_stop = data['netstop']
                        net_stop_time = self.format_time_code_to_seconds(net_stop)
                    else:
                        net_stop = None
                        net_stop_time = None
                except:
                    if full_length:
                        net_stop = None
                        net_stop_time = full_time
                    else:
                        net_stop = None
                        net_stop_time = None
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

# ---   
                # ---------------------------------------
                # filter out wrong cards in general case
                # ---------------------------------------
                if not title_orig:
                    #logging.error( "CARD - No original language set for title in {0}".format(card_path))
                    card_error = "CARD - No original language set for title in {0}".format(card_path)

                if title_orig not in titles:
                    #logging.error( "CARD - No title set for original language  in {0}".format(card_path))
                    card_error = "CARD - No title set for original language  in {0}".format(card_path)

                if title_orig not in db.language_name_id_dict:
                    #logging.error( "CARD - Original language ({1}) set for title in {0} is unknown".format(card_path, title_orig))
                    card_error = "CARD - Original language ({1}) set for title in {0} is unknown".format(card_path, title_orig)

                if not primary_mediatype and not level:
                    #logging.error( "CARD - There is NO mediatype nor level configured in in {0}. At least one of them should be there".format(card_path))
                    card_error = "CARD - There is NO mediatype nor level configured in in {0}. At least one of them should be there".format(card_path)

                if not primary_mediatype and level and not dir_list:
                    #logging.error( "CARD - There is level ({1}) and no mediatype configured for the card in {0} which means, it should be in the higher hierarchy. But there are NO subdirectories in the folder".format(card_path, level ))
                    card_error = "CARD - There is level ({1}) and no mediatype configured for the card in {0} which means, it should be in the higher hierarchy. But there are NO subdirectories in the folder".format(card_path, level )

                if category not in db.category_name_id_dict:
                    #logging.error( "CARD - Category ({1}) is unknown in {0}".format(card_path, category))
                    card_error = "CARD - Category ({1}) is unknown in {0}".format(card_path, category)

                for genre in genres:
                    if genre not in db.genre_name_id_dict:
                        #logging.error( "CARD - Genre ({1}) is unknown in {0}".format(card_path, genre))
                        card_error = "CARD - Genre ({1}) is unknown in {0}".format(card_path, genre)

                for origin in origins:
                    if origin not in db.country_name_id_dict:
                        #logging.error( "CARD - Origin ({1}) is unknown in {0}".format(card_path, origin))
                        card_error = "CARD - Origin ({1}) is unknown in {0}".format(card_path, origin)

                if decade and not self.getPatternDecade().match( decade ):
                    #logging.error( "CARD - Decade ({1}) is in unknown form in {0}".format(card_path, decade))
                    card_error = "CARD - Decade ({1}) is in unknown form in {0}".format(card_path, decade)

#                if not card_error and not card_id and media_dict and not is_appendix:
#                    logging.error( "CARD - id is missing from the card in {0}".format(card_path))
#                    card_error = True

#                if is_appendix:
#                    logging.error( "Appendix:      {0} error: {1}".format(card_path, card_error))

 # ---  

# !!!   
#                logging.debug("SOURCE path: '{0}'".format(source_path))
# !!!   


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

#                        card_id=given_card_id,

                        isappendix=is_appendix,
                        show=show,
                        download=download,
                        date=date,
                        decade=decade,
                        category=category,
                        storylines=storylines,
                        level=level,
                        genres=genres, 
                        themes=themes, 
                        origins=origins,
                        basename=basename,
                        source_path=source_path,
                        sequence=sequence,
                        higher_card_id=higher_card_id
                    )
                    card_type = 'level'
# !!!   
#                    logging.debug("    level id: '{0}'".format(card_id))
# !!!   



                # this must be the lowest level or a simple card or appendix
#                elif not card_error and card_id:
                elif not card_error:

                    for lang, text in storylines.items():
                        if lang not in db.language_name_id_dict:
                            #logging.error( "CARD - Storyline language ({1}) is unknown in {0}".format(card_path, lang))
                            card_error = "CARD - Storyline language ({1}) is unknown in {0}".format(card_path, lang)

                    if date and not self.getPatternDate().match( date ):
                        #logging.error( "CARD - Date ({1}) is missing or in unknown form in {0}".format(card_path, date))
                        card_error = "CARD - Date ({1}) is missing or in unknown form in {0}".format(card_path, date)

                    if full_length and not self.getPatternLength().match(full_length):
                        #logging.error( "CARD - Full Length ({1}) is unknown form in {0}".format(card_path, full_length))
                        card_error = "CARD - Full Length ({1}) is unknown form in {0}".format(card_path, full_length)

                    if net_start and not self.getPatternLength().match(net_start):
                        #logging.error( "CARD - Net Start Length ({1}) is unknown form in {0}".format(card_path, net_start))
                        card_error = "CARD - Net Start Length ({1}) is unknown form in {0}".format(card_path, net_start)

                    if net_stop and not self.getPatternLength().match(net_stop):
                        #logging.error( "CARD - Net Start Length ({1}) is unknown form in {0}".format(card_path, net_stop))
                        card_error = "CARD - Net Stop Length ({1}) is unknown form in {0}".format(card_path, net_stop)

                    for lang in subs:
                        if lang not in db.language_name_id_dict:
                            #logging.error( "CARD - Sub language ({1}) is unknown in {0}".format(card_path, lang))
                            card_error = "CARD - Sub language ({1}) is unknown in {0}".format(card_path, lang)

                    for lang in sounds:
                        if lang not in db.language_name_id_dict:
                            #logging.error( "CARD - Sound language ({1}) is unknown in {0}".format(card_path, lang))
                            card_error = "CARD - Sound language ({1}) is unknown in {0}".format(card_path, lang)

                    for theme in themes:
                        if theme not in db.theme_name_id_dict:
                            #logging.error( "CARD - Theme ({1}) is unknown in {0}".format(card_path, theme))
                            card_error = "CARD - Theme ({1}) is unknown in {0}".format(card_path, theme)

                    if not card_error:

                        card_id=db.append_card_media(
                            card_path=card_path,
                            title_orig=title_orig, 
                            titles=titles,
                            title_on_thumbnail=title_on_thumbnail,
                            title_show_sequence=title_show_sequence,
#                            
#                            card_id=given_card_id,
                            isappendix=is_appendix,
                            show=show,
                            download=download,
                            category=category,
                            storylines=storylines,
                            lyrics=lyrics,                        
                            decade=decade,
                            date=date, 
                            length=full_length,
                            full_time=full_time,
                            net_start_time=net_start_time,
                            net_stop_time=net_stop_time,
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
                            reporters=reporters,

                            media=media_dict,

                            basename=basename,
                            source_path=source_path,

                            sequence=sequence,
                            higher_card_id=higher_card_id,
                        )
                        card_type = 'media'
            finally:

                if card_type == "media":
                    card_type_color = CardHandle.COLOR_GREEN
                elif card_type == "level":
                    card_type_color = CardHandle.COLOR_BLUE
                else:
                    card_type_color = CardHandle.COLOR_HIGH_RED

                error_color = CardHandle.COLOR_HIGH_RED

                logging.debug("id: {0} {1} {2} {3} {4} SOURCE Path: {5}".format(card_id, (1 if card_id else 3) * "\t", card_type_color, card_type, CardHandle.COLOR_RESET, source_path))

                if card_error:
                    logging.error( "{0}{1}{2}".format(error_color, card_error, CardHandle.COLOR_RESET))


        for name in dir_list:
            subfolder_path_os = os.path.join(actualDir, name)
            val = self.collectCardsFromFileSystem( subfolder_path_os, db, higher_card_id=card_id )

        return