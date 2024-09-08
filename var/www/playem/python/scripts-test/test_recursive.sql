
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

-------------------------------
-- Recursive simple example ---
-------------------------------

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

---------------------------------------------
--- find the highest element of all cards ---
---------------------------------------------

con.execute('''
WITH RECURSIVE
    rec(group_id,id,id_higher_card,level,source_path) AS
    (
        SELECT 
            id group_id,                    -- For group the hierarchy of one media
            id, 
            id_higher_card, 
            level,
            source_path            
        FROM 
            Card card
        WHERE 
            card.level IS NULL
--            AND card.id = :card_id
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
SELECT group_id,id,source_path 
FROM
    rec
WHERE
    id_higher_card IS NULL
GROUP BY group_id
''', {'card_id': '19'}).fetchall()


----------------------------------------------------------------------------
--- Creates list to the media from the highest level (if there is level) --- 
----------------------------------------------------------------------------

con.execute('''
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
            AND card.id = :card_id
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
--WHERE
--    id_higher_card IS NULL
--GROUP BY id
ORDER BY id
''', {'card_id': '454'}).fetchall()


-----------------------------------
--- List of hierarchy to medium ---
-----------------------------------

con.execute('''
SELECT group_id, group_concat("ID:" || id || ";SRC:" || source_path)
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
                AND card.id_higher_card IS NOT NULL
                AND card.isappendix == 0
--                AND card.id = :card_id
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
    ORDER BY id         -- Needed to make hierarchy in order to highest to lowest (medium)
    )
GROUP BY group_id       -- Needed for group_concat()

''', {'card_id': '454'}).fetchall()

[
  (182,
  'ID:180;SRC:MEDIA/01.Movie/02.Documentary,ID:181;SRC:MEDIA/01.Movie/02.Documentary/Haboru.A.Nemzet.Ellen-2009,ID:182;SRC:MEDIA/01.Movie/02.Documentary/Haboru.A.Nemzet.Ellen-2009/E01'),
  (183,
  'ID:180;SRC:MEDIA/01.Movie/02.Documentary,ID:181;SRC:MEDIA/01.Movie/02.Documentary/Haboru.A.Nemzet.Ellen-2009,ID:183;SRC:MEDIA/01.Movie/02.Documentary/Haboru.A.Nemzet.Ellen-2009/E02'),
  (184,
  'ID:180;SRC:MEDIA/01.Movie/02.Documentary,ID:184;SRC:MEDIA/01.Movie/02.Documentary/Home-2009'),
  (185,
  'ID:180;SRC:MEDIA/01.Movie/02.Documentary,ID:185;SRC:MEDIA/01.Movie/02.Documentary/Inside.Job-2010'),
  
]



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
