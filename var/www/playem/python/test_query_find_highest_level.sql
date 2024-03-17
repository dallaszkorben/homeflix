


=== Recursive ===

sudo mount /dev/sda1 /media/pi -o uid=pi,gid=pi

sudo mount -o bind /home/pi/Projects/playem/var/www/playem/ /var/www/playem
sudo mount -o bind  /media/pi/MEDIA /var/www/playem/MEDIA/

sudo service apache2 restart

sudo umount /var/www/playem/MEDIA
sudo umount /var/www/playem


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



------------------------------------------------------
--- FULL QUERY for highest level list              ---
--- Returns mixed standalone media and level cards ---
--- With filters category/genre                    ---
---                                                ---
--- get_highest_level_mixed()                      ---
------------------------------------------------------

con.execute('''
SELECT
    core.*,
    mixed_id_list.themes,
    mixed_id_list.genres,
    mixed_id_list.origins,
    mixed_id_list.directors,
    mixed_id_list.actors,
    
    storyline,
    lyrics,
    medium,
    appendix,
    
    sounds,
    subs,
    writers,
    voices,
    stars,
    hosts,
    guests    

--        interviewers,
--        interviewees,
--        presenters,
--        reporters,
--        lecturers,
--        performers, 
FROM

    --- mixed level id list ---
    (
    WITH RECURSIVE
        rec(id,id_higher_card,level,source_path, themes, genres, origins, directors, actors) AS
        (
            SELECT                 
                card.id, 
                card.id_higher_card, 
                card.level,
                card.source_path,
                themes,
                genres,
                origins,
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
    
            --- ORIGINS ---
            LEFT JOIN
            (
                SELECT group_concat(origin.name) origins, card_origin.id_card
                FROM
                    Country origin,
                    Card_Origin card_origin
                WHERE
                    card_origin.id_origin=origin.id
                GROUP BY card_origin.id_card
            )rgn
            ON rgn.id_card=card.id    
    
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
                AND ',' || themes || ',' LIKE '%,' || :theme || ',%'

                --- WHERE GENRES - conditional ---
                AND ',' || genres || ',' LIKE '%,' || :genre || ',%'                
                
                --- WHERE DIRECTORS - conditional ---
--                AND ',' || directors || ',' LIKE '%,' || :director || ',%'
                
                --- WHERE ACTORS - conditional ---
--                AND ',' || actors || ',' LIKE '%,' || :actor || ',%'

                --- WHERE ORIGINS - conditional ---
--                AND ',' || origins || ',' LIKE '%,' || :origin || ',%'


            UNION ALL

            SELECT 
                card.id,
                card.id_higher_card,
                card.level,
                card.source_path,
                NULL,
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
    SELECT id, themes, genres, origins, directors, actors 
    FROM
        rec
    WHERE
        id_higher_card IS NULL
    GROUP BY id
    ) mixed_id_list,
    
    --- unioned  with title ---
    (
    SELECT 
        unioned.id id,
        unioned.level level,
                
        MAX(title_req) title_req, 
        MAX(title_orig) title_orig, 
        MAX(lang_orig) lang_orig,
        MAX(lang_req) lang_req,

        unioned.title_on_thumbnail,
        unioned.title_show_sequence,

        unioned.decade,
        unioned.date,
        unioned.length,
                            
        unioned.source_path,
        unioned.id_category
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

            card.decade decade,
            card.date date,
            card.length length,
                                
            card.source_path source_path
        FROM                     
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE                
            tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
            AND card.id_title_orig=lang.id

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

            card.decade decade,
            card.date date,
            card.length length,
                                
            card.source_path source_path
        FROM               
            Card card,
            Text_Card_Lang tcl, 
            Language lang                    
        WHERE               
            tcl.id_card=card.id
            AND tcl.id_language=lang.id
            AND tcl.type="T"
 
            AND card.isappendix = 0
            AND lang.name=:lang
        ) unioned

    -- because of the title required and origin
    GROUP BY unioned.id               

    ) core
  
    -----------------
    --- STORYLINE ---
    -----------------
    LEFT JOIN
    (
        SELECT ord, storyline, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the storyline on the original language ---

            SELECT "2" as ord, tcl.text as storyline, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "S" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
--        HAVING MIN(ord)
--        ORDER BY ord
    )strl
    ON strl.id_card=core.id
   
    --------------
    --- LYRICS ---
    --------------
    LEFT JOIN
    (
        SELECT ord, lyrics, id_card
        FROM
        (

            --- Select the lyrics on the requested language, not the original ---

            SELECT "1" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                language.name = :lang AND
                card.id_title_orig<>language.id AND
                tcl.text IS NOT NULL
                
            UNION

            --- Select the lyrics on the original language ---

            SELECT "2" as ord, tcl.text as lyrics, tcl.id_card id_card
            FROM 
                Text_Card_Lang tcl,
                Language language,
                Card card
            WHERE 
                tcl.type = "L" AND
                tcl.id_language = language.id AND
                tcl.id_card = card.id AND
                card.id_title_orig=language.id AND        
                tcl.text IS NOT NULL
        )
        GROUP BY id_card
    )lrx
    ON lrx.id_card=core.id       
   
    --------------
    --- MEDIUM ---
    --------------
    LEFT JOIN
    (
        SELECT group_concat( media_type.name || "=" || card_media.name) medium, card_media.id_card
        FROM
            MediaType media_type,
            Card_Media card_media
        WHERE
            card_media.id_mediatype=media_type.id
        GROUP BY card_media.id_card
    )mdt
    ON mdt.id_card=core.id
   
    ----------------
    --- APPENDIX ---
    ----------------
     LEFT JOIN    
    (    
        SELECT
            card_id,
            group_concat("id=" || id || ";mt=" || media_type || ";cm=" || contact_media || ";sw=" || show || ";dl=" || download || ";rt=" || title_req || ";ot=" || title_orig || ";sp=" || source_path) appendix
        FROM
        
            (
            SELECT                
                merged_appendix.id,
                merged_appendix.card_id,
                MAX(merged_appendix.title_req) title_req, 
                MAX(merged_appendix.title_orig) title_orig,
                merged_appendix.show,
                merged_appendix.download,
                merged_appendix.source_path,
                mt.name media_type,
                cm.name contact_media                
            FROM
                (
                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    "" title_req, 
                    tcl.text title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE                
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND app_card.id_title_orig=lang.id
                    AND lang.name <> :lang

                UNION

                SELECT 
                    app_card.id id,
                    id_higher_card card_id,
                    app_card.isappendix,
                    app_card.show,
                    app_card.download,
                    app_card.source_path,
                    tcl.text title_req, 
                    "" title_orig
                FROM 
                    CARD app_card,
                    TEXT_CARD_LANG tcl, 
                    LANGUAGE lang                    
                WHERE
                    app_card.isappendix=1
                    AND tcl.id_card=app_card.id
                    AND tcl.id_language=lang.id
                    AND tcl.type="T"
                    AND lang.name=:lang
                ) merged_appendix,
                Card_Media cm,
                MediaType mt
                
            WHERE
                cm.id_card=merged_appendix.id
                AND mt.id=cm.id_mediatype
                
            GROUP BY merged_appendix.id
            )
        GROUP BY card_id
    ) pndx
    ON pndx.card_id=core.id    
  
    --------------
    --- SOUNDS ---
    --------------
    LEFT JOIN 
    (
        SELECT group_concat(language.name) sounds, card_sound.id_card
        FROM 
            Language language,
            Card_Sound card_sound
        WHERE 
            card_sound.id_sound=language.id 
        GROUP BY card_sound.id_card
    ) snd
    ON snd.id_card=core.id

    ----------------
    --- SUBTITLE ---
    ----------------
    LEFT JOIN
    (
        SELECT group_concat(language.name) subs, card_sub.id_card
        FROM 
            Language language,
            Card_Sub card_sub
        WHERE 
            card_sub.id_sub=language.id
        GROUP BY card_sub.id_card
    ) sb
    ON sb.id_card=core.id

    ---------------
    --- WRITERS ---
    ---------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) writers,  card_writer.id_card
        FROM 
            Person person,
            Card_Writer card_writer
        WHERE 
            card_writer.id_writer = person.id
        GROUP BY card_writer.id_card
    ) wr
    ON wr.id_card=core.id

    --------------
    --- VOICES ---
    --------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) voices,  card_voice.id_card
        FROM 
            Person person,
            Card_Voice card_voice
        WHERE 
            card_voice.id_voice = person.id
        GROUP BY card_voice.id_card
    ) vc
    ON vc.id_card=core.id    

    -------------
    --- STARS ---
    -------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) stars,  card_star.id_card
        FROM 
            Person person,
            Card_Star card_star
        WHERE 
            card_star.id_star = person.id
        GROUP BY card_star.id_card
    ) str
    ON str.id_card=core.id

    -------------
    --- HOSTS ---
    -------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) hosts,  card_host.id_card
        FROM 
            Person person,
            Card_Host card_host
        WHERE 
            card_host.id_host = person.id
        GROUP BY card_host.id_card
    ) hst
    ON hst.id_card=core.id    
    
    --------------
    --- GUESTS ---
    --------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) guests,  card_guest.id_card
        FROM 
            Person person,
            Card_Guest card_guest
        WHERE 
            card_guest.id_guest = person.id
        GROUP BY card_guest.id_card
    ) gst
    ON gst.id_card=core.id       
   
   
WHERE
    mixed_id_list.id=core.id
    

''', {'category': 'movie', 'genre': 'scifi', 'theme': 'ai', 'origin': 'us', 'director': 'Ridley Scott', 'actor': '*', 'lang': 'en'}).fetchall()


[(2, None, '2001: A Space Odyssey', None, None, 'en', 1, '', '60s', '1968', '2:29:00', 'MEDIA/01.Movie/01.Standalone/2001.Space.Odyssey-1968', 1, 'ai,meaning_of_life,origin_of_life', 'scifi,adventure', 'us', 'Stanley Kubrick', 'Keir Dullea,Gary Lockwood,William Sylvester,Daniel Richter,Leonard Rossiter,Margaret Tyzack,Robert Beatty,Sean Sullivan,Douglas Rain,Frank Miller,Bill Weston,Ed Bishop,Glenn Beck,Alan Gifford,Ann Gillis,Edwina Carroll,Penny Brahms,Heather Downham', '"\'2001\' is a story of evolution.\nSometime in the distant past, someone or something nudged evolution by placing a monolith on Earth (presumably elsewhere throughout the universe as well).\nEvolution then enabled humankind to reach the moon\'s surface, where yet another monolith is found, one that signals the monolith placers that humankind has evolved that far.\nNow a race begins between computers (HAL) and human (Bowman) to reach the monolith placers. \nThe winner will achieve the next step in evolution, whatever that may be."\n', None, 'video=2001.A.Space.Odyssey-1968.mkv', 'id=3;mt=picture;cm=poster-1.jpg;sw=1;dl=1;rt=Poster 1;ot=;sp=MEDIA/01.Movie/01.Standalone/2001.Space.Odyssey-1968/appendix-poster-1,id=4;mt=picture;cm=poster-2.jpg;sw=1;dl=1;rt=Poster 2;ot=;sp=MEDIA/01.Movie/01.Standalone/2001.Space.Odyssey-1968/appendix-poster-2', 'hu,en', 'hu,en', 'Stanley Kubrick,Arthur C. Clarke', None, 'Keir Dullea,Gary Lockwood,William Sylvester', None, None), (117, None, 'Saturn 3', None, None, 'en', 1, '', '80s', '1980', '1:27:28', 'MEDIA/01.Movie/01.Standalone/Saturn.3', 1, 'ai', 'trash,scifi', 'gb', 'John Barry,Stanley Donen', 'Ed Bishop,Farrah Fawcett,Kirk Douglas,Harvey Keitel,Christopher Muncke', 'Two lovers stationed at a remote base in the asteroid fields of Saturn are intruded upon by a retentive technocrat from Earth and his charge: a malevolent 8-ft robot.\nRemember, in space no one can hear you scream...\n', None, 'video=Harmas.Szamu.Urbazis-1980.mkv', None, 'hu,en', 'hu,en', 'Martin Amis,John Barry', None, 'Farrah Fawcett,Kirk Douglas,Harvey Keitel', None, None), 
(472, 'sequel', 'Alien', None, None, 'en', 1, '', None, '', None, 'MEDIA/01.Movie/04.Sequels/Alien', 1, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None), 
(487, 'sequel', 'Blade Runner', None, None, 'en', 1, '', None, '', None, 'MEDIA/01.Movie/04.Sequels/Blade.Runner', 1, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)]



---------------------------------------------------------------
--- FULL QUERY for lowest (medium) level list               ---
--- Returns only medium level cards level cards             ---
--- With filters category/genre/theme/origin/director/actor ---
---                                                         ---
--- get_lowest_level()                                      ---
---------------------------------------------------------------



---------------------------------------------------------------
--- FULL QUERY for next down level list of a card id        ---
--- Returns mixed standalone media and level cards          ---
--- With filters category/genre/theme/origin/director/actor ---
---                                                         ---
--- get_next_down_level_mixed()                             ---
---------------------------------------------------------------
