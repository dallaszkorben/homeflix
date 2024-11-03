
=== Recursive ===

sudo mount /dev/sda1 /media/pi -o uid=pi,gid=pi

sudo mount -o bind /home/pi/Projects/playem/var/www/playem/ /var/www/playem
sudo mount -o bind  /media/pi/MEDIA /var/www/playem/MEDIA/

sudo service apache2 restart

sudo umount /var/www/playem/MEDIA
sudo umount /var/www/playem


source ~/Projects/python/playem/var/www/playem/python/env/bin/activate
cd /home/akoel/Projects/python/playem/var/www/playem/python
python3

from playem.card.database import SqlDatabase as DB
db=DB()

import sqlite3
con = sqlite3.connect("/home/akoel/.playem/playem.db")

---------------------------------------------------------
-- Show all tables with AUTOINCREMENT column in the DB --
---------------------------------------------------------

con.execute('''
    select * from sqlite_sequence
''', {}).fetchall()

con.execute('''
    SELECT * FROM Card WHERE source_path LIKE "%Bang%"
''', {}).fetchall()

con.execute('''
    SELECT * FROM Card WHERE id='6d6c0ba21c7606819297c7e29d0ffdf9'
''', {}).fetchall()


----------------------------------
-- Recursive learning examples ---
----------------------------------

--- Example 1: consecutive numbers
con.execute('''
WITH RECURSIVE cnt(x) AS    -- Define the TABLE (cnt) with its FIELD (x)
(
    SELECT 1                -- Initial select
    UNION ALL
    SELECT x+1              -- Recursive_select - where TABLE name can be used to join
    FROM cnt
    LIMIT 100
)
SELECT x FROM cnt;          -- Query on the TABLE
''', {}).fetchall()

--- Example 2: fibonacci sequnce
con.execute('''
WITH RECURSIVE fibonacci(a,b,c) AS      -- Define the TABLE (cnt) with its FIELD (x)
(
    SELECT 0,1,1                        -- Initial first record of the virtual (fibonacci) table
    UNION ALL
    SELECT b, c, b+c                    -- Takes the last record of the table, do any operation with them and create a new record.
    FROM fibonacci
    LIMIT 10                            -- Take only the first 10 records
)
SELECT c FROM fibonacci;                -- Only the 3rd column I want to show in the result
''', {}).fetchall()


----------------------------------------------
--- find all hierarchy of a low level card ---
----------------------------------------------

con.execute('''
WITH RECURSIVE
    rec(group_id,id,id_higher_card,level,source_path) AS    -- define a new table, called 'rec' having the given fields
    (
        SELECT                                              -- define the INITIAL record
            id group_id,                                    -- the group_id`s initial value is the id - meaning of the field: the lowest level card_id
            id, 
            id_higher_card, 
            level,
            source_path            
        FROM 
            Card card
        WHERE                                               -- INITIAL conditions
            card.level IS NULL                              -- take the lowest level cards 
            AND card.id = :card_id                          -- take that specific card
        UNION ALL

        SELECT                                              -- the next record
            rec.group_id,                                   --   takes the group_id of the previous record => lowest card id
            card.id,                                        --   takes the recent card id => the higher level card id
            card.id_higher_card,                            --   takes the higher level card_id
            card.level,
            card.source_path
        FROM
            rec,
            Card card
        WHERE
            rec.id_higher_card=card.id                      -- connects the new card record and the previous card record. previous record`s id_higher_card is the recent card id. Which means, the recent record is the parent of the previous
    )
SELECT group_id,id,source_path                              -- print out only the group_id, id, source_path
FROM
    rec
''', {'card_id': '85eaef2bb3e3ef4986d0a8994b4ee1ce'}).fetchall()

-- result:
--   [
--   ('85eaef2bb3e3ef4986d0a8994b4ee1ce', '85eaef2bb3e3ef4986d0a8994b4ee1ce', 'MEDIA/01.Movie/03.Series/02-Series/The.Big.Bang.Theory/S01/E07'), 
--   ('85eaef2bb3e3ef4986d0a8994b4ee1ce', 'f3c94b019ee85c4ff085c1b991dee2ef', 'MEDIA/01.Movie/03.Series/02-Series/The.Big.Bang.Theory/S01'), 
--   ('85eaef2bb3e3ef4986d0a8994b4ee1ce', '670b1bb7bbfded8a6f26ecf5754943d4', 'MEDIA/01.Movie/03.Series/02-Series/The.Big.Bang.Theory')
--   ]

-- standalone movie id: '1dc9c4cef22199632bc71b7db427f822'
-- sequel movie id:     'c091e3dcbcbbb42e10b1bc4bb2c96e85'
-- series movie id:     '85eaef2bb3e3ef4986d0a8994b4ee1ce'

---------------------------------------------------------------
--- find the highest level card of the given low level card ---
---------------------------------------------------------------
con.execute('''
WITH RECURSIVE
    rec(group_id,id,id_higher_card,level,source_path) AS    -- define a new table, called 'rec' having the given fields
    (
        SELECT                                              -- define the initial record
            id group_id,                                    -- the group_id`s initial value is the id
            id, 
            id_higher_card, 
            level,
            source_path            
        FROM 
            Card card
        WHERE 
            card.level IS NULL                              -- take the lowest level cards 
            AND card.id = :card_id                          -- take that specific card
        UNION ALL

        SELECT                                              -- the next record
            rec.group_id,
            card.id,
            card.id_higher_card,
            card.level,
            card.source_path
        FROM
            rec,
            Card card
        WHERE
            rec.id_higher_card=card.id                      -- previous record`s id_higher_card is the recent card id. Which means, the recent record is the parent of the previous
    )
SELECT group_id,id,source_path                              -- I print out only the group_i, id, source_path
FROM
    rec
WHERE
    id_higher_card IS NULL                                  -- take only the record which has NO id_higher_card => the highest level card of the given card
-- GROUP BY group_id
''', {'card_id': '85eaef2bb3e3ef4986d0a8994b4ee1ce'}).fetchall()

-- result:
--   [('85eaef2bb3e3ef4986d0a8994b4ee1ce', '670b1bb7bbfded8a6f26ecf5754943d4', 'MEDIA/01.Movie/03.Series/02-Series/The.Bing.Bang.Theory')]


----------------------------------------
--- find all the highest level cards ---
---                                  ---
--- hide all duplications            ---
----------------------------------------
res=con.execute('''
WITH RECURSIVE
    rec(group_id,id,id_higher_card,level,source_path) AS    -- define a new table, called 'rec' having the given fields
    (
        SELECT                                              -- define the initial record
            id group_id,                                    -- the group_id`s initial value is the id
            id, 
            id_higher_card, 
            level,
            source_path            
        FROM 
            Card card
        WHERE 
            card.level IS NULL                              -- take the lowest level cards 
        UNION ALL

        SELECT                                              -- the next record
            rec.group_id,
            card.id,
            card.id_higher_card,
            card.level,
            card.source_path
        FROM
            rec,
            Card card
        WHERE
            rec.id_higher_card=card.id                      -- previous record`s id_higher_card is the recent card id. Which means, the recent record is the parent of the previous
    )
SELECT group_id,id,source_path                              -- I print out only the group_i, id, source_path
FROM
    rec
WHERE
    id_higher_card IS NULL                                  -- take only the record which has NO id_higher_card => the highest level card of the given card
GROUP BY id
ORDER BY source_path
''', {'card_id': '85eaef2bb3e3ef4986d0a8994b4ee1ce'})
for name in res.fetchall():
    print(name)

-- result:
--   ('97ffa458d3eda176e7209ec13c900144', '97ffa458d3eda176e7209ec13c900144', 'MEDIA/01.Movie/01.Standalone/10.Cloverfield.Lane')
--   ('5583062bccde422e47378450068cc5a2', '5583062bccde422e47378450068cc5a2', 'MEDIA/01.Movie/01.Standalone/2001.Space.Odyssey-1968')
--   ('6d6c0ba21c7606819297c7e29d0ffdf9', '6d6c0ba21c7606819297c7e29d0ffdf9', 'MEDIA/01.Movie/01.Standalone/A.100.Eves.Ember.Aki.Kimaszott.Az.Ablakon.Es.Eltunt')
--   ('8d64eb3ccaefdf29038fe1441816c571', '8d64eb3ccaefdf29038fe1441816c571', 'MEDIA/01.Movie/01.Standalone/A.Halal.50.Oraja-1965')
--   ('11ce502ee42b9223e44145262a4e0b8b', '11ce502ee42b9223e44145262a4e0b8b', 'MEDIA/01.Movie/01.Standalone/A.Profi-1981')



----------------------------------------------------------------------------
--- Creates list to the media from the highest level (if there is level) --- 
----------------------------------------------------------------------------

res=con.execute('''
WITH RECURSIVE
    rec(group_id, id,id_higher_card,level,source_path) AS
    (
        SELECT
            id group_id,
            id, 
            id_higher_card, 
            level,
            source_path            
        FROM 
            Card card
        WHERE 
            card.level IS NULL
            AND card.id_higher_card IS NOT NULL
            AND card.isappendix == 0
        UNION ALL

        SELECT 
            rec.group_id,
            card.id,
            card.id_higher_card,
            card.level,
            card.source_path
        FROM
            rec,
            Card card
        WHERE
            rec.id_higher_card=card.id
    )
SELECT group_id, id,source_path 
FROM
    rec
WHERE
    id_higher_card IS NULL
GROUP BY id
ORDER BY id
''', {'card_id': '454'})
for name in res.fetchall():
    print(name)


---------------------------------------------------------
--- List of highest levels and the belonging card ids ---
--- using group_concat                                ---
---------------------------------------------------------

res=con.execute('''
--- SELECT group_id, group_concat("ID:" || id || ";SRC:" || source_path)
SELECT group_concat("ID:" || group_id), source_path
-- SELECT group_id, id, source_path
FROM
    (WITH RECURSIVE
        rec(group_id, id,id_higher_card,level,source_path) AS
        (
            SELECT
                id group_id,
                id, 
                id_higher_card, 
                level,
                source_path            
            FROM 
                Card card
            WHERE 
                card.level IS NULL
--                AND card.id_higher_card IS NOT NULL
                AND card.isappendix == 0
            UNION ALL

            SELECT 
                rec.group_id,
                card.id,
                card.id_higher_card,
                card.level,
                card.source_path
            FROM
                rec,
                Card card
            WHERE
                rec.id_higher_card=card.id
        )
    SELECT group_id, id,source_path 
    FROM
        rec
    WHERE
        id_higher_card IS NULL                              -- Only the highest level records will be considered
    )
GROUP BY id                                                 -- Needed for group_concat()
ORDER BY source_path
''', {'card_id': '454'})
for name in res.fetchall():
    print(name)
    
-- result:
--   ('ID:92894330d1ccb7a0c167d887f65a5142,ID:343680ed875ca9280c8f877ae2bfd793,ID:54f0a50adfcd37acce95ebab7ba70f56', 'MEDIA/01.Movie/02.Documentary/~Aaron.Russo')
--   ('ID:6e2d97530fde20cb5fa8781ba868e920,ID:d4b0bebb12e7b6b8e40bd6cfc39bc07a,ID:c6af8fdbc816774461ab53d7faf3255d,ID:2250d55dd59567547872382877f001dc', 'MEDIA/01.Movie/05.Remakes/Dune')
--   ('ID:57f0b675489b7d3af92326d18e813551,ID:cfe84c9f703a88fea67de004091436c6', 'MEDIA/02.Music/02.Audio/The.Human.League')
--   ('ID:9e7e21bfa68989f00f4772a8fb1b4b2b', 'MEDIA/02.Music/01.Video/03.80s/Roni.Griffith')
--   ('ID:37b9a23005464627de6f526699534bbc', 'MEDIA/02.Music/01.Video/03.80s/Taco')
--   ('ID:8c8a1439ca421662f76e2f48206fb992,ID:43f6b3914ade4459001a029236b8cf1e,ID:a4eff518b196e799f85477704f982e50', 'MEDIA/02.Music/02.Audio/Yonderboi')
--   ('ID:f5eb74ebfd2ff2e8bcdf4b025cc2e17b', 'MEDIA/02.Music/01.Video/03.80s/Styx')



---------------------






-----------------------------------------------
--- List of hierarchy to medium             ---
--- With traditional filter category/genre  ---
-----------------------------------------------

con.execute('''
SELECT group_id, MAX(id_category), group_concat("ID:" || id || ";SRC:" || source_path)
FROM
    (WITH RECURSIVE
        rec(group_id, id,id_higher_card,level,source_path, id_category) AS
        (
            SELECT
                card.id group_id,
                card.id id, 
                card.id_higher_card, 
                card.level,
                card.source_path,
                card.id_category id_category
            FROM 
                Card card,
                
                --- Conditional ---
                Category category,
                
                Genre genre,
                Card_Genre card_genre,
                
                Theme theme,
                Card_Theme card_theme
                
            WHERE 
                card.level IS NULL
                --AND card.id_higher_card IS NOT NULL
                AND card.isappendix == 0
                
                --- Conditional ---
                AND category.id=card.id_category
                AND category.name = :category
                
                AND card_genre.id_genre=genre.id
                AND card_genre.id_card=card.id
                AND genre.name = :genre
                
                AND card_theme.id_theme=theme.id
                AND card_theme.id_card=card.id
                AND theme.name = :theme
                
            UNION ALL

            SELECT 
                rec.group_id,
                card.id,
                card.id_higher_card,
                card.level,
                card.source_path,
                NULL
            FROM
                rec,
                Card card
            WHERE
                rec.id_higher_card=card.id
        )
    SELECT group_id, id_category, id,source_path 
    FROM
        rec
    ORDER BY id         -- Needed to make hierarchy in order to highest to lowest (medium)
    )
GROUP BY group_id       -- Needed for group_concat()

''', {'card_id': '454', 'category': 'movie', 'genre': 'scifi', 'theme': 'alien'}).fetchall()

[
  (34,   1,  'ID:34;SRC:MEDIA/01.Movie/01.Standalone/Paul-2011'),
  (38,   1,  'ID:38;SRC:MEDIA/01.Movie/01.Standalone/Plan.9.from.Outer.Space'),
  (61,   1,  'ID:61;SRC:MEDIA/01.Movie/01.Standalone/Forbidden.Planet-1956'),
  (82,   1,  'ID:82;SRC:MEDIA/01.Movie/01.Standalone/The.Thing-1982'),
  (87,   1,  'ID:87;SRC:MEDIA/01.Movie/01.Standalone/Contact-1997'),
  (89,   1,  'ID:89;SRC:MEDIA/01.Movie/01.Standalone/Mars.Attacks-1996'),
  (126,  1,  'ID:126;SRC:MEDIA/01.Movie/01.Standalone/Sunshine-2007'),
  (127,  1,  'ID:127;SRC:MEDIA/01.Movie/01.Standalone/Super.8'),
  (145,  1,  'ID:145;SRC:MEDIA/01.Movie/01.Standalone/They.Live-1988'),
  (176,  1,  'ID:176;SRC:MEDIA/01.Movie/01.Standalone/Close.Encounters.of.the.Third.Kind-1977'),
  (473,  1,  'ID:472;SRC:MEDIA/01.Movie/04.Sequels/Alien,ID:473;SRC:MEDIA/01.Movie/04.Sequels/Alien/Alien1.Alien-1979'),
  (474,  1,  'ID:472;SRC:MEDIA/01.Movie/04.Sequels/Alien,ID:474;SRC:MEDIA/01.Movie/04.Sequels/Alien/Alien2.Aliens-1986'),
  (475,  1,  'ID:472;SRC:MEDIA/01.Movie/04.Sequels/Alien,ID:475;SRC:MEDIA/01.Movie/04.Sequels/Alien/Alien3-Alien3-1992'),
  (476,  1,  'ID:472;SRC:MEDIA/01.Movie/04.Sequels/Alien,ID:476;SRC:MEDIA/01.Movie/04.Sequels/Alien/Alien4-Resurrection-1997'),
  (477,  1,  'ID:472;SRC:MEDIA/01.Movie/04.Sequels/Alien,ID:477;SRC:MEDIA/01.Movie/04.Sequels/Alien/Alien5.Prometheus-2012'),
  (478,  1,  'ID:472;SRC:MEDIA/01.Movie/04.Sequels/Alien,ID:478;SRC:MEDIA/01.Movie/04.Sequels/Alien/Alien6.Covenant-2017')
]



-----------------------------------------------
--- List of ids of the highest hierarchy    ---
--- With traditional filters category/genre ---
-----------------------------------------------

con.execute('''
WITH RECURSIVE
    rec(id,id_higher_card,level,source_path) AS
    (
        SELECT 
            
            card.id, 
            card.id_higher_card, 
            card.level,
            card.source_path            
        FROM 
            Card card,
                
            --- Conditional ---
            Category category,
                
            Genre genre,
            Card_Genre card_genre,
                
            Theme theme,
            Card_Theme card_theme
        WHERE 

            --AND card.id_higher_card IS NOT NULL
            card.isappendix == 0
                
            --- Conditional ---
            AND category.id=card.id_category
            AND category.name = :category
                
            AND card_genre.id_genre=genre.id
            AND card_genre.id_card=card.id
            AND genre.name = :genre
                
            AND card_theme.id_theme=theme.id
            AND card_theme.id_card=card.id
            AND theme.name = :theme

        UNION ALL

        SELECT 
            card.id,
            card.id_higher_card,
            card.level,
            card.source_path
        FROM
            rec,
            Card card
        WHERE
            rec.id_higher_card=card.id
    )
SELECT id,source_path 
FROM
    rec
WHERE
    id_higher_card IS NULL
GROUP BY id
''', {'category': 'movie', 'genre': 'scifi', 'theme': 'ai'}).fetchall()

[
(2,   'MEDIA/01.Movie/01.Standalone/2001.Space.Odyssey-1968'), 
(117, 'MEDIA/01.Movie/01.Standalone/Saturn.3'), 
(472, 'MEDIA/01.Movie/04.Sequels/Alien'), 
(487, 'MEDIA/01.Movie/04.Sequels/Blade.Runner')
]


-----------------------------------------------
--- List of ids of the highest hierarchy    ---
--- With filters category/genre             ---
-----------------------------------------------

con.execute('''

SELECT
    card.id,
    card.source_path,
    themes,
    genres,
    directors,
    actors
FROM
    (
    WITH RECURSIVE
        rec(id,id_higher_card,level,source_path, themes, genres, directors, actors) AS
        (
            SELECT                 
                card.id, 
                card.id_higher_card, 
                card.level,
                card.source_path,
                themes,
                genres,
                directors,
                actors
                
            FROM 
                Card card,
                
                --- Conditional ---
                Category category
                
            --- GENRE ---
            LEFT JOIN 
            (
                SELECT group_concat(genre.name) genres, card_genre.id_card
                FROM
                    Genre genre,
                    Card_Genre card_genre
                WHERE            
                    card_genre.id_genre=genre.id
                GROUP BY card_genre.id_card
            )gnr
            ON gnr.id_card=card.id
            
            --- THEME ---
            LEFT JOIN 
            (
                SELECT group_concat(theme.name) themes, card_theme.id_card
                FROM
                    Theme theme,
                    Card_Theme card_theme
                WHERE            
                    card_theme.id_theme=theme.id
                GROUP BY card_theme.id_card
            )thm
            ON thm.id_card=card.id
    
            --- DIRECTORS ---
            LEFT JOIN    
            (
                SELECT group_concat(person.name) directors,  card_dir.id_card
                FROM 
                    Person person,
                    Card_Director card_dir
                WHERE 
                    card_dir.id_director = person.id
                GROUP BY card_dir.id_card
            ) dr
            ON dr.id_card=card.id

            --- ACTORS ---
            LEFT JOIN    
            (
                SELECT group_concat(person.name) actors,  card_actor.id_card
                FROM 
                    Person person,
                    Card_Actor card_actor
                WHERE 
                    card_actor.id_actor = person.id
                GROUP BY card_actor.id_card
            ) act
            ON act.id_card=card.id
    
            WHERE 
                card.isappendix == 0
                AND category.id=card.id_category
                
                -------------------
                --- Conditional ---
                --- Pre-filter  ---
                -------------------

                --- WHERE CATEGORY ---
                AND category.name = :category
                
                --- WHERE THEMES - conditional ---
                --AND ',' || themes || ',' LIKE '%,' || :theme || ',%'

                --- WHERE GENRES - conditional ---
                AND ',' || genres || ',' LIKE '%,' || :genre || ',%'                
                
                --- WHERE DIRECTORS - conditional ---
                AND ',' || directors || ',' LIKE '%,' || :director || ',%'
                
                --- WHERE ACTORS - conditional ---
                -- AND ',' || actors || ',' LIKE '%,' || :actor || ',%'

            UNION ALL

            SELECT 
                card.id,
                card.id_higher_card,
                card.level,
                card.source_path,
                NULL,
                NULL,
                NULL,
                NULL
            FROM
                rec,
                Card card
            WHERE
                rec.id_higher_card=card.id
        )
    SELECT id, themes, genres, directors, actors
    FROM
        rec
    WHERE
        id_higher_card IS NULL
    GROUP BY id
    ) mixed_id_list,
    Card card    
WHERE
    mixed_id_list.id=card.id

''', {'category': 'movie', 'genre': 'scifi', 'theme': '*', 'director': 'Ridley Scott', 'actor': '*'}).fetchall()

[
(75, 'MEDIA/01.Movie/01.Standalone/The.Martian-2015', 'survival', 'scifi,drama,adventure', 'Ridley Scott', 'Matt Damon,Jessica Chastain,Kristen Wiig,Jeff Daniels,Michael Peña,Sean Bean,Kate Mara,Sebastian Stan,Aksel Hennie,Chiwetel Ejiofor,Benedict Wong,Mackenzie Davis,Donald Glover,Nick Mohammed,Shu Chen'), 
(472, 'MEDIA/01.Movie/04.Sequels/Alien', None, None, None, None), 
(487, 'MEDIA/01.Movie/04.Sequels/Blade.Runner', None, None, None, None)]
