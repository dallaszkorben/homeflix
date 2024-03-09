
import sqlite3

con = sqlite3.connect("/home/akoel/.playem/playem.db")
con.execute('SELECT * from Level').fetchall()
con.execute('SELECT * from Card').fetchall()
con.execute('SELECT * from Text_Card_Language WHERE type="T"').fetchall()

=================================

--- get all standalone movies ---
 
==================================

----------
version 1:
----------


--- The original title of the movies will be shown, if the original title is NOT on the requested language
--- "title_req" field is EMPTY
--- "title_orig" field contains the original title
con.execute('''
                SELECT 
                    card.id id, 
                    NULL title_req, 
                    -- NULL lang_req, 
                    tcl.text title_orig, 
                    -- lang.name lang_orig,
                    card.source_path source_path
                FROM 
                    Card card, 
                    Text_Card_Lang tcl, 
                    Category cat,
                    Language lang
                WHERE
                    card.id_higher_hierarchy IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND
                    card.id_title_orig=lang.id AND
                    cat.name = :category AND
                    lang.name <> :lang;
''', {'category': 'movie', 'lang': 'hu'}).fetchall()


--- The movies with the title on the requested language will be shown - even if it is the original language
--- It will NOT show the movie if there is NO title on the requested language
--- "title_req" field contains the title
--- "title_orig" field is EMPTY
con.execute('''
                SELECT 
                    card.id id, 
                    tcl.text title_req, 
                    -- lang.name lang_req, 
                    NULL title_orig, 
                    -- NULL lang_orig,
                    card.source_path source_path
                FROM 
                    Card card, 
                    Text_Card_Lang tcl, 
                    Category cat,
                    Language lang
                WHERE
                    card.id_higher_hierarchy IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND
                    --card.id_title_orig=lang.id AND
                    card.id_category=cat.id AND
                    cat.name = :category AND
                    lang.name=:lang
''', {'category': 'movie', 'lang': 'hu'}).fetchall()

--- combine the two lists ---

con.execute('''
SELECT 
    id, 
    MAX(text_req) title_req, 
    MAX(text_orig) title_orig, 
    MAX(lang_orig) lang_orig,
    source_path

FROM

(                SELECT 
                    card.id id, 
                    NULL text_req, 
                    -- NULL lang_req, 
                    tcl.text text_orig, 
                    lang.name lang_orig,
                    card.source_path source_path
                FROM 
                    Card card, 
                    Text_Card_Lang tcl, 
                    Category cat,
                    Language lang
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
                    Card card, 
                    Text_Card_Lang tcl, 
                    Category cat,
                    Language lang
                WHERE
                    card.id_higher_hierarchy IS NULL AND
                    tcl.id_card=card.id AND
                    tcl.id_language=lang.id AND
                    tcl.type="T" AND
                    --card.id_title_orig=lang.id AND
                    card.id_category=cat.id AND
                    cat.name = :category AND
                    lang.name=:lang
)

GROUP BY id
ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END

''', {'lang': 'hu', 'category': 'movie'}).fetchall()



===================================================

--- get all standalone movies with genre=action ---
 
===================================================

----------
version 1:
----------


con.execute('''
SELECT 
id, 
MAX(text_req) title_req,
MAX(text_orig) title_orig,
MAX(lang_orig) lang_orig,
source_path

FROM

(                SELECT 
                    card.id id, 
                    NULL text_req, 
                    -- NULL lang_req, 
                    tcl.text text_orig, 
                    lang.name lang_orig,
                    card.source_path source_path
                FROM 
                    Card card, 
                    Text_Card_Lang tcl, 
                    Category cat,
                    Language lang,
                    
                    Genre genre, 
                    Card_Genre cg
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
                    Card card, 
                    Text_Card_Lang tcl, 
                    Category cat,
                    Language lang,

                    Genre genre, 
                    Card_Genre cg
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
                    lang.name=:lang
)

GROUP BY id
ORDER BY CASE WHEN title_req IS NULL THEN title_orig ELSE title_req END

''', {'genre': 'action', 'lang': 'hu', 'category': 'movie'}).fetchall()



=================================================

--- get all standalon movies with genre=drama ---
--- with extended data: all from card ---

=================================================

con.execute('''
SELECT 
    id, 
    MAX(title_req) title_req, 
    MAX(title_orig) title_orig, 
    MAX(lang_orig) lang_orig,
    MAX(lang_req) lang_req,
    MAX(storyline) storyline,
    source_path
FROM 
(
                SELECT 
                    card.id id, 
                    NULL title_req, 
                    NULL lang_req, 
                    tcl_title.text title_orig, 
                    title_lang.name lang_orig,
                    card.source_path source_path,
                    (SELECT tcl_storyline.text
                        FROM
                            Text_Card_Lang tcl_storyline,
                            Language storyline_language
                           
                        WHERE 
                            tcl_storyline.id_language=storyline_language.id AND
                            tcl_storyline.id_card=id AND
                            tcl_storyline.type="S" AND
                            storyline_language.name = :lang
                    ) storyline
                FROM 
                    Card card, 
                    Genre genre,
                    Card_Genre cg,

                    Text_Card_Lang tcl_title, 
                    Text_Card_Lang tcl_storyline,
                    Category cat,
                    Language title_lang
                    
                WHERE
                    card.id_higher_hierarchy IS NULL AND
                    tcl_title.id_card=card.id AND
                    tcl_title.id_language=title_lang.id AND
                    tcl_title.type="T" AND

                    cg.id_card=card.id AND
                    cg.id_genre=genre.id AND
                    genre.name=:genre AND

                    card.id_title_orig=title_lang.id AND
                    cat.name = :category AND
                    title_lang.name <> :lang                   
UNION
                SELECT 
                    card.id id, 
                    tcl_title.text title_req, 
                    title_lang.name lang_req, 
                    NULL title_orig, 
                    NULL lang_orig,
                    card.source_path source_path,
                    (SELECT tcl_storyline.text
                        FROM
                            Text_Card_Lang tcl_storyline,
                            Language storyline_language
                           
                        WHERE 
                            tcl_storyline.id_language=storyline_language.id AND
                            tcl_storyline.id_card=id AND
                            tcl_storyline.type="S" AND
                            storyline_language.name = :lang
                    ) storyline
                    
                FROM 
                    Card card, 
                    Genre genre,
                    Card_Genre cg,

                    Text_Card_Lang tcl_title,
                    
                    Category cat,
                    Language title_lang                    

                WHERE
                    card.id_higher_hierarchy IS NULL AND
                    tcl_title.id_card=card.id AND
                    tcl_title.id_language=title_lang.id AND
                    tcl_title.type="T" AND
                   
                    cg.id_card=card.id AND
                    cg.id_genre=genre.id AND
                    genre.name=:genre AND

                    --card.id_title_orig=title_lang.id AND
                    card.id_category=cat.id AND
                    cat.name = :category AND
                    title_lang.name=:lang
)
GROUP BY id
ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END

''', {'lang': 'hu', 'category': 'movie', 'genre': 'drama'}).fetchall()


======================================================

--- get all data from a Card ---
--- multiple hits in one field, separated by comma ---

======================================================
con.execute('''
                SELECT 
                    card.id as id,
                    card.date as date,
                    card.length as length,
                    card.source_path as source_path,
                    medium,
                    storyline,
                    sound,
                    sub,
                    origins,
                    genres,
                    themes,
                    directors,
                    writers,
                    voices,
                    stars,
                    actors
                FROM
                    (SELECT group_concat("{'" || mt.name || "': '" || m.name || "'}") medium
                        FROM 
                            Medium m,
                            MediaType mt
                        WHERE
                            m.id_card= :card_id AND
                            m.id_mediatype = mt.id
                    ),
                
                    (SELECT group_concat(tcl.text) storyline
                        FROM 
                            Text_Card_Lang tcl,
                            Language language
                        WHERE 
                            tcl.type = "S" AND
                            tcl.id_card = :card_id AND
                            tcl.id_language = language.id AND
                            language.name = :lang
                    ),                        

                    (SELECT group_concat(language.name) sound
                        FROM 
                            Language language,
                            Card_Sound card_sound
                        WHERE 
                            card_sound.id_sound=language.id AND
                            card_sound.id_card = :card_id
                    ),

                    (SELECT group_concat(language.name) sub
                        FROM 
                            Language language,
                            Card_Sub card_sub
                        WHERE 
                            card_sub.id_sub=language.id AND
                            card_sub.id_card = :card_id
                    ),
                    
                    (SELECT group_concat(country.name) origins
                        FROM 
                            Country country,
                            Card_Origin card_origin
                        WHERE 
                            card_origin.id_card = :card_id AND
                            country.id = card_origin.id_origin
                    ),                        

                    (SELECT group_concat(genre.name) genres
                        FROM 
                            Genre genre,
                            Card_Genre card_genre
                        WHERE 
                            card_genre.id_card = :card_id AND
                            genre.id = card_genre.id_genre
                    ),
                       
                    (SELECT group_concat(theme.name) themes
                        FROM 
                            Theme theme,
                            Card_Theme card_theme
                        WHERE 
                            card_theme.id_card = :card_id AND
                            theme.id = card_theme.id_theme
                    ),

                    (SELECT group_concat(person.name) directors
                        FROM 
                            Person person,
                            Card_Director cd
                        WHERE 
                            cd.id_director = person.id AND
                            cd.id_card = :card_id
                    ),

                    (SELECT group_concat(person.name) writers
                        FROM 
                            Person person,
                            Card_Writer cv                            
                        WHERE 
                            cv.id_writer = person.id AND
                            cv.id_card = :card_id
                    ),

                    (SELECT group_concat(person.name) voices
                        FROM 
                            Person person,
                            Card_Voice cv
                        WHERE 
                            cv.id_voice = person.id AND
                            cv.id_card = :card_id
                    ),

                    (SELECT group_concat(person.name) stars
                        FROM 
                            Person person,
                            Card_Star cs
                        WHERE 
                            cs.id_star = person.id AND
                            cs.id_card = :card_id
                    ),

                    (SELECT group_concat(person.name) actors
                        FROM 
                            Person person,
                            Card_Actor ca
                        WHERE 
                            ca.id_actor = person.id AND
                            ca.id_card = :card_id
                    ),

                    Card card
                WHERE
                    card.id = :card_id                    
''', {'card_id': 4, 'lang': 'hu'}).fetchone()






======================
-                    - 
--- get all series ---
-                    - 
======================

----------
version 1:
----------
input:  level.name, language.name, source_path

con.execute('''
SELECT level.id, level_title_lang.text, level.source_path
FROM Level, Level_Title_Lang, Language
WHERE 
level.name="series" AND
level_title_lang.id_level=level.id AND
level_title_lang.id_language=language.id AND
language.name="hu"
''').fetchall()

[(1, 'Kockafejek', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek'), (6, 'Psyché és Nárcisz', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/PsycheEsNarcisz-1980')]

----------
version 2:
----------
--- If there is no title on the given language, it gives back the title on the original language ---
--- If there is title on the given language but it is different to the original title then it gives back 2 lines of the same id ---
con.execute('''
SELECT level.id, level_title_lang.text, level.source_path, language.name
FROM Level, Level_Title_Lang, Language
WHERE 
level.name="series" AND
level_title_lang.id_level=level.id AND
level_title_lang.id_language=language.id AND
(language.name="hu" OR level.id_title_orig=language.id)
''').fetchall()

----------
version 3:
----------
--- It gives back the title on the given language
--- If there is no title on the given language, it gives back the title on the original language ---
--- It uses the ROW_NUMBER() function to order the title in the same level.id. First: the title on the requested language, second: the title on the original language, third: title on any other language. Finally it GROUP BY the level.id and only the first line will be kept in every group (every id)
con.execute('''
SELECT level.id id, 
ltl.text title, 
level.source_path source_path, 
language.name lang, 
orig.name orig, 
ROW_NUMBER() OVER (PARTITION BY level.id ORDER BY CASE WHEN language.name='hu' THEN 0 WHEN language.name=orig.name THEN 1 ELSE 2 END, language.name) AS rn
FROM 
Level level, 
Level_Title_Lang ltl, 
Language language, 
Language orig
WHERE 
level.name='series' AND
ltl.id_level=level.id AND
ltl.id_language=language.id AND
level.id_title_orig=orig.id AND
(language.name='hu' OR level.id_title_orig=language.id)
GROUP BY level.id
''').fetchall()


----------
version 4:
----------
--- It gives back the title on the given language
--- If there is no title on the given language, it gives back the title on the original language ---
--- It uses the ROW_NUMBER() function to order the title in the same level.id. First: the title on the requested language, second: the title on the original language, third: title on any other language. Finally it GROUP BY the level.id and only the first line will be kept in every group (every id)

--- show original title of all series ---
con.execute('''
SELECT level.id id, NULL title_req, NULL lang_req, ltl.text title_orig, lang.name lang_orig
FROM 
Level level, 
Level_Title_Lang ltl, 
Language lang 
WHERE
level.name='series' AND
ltl.id_level=level.id AND
ltl.id_language=lang.id AND
level.id_title_orig=lang.id
''').fetchall()

--- show original title of all series except if the requested language is the original ---
con.execute('''
SELECT level.id id, NULL title_req, NULL lang_req, ltl.text title_orig, lang.name lang_orig
FROM 
Level level, 
Level_Title_Lang ltl, 
Language lang,
Language orig
WHERE
level.name='series' AND
ltl.id_level=level.id AND
ltl.id_language=lang.id AND
level.id_title_orig=lang.id AND
level.id_title_orig=orig.id AND
orig.name <> 'en'
''').fetchall()


--- show requested title of all series if there is ---

con.execute('''
SELECT level.id id, level.category category, ltl.text title_req, lang.name lang_req, NULL title_orig, NULL lang_orig
FROM 
Level level, 
Level_Title_Lang ltl, 
Language lang 
WHERE
level.name=:level AND
level.category = :category AND
ltl.id_level=level.id AND
ltl.id_language=lang.id AND
lang.name=:lang
''', {"level": "series", "lang": "en", "category":"movie"}).fetchall()

--- combine the two lists ---

con.execute('''

SELECT id, MAX(title_req) title_req, MAX(lang_req) lang_req, MAX(title_orig) title_orig, MAX(lang_orig) lang_orig

FROM
(SELECT level.id id, NULL title_req, NULL lang_req, ltl.text title_orig, lang.name lang_orig
FROM 
Level level,
Level_Title_Lang ltl,
Category cat,
Language lang
WHERE
level.name=:level AND
ltl.id_level=level.id AND
ltl.id_language=lang.id AND
level.id_title_orig=lang.id AND
level.id_category=cat.id AND
cat.name=:category AND
lang.name <> :lang

UNION

SELECT level.id id, ltl.text title_req, lang.name lang_req, NULL title_orig, NULL lang_orig
FROM 
Level level, 
Level_Title_Lang ltl, 
Category cat,
Language lang 
WHERE
level.name=:level AND
ltl.id_level=level.id AND
ltl.id_language=lang.id AND
level.id_category=cat.id AND
cat.name=:category AND
lang.name=:lang)

GROUP BY id;

''', {'level': 'series', 'lang': 'it', 'category': 'movie'}).fetchall()


===================================
                                
--- get all sublevel of a level ---
                               
===================================
----------
version 1:
----------
input:  actual level ID, language
output: sublevel ID, sublevel name, sublevel title, source_path

con.execute('''
SELECT level.id, level.name, level_title_lang.text, level.source_path
FROM Level, level_title_lang, language
WHERE 
level.id_higher_level=6 AND
level_title_lang.id_level=level.id AND
level_title_lang.id_language=language.id AND
language.name="hu"
''').fetchall()


with level.id_higher_level=1
[(2, 'season', 'S01', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S01'), (3, 'season', 'S02', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S02'), (4, 'season', 'S03', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S03'), (5, 'season', 'S04', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S04')]

with level.id_higher_level=6
[]

----------
version 2:
----------
input:  actual level ID, language
output: sublevel ID, sublevel name, sublevel title, source_path

con.execute('''
SELECT NULL level_id, card.id card_id, card.sequence sequence, card.level level_name, text_card_lang.text title, card.source_path path
FROM Level, Card, text_card_lang, language
WHERE
card.id_higher_level=6 AND
level.id=card.id_higher_level AND
language.name="hu" AND
text_card_lang.id_language=language.id AND
text_card_lang.id_card=card.id AND
text_card_lang.type="T"
UNION
SELECT level.id level_id, NULL card_id, level.sequence sequence, level.name level_name, level_title_lang.text title, level.source_path path
FROM Level, level_title_lang, language
WHERE 
level.id_higher_level=6 AND
level_title_lang.id_level=level.id AND
level_title_lang.id_language=language.id AND
language.name="hu"
''').fetchall()


id_higher_level=6
[(None, 7, 1, 'episode', 'Psyché és Nárcisz', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/PsycheEsNarcisz-1980/E01'), (None, 8, 2, 'episode', 'Psyché és Nárcisz', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/PsycheEsNarcisz-1980/E02'), (None, 9, 3, 'episode', 'Psyché és Nárcisz', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/PsycheEsNarcisz-1980/E03')]


id_higher_level=1
[(2, None, 'season', 'S01', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S01'), (3, None, 'season', 'S02', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S02'), (4, None, 'season', 'S03', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S03'), (5, None, 'season', 'S04', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek/S04')]


----------
version 3:
----------
input:  actual level ID, language
output: sublevel ID, sublevel name, sublevel title, source_path
orders the list by sequence+folder name. It means if there is NO sequence added to the Card/Leve the it orders it by the folder name (usually name it by date)

con.execute('''
SELECT NULL level_id, card.id card_id, card.level level_name, text_card_lang.text title, card.sequence sequence, card.basename basename, card.source_path path
FROM Level, Card, text_card_lang, language
WHERE
card.id_higher_level=1 AND
level.id=card.id_higher_level AND
language.name="hu" AND
text_card_lang.id_language=language.id AND
text_card_lang.id_card=card.id AND
text_card_lang.type="T"

UNION

SELECT level.id level_id, NULL card_id, level.name level_name, level_title_lang.text title, level.sequence sequence, level.basename basename, level.source_path path
FROM Level, level_title_lang, language
WHERE 
level.id_higher_level=1 AND
level_title_lang.id_level=level.id AND
level_title_lang.id_language=language.id AND
language.name="hu" 
ORDER BY sequence, basename ASC
''').fetchall()

[(None, 2, '', 'episode', 'A második rész', '002', '/media/akoel/vegyes/MEDIA/07.Entertainment/01.Analysis/01.Film/01.A.Het.Mesterlovesze/002'), (None, 1, '', 'episode', 'Ez az első rész', '001', '/media/akoel/vegyes/MEDIA/07.Entertainment/01.Analysis/01.Film/01.A.Het.Mesterlovesze/001')]

==========================
-                        - 
--- get all ascendants ---
-                        - 
==========================

----------
version 1:
----------
input: Level ID
output: As many levels as there are records. Every record has level.id, level.name, title

con.execute('''
WITH RECURSIVE
b(id) AS (
SELECT 3
UNION
SELECT actual.id_higher_level
FROM b, Level as actual
WHERE b.id=actual.id
) SELECT * FROM b
''').fetchall()

[(3,), (2,), (1,), (None,)]


----------
version 2:
----------
input:  Card ID
output: As many levels as there are records. Every record has level.id, level.name, title

con.execute('''
WITH RECURSIVE
b(id) AS (
SELECT id_higher_level FROM Card WHERE id=1
UNION
SELECT actual.id_higher_level
FROM b, Level as actual
WHERE b.id=actual.id AND actual.id_higher_level IS NOT NULL
) SELECT * FROM b
''').fetchall()

[(3, 'episode'), (2, 'season'), (1, 'series')]

----------
version 3:
----------
input: Level ID, Language Name
output: As many levels as there are records. Every record has level.id, level.name, title

con.execute('''
SELECT level.id, level.name, level_title_lang.text FROM 
(WITH RECURSIVE
b(id) AS (
SELECT id_higher_level FROM Card WHERE id=1
UNION
SELECT actual.id_higher_level
FROM b, Level as actual
WHERE b.id=actual.id AND actual.id_higher_level IS NOT NULL
) SELECT * FROM b) as level_id, Level, Level_title_Lang, Language
WHERE 
level_id.id=level.id AND
level.id=level_title_lang.id_level AND
level_title_lang.id_language=language.id AND
language.name="hu"
''').fetchall()

[(2, 'season', 'S01'), (1, 'series', 'Kockafejek')]

--- 




===================================
                                
--- get all sub-hierarchy/card  ---
                               
===================================
----------
version 1:
----------

# --- In Hierarchy ---

con.execute('''
SELECT id, level, MAX(title_req) title_req, MAX(title_orig) title_orig

FROM
(SELECT hrchy.id id, hrchy.level level, NULL title_req, htl.text title_orig
FROM 
Hierarchy hrchy, 
Hierarchy_Title_Lang htl,
Category cat,
Language lang
WHERE
-- hrchy.level=:level AND
hrchy.id_higher_hierarchy=:hierarchy_id AND
htl.id_hierarchy=hrchy.id AND
htl.id_language=lang.id AND
hrchy.id_title_orig=lang.id AND
hrchy.id_category=cat.id AND
--cat.name=:category AND
lang.name <> :lang

UNION

SELECT hrchy.id id, hrchy.level level, htl.text title_req, NULL title_orig
FROM 
Hierarchy hrchy, 
Hierarchy_Title_Lang htl, 
Category cat,
Language lang 
WHERE
--hrchy.level=:level AND
hrchy.id_higher_hierarchy=:hierarchy_id AND
htl.id_hierarchy=hrchy.id AND
htl.id_language=lang.id AND
hrchy.id_category=cat.id AND
--cat.name=:category AND
lang.name=:lang)

GROUP BY id;

''', {'hierarchy_id': 2, 'lang': 'hu'}).fetchall()

# --- In CARD ---

con.execute('''
SELECT id, NULL level, MAX(title_req) title_req, MAX(title_orig) title_orig

FROM

(SELECT card.id id, NULL title_req, tcl.text title_orig
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
-- cat.name = :category AND
lang.name <> :lang

UNION


SELECT card.id id, tcl.text title_req, NULL title_orig
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
--card.id_title_orig=lang.id AND
-- cat.name = :category AND
lang.name=:lang)

GROUP BY id;

''', {'hierarchy_id': 2, 'lang': 'hu'}).fetchall()

# --- Combine 2 requests ---

con.execute('''
SELECT id, level, title_req, title_orig, sequence, source_path
FROM (

SELECT id, level, MAX(title_req) title_req, MAX(title_orig) title_orig, sequence, basename, source_path

FROM
(SELECT hrchy.id id, hrchy.level level, NULL title_req, htl.text title_orig, sequence, basename, source_path
FROM 
Hierarchy hrchy, 
Hierarchy_Title_Lang htl,
Category cat,
Language lang
WHERE
-- hrchy.level=:level AND
hrchy.id_higher_hierarchy=:hierarchy_id AND
htl.id_hierarchy=hrchy.id AND
htl.id_language=lang.id AND
hrchy.id_title_orig=lang.id AND
hrchy.id_category=cat.id AND
--cat.name=:category AND
lang.name <> :lang

UNION

SELECT hrchy.id id, hrchy.level level, htl.text title_req, NULL title_orig, sequence, basename, source_path
FROM 
Hierarchy hrchy, 
Hierarchy_Title_Lang htl, 
Category cat,
Language lang 
WHERE
--hrchy.level=:level AND
hrchy.id_higher_hierarchy=:hierarchy_id AND
htl.id_hierarchy=hrchy.id AND
htl.id_language=lang.id AND
hrchy.id_category=cat.id AND
--cat.name=:category AND
lang.name=:lang)

GROUP BY id




UNION



SELECT id, NULL level, MAX(title_req) title_req, MAX(title_orig) title_orig, sequence, basename, source_path

FROM

(SELECT card.id id, NULL title_req, tcl.text title_orig, sequence, basename, source_path
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
-- cat.name = :category AND
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
--card.id_title_orig=lang.id AND
-- cat.name = :category AND
lang.name=:lang)

GROUP BY id
)
            ORDER BY CASE 
                WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
                WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
                WHEN sequence<0 THEN basename
                WHEN sequence>=0 THEN sequence
            END

''', {'hierarchy_id': 2, 'lang': 'hu'}).fetchall()




===================================
                                
--- get medium of a card id  ---
                               
===================================

con.execute('''
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
''', {'card_id': '33', 'limit': 100}).fetchall()




==============================================
---        specific level of Cards         ---
---   filtered by level, category, genre   ---
---                                        ---
--- List example:                          ---
---              Bands New Wave Video      ---

---              Synth collection Video
===============================================

con.execute('''   
           SELECT 
                merged.id, 
               
                MAX(title_req) title_req, 
                MAX(lang_req) lang_req, 
                MAX(title_orig) title_orig, 
                MAX(lang_orig) lang_orig,
                source_path
            FROM (
                SELECT 
                    card.id id,
                    card.id_category id_category,
                    NULL title_req, 
                    NULL lang_req, 
                    htl.text title_orig, 
                    lang.name lang_orig,
                    card.source_path source_path,
                    card.sequence sequence,
                    card.basename
                FROM 
                        CARD card, 
                        TEXT_CARD_LANG htl, 
                        LANGUAGE lang
                WHERE
                    card.level=:level AND
                    htl.id_card=card.id AND
                    htl.id_language=lang.id AND
                    card.id_title_orig=lang.id AND
                    lang.name <> :lang 

                UNION

                SELECT 
                    card.id id,
                    card.id_category id_category,
                    htl.text title_req, 
                    lang.name lang_req, 
                    NULL title_orig, 
                    NULL lang_orig,
                    card.source_path source_path,
                    card.sequence sequence,
                    card.basename
                FROM 
                        CARD card, 
                        TEXT_CARD_LANG htl, 
                        LANGUAGE lang
                WHERE
                    card.level=:level AND
                    htl.id_card=card.id AND
                    htl.id_language=lang.id AND
                    lang.name = :lang
            ) merged,

---            Country country,
---            Card_Origin co,

---            Genre genre,
---            Card_Genre cg,

                Theme theme,
                Card_Theme ct,

            Category cat

            WHERE
                merged.id_category=cat.id
                AND cat.name=:category
                
                --- genre ---
---                AND cg.id_genre = genre.id
---                AND cg.id_card = merged.id 
---                AND genre.name =:genre
                -------------

                --- theme ---
                AND ct.id_theme = theme.id
                AND ct.id_card = merged.id 
                AND theme.name = :theme
                -------------
                
                
                --- origin ---
---                AND co.id_card = merged.id
---                AND co.id_origin = country.id
---                AND country.name = :origin
---                AND country.name != :not_origin
                --------------
            GROUP BY merged.id
            ORDER BY CASE 
                WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
                WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
                WHEN sequence<0 THEN basename
                WHEN sequence>=0 THEN sequence
            END

''', {'level': 'series', 'category': 'movie', 'genre': 'drama', 'theme': 'it', 'origin': 'hu', 'not_origin': 'hu', 'lang': 'en'}).fetchall()

''', {'level': 'band', 'category': 'music_video', 'genre': 'pop', 'origin': 'hu', 'not_origin': 'hu', 'lang': 'en'}).fetchall()






===========================================
---       get general standalone        ---
--- Filter: genre/theme/origin          ---
===========================================


import sqlite3
con = sqlite3.connect("/home/akoel/.playem/playem.db")

con.execute(''' 
SELECT *
FROM
    (
    SELECT
        base.id id,
        base.level level,
        base.title_req title_req,
        base.title_orig title_orig,
        base.lang_orig lang_orig,
        base.lang_req lang_req,
        base.title_on_thumbnail title_on_thumbnail,
        base.title_show_sequence title_show_sequence,
        base.source_path source_path,
        base.appendix appendix,
        base.medium medium,
        base.genres genres,
        base.themes,
        group_concat(country.name) origins
    FROM
        (
        SELECT
            base.id id,
            base.level level,
            base.title_req title_req,
            base.title_orig title_orig,
            base.lang_orig lang_orig,
            base.lang_req lang_req,
            base.title_on_thumbnail title_on_thumbnail,
            base.title_show_sequence title_show_sequence,
            base.source_path source_path,
            base.appendix appendix,
            base.medium medium,
            base.genres genres,
            group_concat(theme.name) themes
        FROM
            (
            SELECT
                base.id id,
                base.level level,
                base.title_req title_req,
                base.title_orig title_orig,
                base.lang_orig lang_orig,
                base.lang_req lang_req,
                base.title_on_thumbnail title_on_thumbnail,
                base.title_show_sequence title_show_sequence,
                base.source_path source_path,
                base.appendix appendix,
                base.medium medium,
                group_concat(genre.name) genres
            FROM
                (        
                SELECT 
                    merged.id id,
                    merged.level level,
                    MAX(title_req) title_req, 
                    MAX(title_orig) title_orig, 
                    MAX(lang_orig) lang_orig,
                    MAX(lang_req) lang_req,

                    merged.title_on_thumbnail title_on_thumbnail,
                    merged.title_show_sequence title_show_sequence,
                
                    merged.source_path,
                    group_concat(appendix_card.id) appendix,
                    group_concat( mt.name || "=" || cm.name) medium
                FROM 
                    (
                    SELECT 
                        card.id id, 
                        card.level level,
                        card.id_category id_category,
                        NULL title_req, 
                        NULL lang_req, 
                        tcl.text title_orig, 
                        lang.name lang_orig,

                        title_on_thumbnail,
                        title_show_sequence,
    
                        card.source_path source_path,
                        card.decade decade
                    FROM                     
                        Card card,
                        Text_Card_Lang tcl, 
                        Language lang                    
                    WHERE                
                        card.id_higher_card IS NULL
                        AND tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"
                        AND card.id_title_orig=lang.id
                        AND card.level IS NULL

                        AND card.isappendix = 0
                        AND lang.name <> :lang

                    UNION

                    SELECT 
                        card.id id,
                        card.level level,
                        card.id_category id_category,
                        tcl.text title_req, 
                        lang.name lang_req, 
                        NULL title_orig, 
                        NULL lang_orig,

                        title_on_thumbnail,
                        title_show_sequence,

                        card.source_path source_path,
                        card.decade decade
                    FROM                
                        Card card,
                        Text_Card_Lang tcl, 
                        Language lang                    
                    WHERE               
                        card.id_higher_card IS NULL
                        AND tcl.id_card=card.id
                        AND tcl.id_language=lang.id
                        AND tcl.type="T"
                        AND card.level IS NULL
 
                        AND card.isappendix = 0
                        AND lang.name=:lang
                    ) merged,
                    Category cat

                    --- It does not matter if it is empty ---
                    LEFT JOIN Card appendix_card 
                        ON appendix_card.id_higher_card = merged.id
                        AND appendix_card.isappendix = 1

                    LEFT JOIN Card_Media cm 
                        ON cm.id_card=merged.id
                        LEFT JOIN MediaType mt
                            ON cm.id_mediatype = mt.id
                    WHERE
                        --- category --- 
                        merged.id_category=cat.id
                        AND cat.name=:category

                        --- decade ---
--                        AND merged.decade=:decade

                GROUP BY merged.id
                ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
                ) base,

                Genre genre,
                Card_Genre card_genre
        
            WHERE
                --- genre ---
                card_genre.id_card = base.id
                AND genre.id = card_genre.id_genre

            GROUP BY base.id
            ) base,

            Theme theme,
            Card_Theme card_theme
        WHERE
            --- theme ---
            card_theme.id_card = base.id
            AND theme.id = card_theme.id_theme

        GROUP BY base.id
        )base,
        
        Country country,
        Card_Origin card_origin
    
    WHERE
        --- origin ---
        card_origin.id_card = base.id
        AND country.id = card_origin.id_origin
    GROUP BY base.id
    )base  
        
     
WHERE 
--    ',' || genres || ',' LIKE '%,comedy,%' AND ',' || genres || ',' LIKE '%,comedy,%'
--    AND ',' || themes || ',' LIKE '%,apocalypse,%' AND ',' || themes || ',' NOT LIKE '%,zombie,%'
--    AND 
    ',' || origins || ',' LIKE '%,fr,%' AND ',' || origins || ',' LIKE '%,fr,%'
LIMIT :limit;   
            

''', {'category': 'movie', 'decade': '80s', 'genre': ('satire', 'drama'), 'theme': None, 'actor': None, 'director': None, 'origin': None, 'not_origin': None, 'lang': 'en', 'limit': 100}).fetchall()        
