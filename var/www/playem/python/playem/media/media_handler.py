import os
import yaml
import re

CARD_FILE_NAME = "card.yaml"

def getPatternImage():
    return re.compile( '^image[.](jp(eg|g)|png)$' )

def getPatternCard():
    return re.compile( '^'+CARD_FILE_NAME+'$' )

def collectCardsFromFileSystem(actualDir, media_dict={}, genre_dict={}, theme_dict={} ):
    """
        Recursive analysis on the the file system for the mediaCollectors
        _________________________________________________________________
    """
        
    # Collect files and and dirs in the current directory
    file_list = [f for f in os.listdir(actualDir) if os.path.isfile(os.path.join(actualDir, f))] if os.path.exists(actualDir) else []
    dir_list = [d for d in os.listdir(actualDir) if os.path.isdir(os.path.join(actualDir, d))] if os.path.exists(actualDir) else []
    
    card_path = None
    image_path = None

    for file_name in file_list:
        
        # find the Card
        if getPatternCard().match( file_name ):
            card_path = os.path.join(actualDir, file_name)
            
        # find the Image
        if getPatternImage().match( file_name ):
            image_path = os.path.join(actualDir, file_name)

    if card_path:
        data = None
        with open(card_path,"r", encoding="utf-8") as file_object:
            data=yaml.load(file_object, Loader=yaml.SafeLoader)

        category = data['category']
        title = data['title']
        genre = data['genre']
        theme = data['theme']
        
        media_dict
        movie:
            id: 1, 
            title:{en:"9", hu:"9"}, 
            media_path: /media/akoel/Movie/MyMovie

        genre_dict
        drama: [1, 23, 42, 545]
        comedy: [22, 324, 545]
        
        theme_dict
        war: [23, 432, ]

        

        if 
        media_dict
        print(, )

    for name in dir_list:
        subfolder_path_os = os.path.join(actualDir, name)
        val = collectCardsFromFileSystem( subfolder_path_os, media_dict, genre_dict, theme_dict )

    return