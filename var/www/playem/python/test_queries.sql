
import sqlite3

con = sqlite3.connect("/home/akoel/.playem/playem.db")
con.execute('SELECT * from Level').fetchall()
con.execute('SELECT * from Card').fetchall()


======================
-                    - 
--- get all series ---
-                    - 
======================
input:  level.name, language.name, source_path

con.execute('''
SELECT level.id, level_lang.text, level.source_path
FROM Level, Level_Lang, Language
WHERE 
level.name="series" AND
level_lang.id_level=level.id AND
level_lang.id_language=language.id AND
language.name="hu"
''').fetchall()

[(1, 'Kockafejek', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/Kockafejek'), (6, 'Psyché és Nárcisz', '/media/akoel/vegyes/MEDIA/01.Movie/03.Series/PsycheEsNarcisz-1980')]

===================================
                                
--- get all sublevel of a level ---
                               
===================================
----------
version 1:
----------
input:  actual level ID, language
output: sublevel ID, sublevel name, sublevel title, source_path

con.execute('''
SELECT level.id, level.name, level_lang.text, level.source_path
FROM Level, level_lang, language
WHERE 
level.id_higher_level=6 AND
level_lang.id_level=level.id AND
level_lang.id_language=language.id AND
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
SELECT level.id level_id, NULL card_id, level.sequence sequence, level.name level_name, level_lang.text title, level.source_path path
FROM Level, level_lang, language
WHERE 
level.id_higher_level=6 AND
level_lang.id_level=level.id AND
level_lang.id_language=language.id AND
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

SELECT level.id level_id, NULL card_id, level.name level_name, level_lang.text title, level.sequence sequence, level.basename basename, level.source_path path
FROM Level, level_lang, language
WHERE 
level.id_higher_level=1 AND
level_lang.id_level=level.id AND
level_lang.id_language=language.id AND
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
SELECT level.id, level.name, level_lang.text FROM 
(WITH RECURSIVE
b(id) AS (
SELECT id_higher_level FROM Card WHERE id=1
UNION
SELECT actual.id_higher_level
FROM b, Level as actual
WHERE b.id=actual.id AND actual.id_higher_level IS NOT NULL
) SELECT * FROM b) as level_id, Level, Level_Lang, Language
WHERE 
level_id.id=level.id AND
level.id=level_lang.id_level AND
level_lang.id_language=language.id AND
language.name="hu"
''').fetchall()

[(3, 'episode', 'A tegnapi lekvár'), (2, 'season', 'S01'), (1, 'series', 'Kockafejek')]

--- 

