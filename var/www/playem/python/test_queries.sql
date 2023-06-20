
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


--- show original title of all standalone media except if the requested language is the original ---
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


--- show requested title of all standalone films if there is ---

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

''', {'hierarchy_id': 1, 'lang': 'it'}).fetchall()

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
card.id_title_orig=lang.id AND
-- cat.name = :category AND
lang.name=:lang)

GROUP BY id;

''', {'hierarchy_id': 6, 'lang': 'it'}).fetchall()

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
card.id_title_orig=lang.id AND
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

''', {'hierarchy_id': 6, 'lang': 'it'}).fetchall()

