import os
import yaml
import re
import logging

CARD_FILE_NAME = "card.yaml"

media_type_dict = {
    'video': {'mkv', 'mp4', 'flv', 'divx', 'avi', 'webm', 'mov', 'mpg'},
    'audio': {'mp3', 'ogg', 'm4a'}, 
    'text':  {'doc', 'odt', 'pdf', 'epub', 'mobi', 'azw', 'azw3', 'iba', 'txt','rtf'}, 
    'image': {'jpg', 'jpeg', 'png'}, 
}

def getPatternMedia(mtypes):
    extension_list = []
    for mtype in mtypes:
        extension_list += media_type_dict[mtype]
    compile_string = ".+\\." + "(" + "|".join(extension_list) + ")$"
    return re.compile(compile_string)

def getPatternImage():
    return re.compile( '^image[.](jp(eg|g)|png)$' )

def getPatternCard():
    return re.compile( '^'+CARD_FILE_NAME+'$' )

def getPatternDate():
    return re.compile( r'^\d{4}(([-|\.])\d{2}\2\d{2})?$' )

def getPatternLength():
    return re.compile( r'^(\d{1,2}:\d{2}:\d{2})?$' )

def collectCardsFromFileSystem(actualDir, db, higher_level_id=None ):
    """ _________________________________________________________________
        Recursive analysis on the the file system
        _________________________________________________________________
    """

    # Collect files and and dirs in the current directory
    file_list = [f for f in os.listdir(actualDir) if os.path.isfile(os.path.join(actualDir, f))] if os.path.exists(actualDir) else []
    dir_list = [d for d in os.listdir(actualDir) if os.path.isdir(os.path.join(actualDir, d))] if os.path.exists(actualDir) else []

    basename = os.path.basename(actualDir)

    source_path = None
    card_path = None
    card_file_name = None    
    #image_path = None
    image_file_name = None

    level_id = None

    for file_name in file_list:
        
        # find the Card
        if getPatternCard().match( file_name ):
            card_path = os.path.join(actualDir, file_name)
            card_file_name = file_name
            source_path = actualDir
            
        # find the Image
        if getPatternImage().match( file_name ):
            #image_path = os.path.join(actualDir, file_name)
            image_file_name = file_name

    # If there is CARD in the actual directory
    if card_path:
        data = None
        with open(card_path, "r", encoding="utf-8") as file_object:
            #data=yaml.load(file_object, Loader=yaml.SafeLoader) # convert string to number if it is possible
            data=yaml.load(file_object, Loader=yaml.BaseLoader)  # every value loaded as string

        category = data['category']
        mtypes = data['mtypes']
        level = data['level']
        title_orig = data['title']['orig']
        titles = data['title']['titles']
        storylines = data['storylines']
        date = data['date']
        try:
            directors = data['directors']
        except:
            directors = []
        try:
            writers = data['writers']
        except:
            writers = []
        try:       
            actors = data['actors']
        except:
            actors = []
        try:
            host = data['host']
        except:
            host = []
        length = data['length']
        sounds = data['sounds']
        subs = data['subs']
        genres = data['genres']
        themes = data['themes']
        origins = data['origins']
        try:
            sequence = data['sequence']
        except:
            sequence = None

        # collect media files now, because at this point the category is known
        media = []
        for file_name in file_list:

            # find media
            if getPatternMedia(mtypes).match( file_name ):
                media.append(file_name)

        # filter out empty titles
        titles=dict((language, title) for language, title in titles.items() if title)

        # filter out empty storylines
        storylines=dict((language, storyline) for language, storyline in storylines.items() if storyline)

        card_error = False

# ---

        # search for wrong values in case of lowest level or simple card
        if not title_orig:
            logging.error( "CARD - No original language set for title in {0}".format(card_path))
            card_error = True
       
        if title_orig not in titles:
            logging.error( "CARD - No title set for original language  in {0}".format(card_path))
            card_error = True

        if title_orig not in db.language_name_id_dict:
            logging.error( "CARD - Original language ({1}) set for title in {0} is unknown".format(card_path, title_orig))
            card_error = True

# ---


        # this is a level not a media
        if not mtypes and level and not card_error:

            # create a new Level record + get back the id
            level_id=db.append_level(
                titles=titles,
                level=level,
                basename=basename,
                source_path=source_path,
                sequence=sequence,
                higher_level_id=higher_level_id                
            )


        # this could be the lowest level or a simple card
        else:
       
            # # search for wrong values in case of lowest level or simple card
            # if not title_orig:
            #     logging.error( "CARD - No original language set for title in {0}".format(card_path))
            #     card_error = True
        
            # if title_orig not in titles:
            #     logging.error( "CARD - No title set for original language  in {0}".format(card_path))
            #     card_error = True

            # if title_orig not in db.language_name_id_dict:
            #     logging.error( "CARD - Original language ({1}) set for title in {0} is unknown".format(card_path, title_orig))
            #     card_error = True

            if category not in db.category_name_id_dict:
                logging.error( "CARD - Category ({1}) is unknown in {0}".format(card_path, category))
                card_error = True

            for lang, text in storylines.items():
                if lang not in db.language_name_id_dict:
                    logging.error( "CARD - Storyline language ({1}) is unknown in {0}".format(card_path, lang))
                    card_error = True

            if not getPatternDate().match( date ):
                logging.error( "CARD - Date ({1}) is missing or in unknown form in {0}".format(card_path, date))
                card_error = True

            if not getPatternLength().match(length):
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

            for genre in genres:
                if genre not in db.genre_name_id_dict:
                    logging.error( "CARD - Genre ({1}) is unknown in {0}".format(card_path, genre))
                    card_error = True

            for theme in themes:
                if theme not in db.theme_name_id_dict:
                    logging.error( "CARD - Theme ({1}) is unknown in {0}".format(card_path, theme))
                    card_error = True

            for origin in origins:
                if origin not in db.country_name_id_dict:
                    logging.error( "CARD - Origin ({1}) is unknown in {0}".format(card_path, origin))
                    card_error = True

            if not card_error:
            
                # this is the lowest level
                # if level:

                    # # create a new Level record + get back the id
                    # level_id=db.append_level(
                    #     titles = titles,
                    #     level=level, 
                    #     higher_level_id=higher_level_id,
                    #     source_path=source_path
                    # )

                    # create a new Card record with level reference
            
            
                db.append_card_movie(
                    category=category,
                    mtypes=mtypes,
                    title_orig=title_orig, 
                    titles=titles, 
                    storylines=storylines,
                    date=date, 
                    length=length,
                    sounds=sounds, 
                    subs=subs, 
                    genres=genres, 
                    themes=themes, 
                    origins=origins,

                    media=media,

                    level=level,
                    basename=basename,
                    source_path=source_path,

                    sequence=sequence,
                    # higher_level_id=level_id,
                    higher_level_id=higher_level_id,

                )        

    for name in dir_list:
        subfolder_path_os = os.path.join(actualDir, name)
        val = collectCardsFromFileSystem( subfolder_path_os, db, higher_level_id=level_id )

    return