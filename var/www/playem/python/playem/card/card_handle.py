import os
import yaml
import re

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
    compile_string = ".+\\." + "|".join(extension_list) + "$"
    return re.compile(compile_string)

def getPatternImage():
    return re.compile( '^image[.](jp(eg|g)|png)$' )

def getPatternCard():
    return re.compile( '^'+CARD_FILE_NAME+'$' )

def collectCardsFromFileSystem(actualDir, db ):
    """ _________________________________________________________________
        Recursive analysis on the the file system
        _________________________________________________________________
    """

    # Collect files and and dirs in the current directory
    file_list = [f for f in os.listdir(actualDir) if os.path.isfile(os.path.join(actualDir, f))] if os.path.exists(actualDir) else []
    dir_list = [d for d in os.listdir(actualDir) if os.path.isdir(os.path.join(actualDir, d))] if os.path.exists(actualDir) else []
    
    source_path = None
    card_path = None
    card_file_name = None    
    #image_path = None
    image_file_name = None

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
            data=yaml.load(file_object, Loader=yaml.SafeLoader)

        category = data['category']
        mtypes = data['mtypes']
        title_orig = data['title']['orig']
        titles = data['title']['titles']
        storylines = data['storylines']
        date = data['general']['date']
        directors = data['general']['directors']
        writers = data['general']['writers']
        actors = data['general']['actors']
        length = data['general']['length']
        sounds = data['general']['sounds']
        subs = data['general']['subs']
        genres = data['general']['genres']
        themes = data['general']['themes']
        origins = data['general']['origins']

        # collect media files now, because at this point the category is known
        media = []
        for file_name in file_list:

            # find media
            if getPatternMedia(mtypes).match( file_name ):
                media.append(file_name)


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

            source_path=source_path,
            media=media
        )        

    for name in dir_list:
        subfolder_path_os = os.path.join(actualDir, name)
        val = collectCardsFromFileSystem( subfolder_path_os, db )

    return