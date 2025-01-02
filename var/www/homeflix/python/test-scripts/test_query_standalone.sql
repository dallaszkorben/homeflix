----------------------------------------------------
--- search by genre/theme/orig/ logical elements ---
--- traditional + left join withouth filtering   ---
----------------------------------------------------

import sqlite3
con = sqlite3.connect("/home/akoel/.playem/playem.db")
                        

con.execute('''                       
SELECT
    list_with_genres.*,
    sounds,
    subs,
    directors,
    writers,
    voices,
    stars,
    actors
FROM
(
    SELECT
        list_with_themes.*,
        group_concat(genre.name) genres
    FROM
    (
        SELECT
            list_with_origins.*,
            group_concat(theme.name) themes
        FROM
        (
            SELECT
                list_with_appendix.*,
                group_concat(origin.name) origins
            FROM
            (
                SELECT
                    list_with_media_type.*,
                    group_concat(appendix_card.id) appendix
                FROM
                (
                    SELECT
                        raw_list.*,
                        group_concat( mt.name || "=" || cm.name) medium
                    FROM
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
                            
                            unioned.source_path
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

                                card.decade decade,
                                card.date date,
                                card.length length,
                                
                                card.source_path source_path
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
                        ) unioned, 
                
                        --- category - it is here regardless ---
                        Category cat 

                        WHERE           

                            --- category --- 
                            unioned.id_category=cat.id
                            AND cat.name=:category

                            --- decade - conditional ---
                            AND unioned.decade='60s' OR unioned.decade='70s'

                        -- because of the title required and origin
                        GROUP BY unioned.id               
        
                    ) raw_list
                    LEFT JOIN Card_Media cm 
                        ON cm.id_card=raw_list.id
                        LEFT JOIN MediaType mt
                        ON cm.id_mediatype = mt.id
                    GROUP BY raw_list.id

                ) list_with_media_type
                LEFT JOIN Card appendix_card 
                    ON appendix_card.id_higher_card = list_with_media_type.id
                    AND appendix_card.isappendix = 1
                GROUP BY list_with_media_type.id

            ) list_with_appendix
            LEFT JOIN Card_Origin co
                ON co.id_card=list_with_appendix.id
                INNER JOIN Country origin
                    ON co.id_origin=origin.id 
            GROUP BY list_with_appendix.id

        ) list_with_origins
        LEFT JOIN Card_Theme ct
            ON ct.id_card=list_with_origins.id
            INNER JOIN Theme theme
                ON ct.id_theme=theme.id

        --- WHERE ORIGIN - conditional ---
        WHERE ',' || origins || ',' LIKE '%,it,%'
        GROUP BY list_with_origins.id

    ) list_with_themes
    LEFT JOIN Card_Genre cg
        ON cg.id_card=list_with_themes.id
        INNER JOIN Genre genre
            ON cg.id_genre=genre.id

    --- WHERE THEMES - conditional ---
--    WHERE ',' || themes || ',' LIKE '%,conspiracy,%' AND ',' || themes || ',' NOT LIKE '%,blabla,%'
    GROUP BY list_with_themes.id
    
) list_with_genres


LEFT JOIN 
    (SELECT group_concat(language.name) sounds, card_sound.id_card
        FROM 
            Language language,
            Card_Sound card_sound
        WHERE 
            card_sound.id_sound=language.id 
        GROUP BY card_sound.id_card
    ) snd
    ON snd.id_card=list_with_genres.id

LEFT JOIN
    (SELECT group_concat(language.name) subs, card_sub.id_card
        FROM 
            Language language,
            Card_Sub card_sub
        WHERE 
            card_sub.id_sub=language.id
        GROUP BY card_sub.id_card
    ) sb
    ON sb.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) directors,  card_dir.id_card
        FROM 
            Person person,
            Card_Director card_dir
        WHERE 
            card_dir.id_director = person.id
        GROUP BY card_dir.id_card
    ) dr
    ON dr.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) writers,  card_writer.id_card
        FROM 
            Person person,
            Card_Writer card_writer
        WHERE 
            card_writer.id_writer = person.id
        GROUP BY card_writer.id_card
    ) wr
    ON wr.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) voices,  card_voice.id_card
        FROM 
            Person person,
            Card_Voice card_voice
        WHERE 
            card_voice.id_voice = person.id
        GROUP BY card_voice.id_card
    ) vc
    ON vc.id_card=list_with_genres.id    

LEFT JOIN    
    (SELECT group_concat(person.name) stars,  card_star.id_card
        FROM 
            Person person,
            Card_Star card_star
        WHERE 
            card_star.id_star = person.id
        GROUP BY card_star.id_card
    ) str
    ON str.id_card=list_with_genres.id
    
LEFT JOIN    
    (SELECT group_concat(person.name) actors,  card_actor.id_card
        FROM 
            Person person,
            Card_Actor card_actor
        WHERE 
            card_actor.id_actor = person.id
        GROUP BY card_actor.id_card
    ) act
    ON act.id_card=list_with_genres.id
    
--- WHERE GENRES - conditional ---
WHERE ',' || genres || ',' LIKE '%,crime,%'



ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
        
LIMIT :limit;
''', {'category': 'movie', 'decade': None, 'actor': None, 'director': None, 'origin': '_NOT_hu', 'lang': 'en', 'limit': 100}).fetchall()  



----------------------------------------------------
--- search by genre/theme/orig/ logical elements ---
--- traditional + left join with filters         ---
----------------------------------------------------

import sqlite3
con = sqlite3.connect("/home/akoel/.playem/playem.db")
                        

con.execute('''                       
SELECT
    list_with_genres.*,
    sounds,
    subs,
    directors,
    writers,
    voices,
    stars,
    actors
FROM
(
    SELECT
        list_with_themes.*,
        group_concat(genre.name) genres
    FROM
    (
        SELECT
            list_with_origins.*,
            group_concat(theme.name) themes
        FROM
        (
            SELECT
                list_with_appendix.*,
                group_concat(origin.name) origins
            FROM
            (
                SELECT
                    list_with_media_type.*,
                    group_concat(appendix_card.id) appendix
                FROM
                (
                    SELECT
                        raw_list.*,
                        group_concat( mt.name || "=" || cm.name) medium
                    FROM
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
                            
                            unioned.source_path
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

                                card.decade decade,
                                card.date date,
                                card.length length,
                                
                                card.source_path source_path
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
                        ) unioned, 
                
                        --- category - it is here regardless ---
                        Category cat 

                        WHERE           

                            --- category --- 
                            unioned.id_category=cat.id
                            AND cat.name=:category

                            --- decade - conditional ---
--                            AND unioned.decade='60s' OR unioned.decade='70s'

                        -- because of the title required and origin
                        GROUP BY unioned.id               
        
                    ) raw_list
                    LEFT JOIN Card_Media cm 
                        ON cm.id_card=raw_list.id
                        LEFT JOIN MediaType mt
                        ON cm.id_mediatype = mt.id
                    GROUP BY raw_list.id

                ) list_with_media_type
                LEFT JOIN Card appendix_card 
                    ON appendix_card.id_higher_card = list_with_media_type.id
                    AND appendix_card.isappendix = 1
                GROUP BY list_with_media_type.id

            ) list_with_appendix
            LEFT JOIN Card_Origin co
                ON co.id_card=list_with_appendix.id
                INNER JOIN Country origin
                    ON co.id_origin=origin.id 
            GROUP BY list_with_appendix.id

        ) list_with_origins
        LEFT JOIN Card_Theme ct
            ON ct.id_card=list_with_origins.id
            INNER JOIN Theme theme
                ON ct.id_theme=theme.id

        --- WHERE ORIGIN - conditional ---
        WHERE ',' || origins || ',' LIKE '%,us,%'
        GROUP BY list_with_origins.id

    ) list_with_themes
    LEFT JOIN Card_Genre cg
        ON cg.id_card=list_with_themes.id
        INNER JOIN Genre genre
            ON cg.id_genre=genre.id

    --- WHERE THEMES - conditional ---
--    WHERE ',' || themes || ',' LIKE '%,conspiracy,%' AND ',' || themes || ',' NOT LIKE '%,blabla,%'
    GROUP BY list_with_themes.id
    
) list_with_genres


LEFT JOIN 
    (SELECT group_concat(language.name) sounds, card_sound.id_card
        FROM 
            Language language,
            Card_Sound card_sound
        WHERE 
            card_sound.id_sound=language.id 
        GROUP BY card_sound.id_card
    ) snd
    ON snd.id_card=list_with_genres.id

LEFT JOIN
    (SELECT group_concat(language.name) subs, card_sub.id_card
        FROM 
            Language language,
            Card_Sub card_sub
        WHERE 
            card_sub.id_sub=language.id
        GROUP BY card_sub.id_card
    ) sb
    ON sb.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) directors,  card_dir.id_card
        FROM 
            Person person,
            Card_Director card_dir
        WHERE 
            card_dir.id_director = person.id
        GROUP BY card_dir.id_card
    ) dr
    ON dr.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) writers,  card_writer.id_card
        FROM 
            Person person,
            Card_Writer card_writer
        WHERE 
            card_writer.id_writer = person.id
        GROUP BY card_writer.id_card
    ) wr
    ON wr.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) voices,  card_voice.id_card
        FROM 
            Person person,
            Card_Voice card_voice
        WHERE 
            card_voice.id_voice = person.id
        GROUP BY card_voice.id_card
    ) vc
    ON vc.id_card=list_with_genres.id    

LEFT JOIN    
    (SELECT group_concat(person.name) stars,  card_star.id_card
        FROM 
            Person person,
            Card_Star card_star
        WHERE 
            card_star.id_star = person.id
        GROUP BY card_star.id_card
    ) str
    ON str.id_card=list_with_genres.id
    
LEFT JOIN    
    (SELECT group_concat(person.name) actors,  card_actor.id_card
        FROM 
            Person person,
            Card_Actor card_actor
        WHERE 
            card_actor.id_actor = person.id
        GROUP BY card_actor.id_card
    ) act
    ON act.id_card=list_with_genres.id
    
--- WHERE GENRES - conditional ---
WHERE ',' || genres || ',' LIKE '%,crime,%'

--- WHERE ACTORS - conditional ---
AND ',' || actors || ',' LIKE '%,Willem Dafoe,%'

--- WHERE DIRECTORS - conditional ---
AND ',' || directors || ',' LIKE '%,David Lynch,%' OR ',' || directors || ',' LIKE '%,Spike Lee,%'


ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
        
LIMIT :limit;
''', {'category': 'movie', 'decade': None, 'actor': None, 'director': None, 'origin': '_NOT_hu', 'lang': 'en', 'limit': 100}).fetchall()  



----------------------------------------------------
--- search by genre/theme/orig/ logical elements ---
--- traditional + left join with filters         ---
----------------------------------------------------

import sqlite3
con = sqlite3.connect("/home/akoel/.playem/playem.db")
                        
                        
con.execute('''
    SELECT
        list_with_genres.*,
        sounds,
        subs,
        directors,
        writers,
        voices,
        stars,
        actors,
        genres,
        themes,
        origins,
        appendix,
        medium
                    FROM
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
                            
                            unioned.source_path
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

                                card.decade decade,
                                card.date date,
                                card.length length,
                                
                                card.source_path source_path
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
                        ) unioned, 
                
                        --- category - it is here regardless ---
                        Category cat 

                        WHERE           

                            --- category --- 
                            unioned.id_category=cat.id
                            AND cat.name=:category

                            --- decade - conditional ---
--                            AND unioned.decade='60s' OR unioned.decade='70s' OR unioned.decade='80s' OR unioned.decade='90s' OR unioned.decade='2000s' OR unioned.decade='2010s'
                            
                            --- date - conditional ---
                            AND unioned.date = '1995'

                        -- because of the title required and origin
                        GROUP BY unioned.id               
        

                      ) list_with_genres

LEFT JOIN
    (SELECT group_concat( media_type.name || "=" || card_media.name) medium, card_media.id_card
    FROM
        MediaType media_type,
        Card_Media card_media
    WHERE
        card_media.id_mediatype=media_type.id
    GROUP BY card_media.id_card
    )mdt
    ON mdt.id_card=list_with_genres.id

LEFT JOIN
    (SELECT group_concat(appendix_card.id) appendix, appendix_card.id_higher_card
    FROM
        Card appendix_card        
    WHERE
        appendix_card.isappendix=1
    GROUP BY appendix_card.id_higher_card
    )pndx
    ON pndx.id_higher_card=list_with_genres.id
   
LEFT JOIN
    (SELECT group_concat(origin.name) origins, card_origin.id_card
    FROM
        Country origin,
        Card_Origin card_origin
    WHERE
        card_origin.id_origin=origin.id
    GROUP BY card_origin.id_card
    )rgn
    ON rgn.id_card=list_with_genres.id

LEFT JOIN 
    (SELECT group_concat(theme.name) themes, card_theme.id_card
        FROM
            Theme theme,
            Card_Theme card_theme
        WHERE            
            card_theme.id_theme=theme.id
        GROUP BY card_theme.id_card
    )thm
    ON thm.id_card=list_with_genres.id

LEFT JOIN 
    (SELECT group_concat(genre.name) genres, card_genre.id_card
        FROM
            Genre genre,
            Card_Genre card_genre
        WHERE            
            card_genre.id_genre=genre.id
        GROUP BY card_genre.id_card
    )gnr
    ON gnr.id_card=list_with_genres.id
    
LEFT JOIN 
    (SELECT group_concat(language.name) sounds, card_sound.id_card
        FROM 
            Language language,
            Card_Sound card_sound
        WHERE 
            card_sound.id_sound=language.id 
        GROUP BY card_sound.id_card
    ) snd
    ON snd.id_card=list_with_genres.id

LEFT JOIN
    (SELECT group_concat(language.name) subs, card_sub.id_card
        FROM 
            Language language,
            Card_Sub card_sub
        WHERE 
            card_sub.id_sub=language.id
        GROUP BY card_sub.id_card
    ) sb
    ON sb.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) directors,  card_dir.id_card
        FROM 
            Person person,
            Card_Director card_dir
        WHERE 
            card_dir.id_director = person.id
        GROUP BY card_dir.id_card
    ) dr
    ON dr.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) writers,  card_writer.id_card
        FROM 
            Person person,
            Card_Writer card_writer
        WHERE 
            card_writer.id_writer = person.id
        GROUP BY card_writer.id_card
    ) wr
    ON wr.id_card=list_with_genres.id

LEFT JOIN    
    (SELECT group_concat(person.name) voices,  card_voice.id_card
        FROM 
            Person person,
            Card_Voice card_voice
        WHERE 
            card_voice.id_voice = person.id
        GROUP BY card_voice.id_card
    ) vc
    ON vc.id_card=list_with_genres.id    

LEFT JOIN    
    (SELECT group_concat(person.name) stars,  card_star.id_card
        FROM 
            Person person,
            Card_Star card_star
        WHERE 
            card_star.id_star = person.id
        GROUP BY card_star.id_card
    ) str
    ON str.id_card=list_with_genres.id
    
LEFT JOIN    
    (SELECT group_concat(person.name) actors,  card_actor.id_card
        FROM 
            Person person,
            Card_Actor card_actor
        WHERE 
            card_actor.id_actor = person.id
        GROUP BY card_actor.id_card
    ) act
    ON act.id_card=list_with_genres.id
    
    
--- WHERE ORIGIN - conditional ---
--WHERE ',' || origins || ',' LIKE '%,us,%'

--- WHERE THEMES - conditional ---
AND ',' || themes || ',' LIKE '%,maffia,%'

--- WHERE GENRES - conditional ---
--AND ',' || genres || ',' LIKE '%,crime,%'

--- WHERE ACTORS - conditional ---
--AND ',' || actors || ',' LIKE '%,Robert De Niro,%'

--- WHERE DIRECTORS - conditional ---
--AND ',' || directors || ',' LIKE '%,Martin Scorsese,%'


ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
        
LIMIT :limit;
''', {'category': 'movie', 'decade': None, 'actor': None, 'director': None, 'origin': '_NOT_hu', 'lang': 'en', 'limit': 100}).fetchall()





----------------------------------------------------
--- search by genre/theme/orig/ logical elements ---
--- traditional + left join with filters         ---
----------------------------------------------------

import sqlite3
con = sqlite3.connect("/home/akoel/.playem/playem.db")
                        
                        
con.execute('''
    SELECT
        core.*,

        storyline,
        lyrics,

        sounds,
        subs,
        directors,
        writers,
        voices,
        stars,
        actors,
        
        hosts,
        guests,
--        interviewers,
--        interviewees,
--        presenters,
--        reporters,
--        lecturers,
--        performers,
        
        genres,
        themes,
        origins,
        appendix,
        medium
                    FROM
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

                                card.decade decade,
                                card.date date,
                                card.length length,
                                
                                card.source_path source_path
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
                        ) unioned

                        -- because of the title required and origin
                        GROUP BY unioned.id               

                      ) core, Category cat

                      
    --- STORYLINE ---
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

    
    --- LYRICS ---
    LEFT JOIN
    (
        SELECT ord, lyrics, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

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

            --- Select the storyline on the original language ---

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
--        HAVING MIN(ord)
--        ORDER BY ord
    )lrx
    ON lrx.id_card=core.id    

    
    --- MEDIUM ---                  
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

    --- APPENDIX ---
    LEFT JOIN
    (
        SELECT group_concat(appendix_card.id) appendix, appendix_card.id_higher_card
        FROM
            Card appendix_card        
        WHERE
            appendix_card.isappendix=1
        GROUP BY appendix_card.id_higher_card
    )pndx
    ON pndx.id_higher_card=core.id
   
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
    ON rgn.id_card=core.id

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
    ON thm.id_card=core.id

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
    ON gnr.id_card=core.id
    
    --- SOUNDS ---
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

    --- SUBTITLE ---
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
    ON dr.id_card=core.id

    --- WRITERS ---
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

    --- VOICES ---
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

    --- STARS ---
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
    ON act.id_card=core.id

    
    
    

    --- HOSTS ---
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
    
    --- GUESTS ---
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

        --- category --- 
        core.id_category=cat.id
        AND cat.name=:category

        --- decade - conditional ---
        AND core.decade=:decade
                            
        --- date - conditional ---
        AND core.date = :date
  
    
    
--- WHERE ORIGIN - conditional ---
--AND ',' || origins || ',' LIKE '%,us,%'

--- WHERE THEMES - conditional ---
--AND ',' || themes || ',' LIKE '%,maffia,%'

--- WHERE GENRES - conditional ---
AND ',' || genres || ',' LIKE '%,drama,%'

--- WHERE ACTORS - conditional ---
--AND ',' || actors || ',' LIKE '%,Robert De Niro,%'

--- WHERE DIRECTORS - conditional ---
--AND ',' || directors || ',' LIKE '%,Martin Scorsese,%'


ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
        
LIMIT :limit;
''', {'category': 'movie', 'date': '1995', 'decade': '90s', 'actor': None, 'director': None, 'origin': '_NOT_hu', 'lang': 'hu', 'limit': 100}).fetchall()






---------------------------------------------------------
--- Read the storyline                                ---
---                                                   ---
--- On the requested language if there is             ---
--- On the original language if no requested language ---
---------------------------------------------------------
    
con.execute('''
SELECT ord, storyline, id_card
FROM Card core
LEFT JOIN
(
    SELECT ord, storyline, id_card
    FROM
    (

        --- Select the storyline on the requested language, not the original ---

        SELECT "1" as ord, tcl.text as storyline, card.id id_card
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

        SELECT "2" as ord, tcl.text as storyline, card.id id_card
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
--    HAVING MIN(ord)
--    ORDER BY ord
)strl
ON strl.id_card=core.id
 
WHERE core.id=:card_id

 
''', {'card_id': '117', 'category': 'movie', 'date': '1995', 'decade': '90s', 'actor': None, 'director': None, 'origin': '_NOT_hu', 'lang': 'it', 'limit': 20}).fetchall()
    

    
---------------------------------------------------------
--- Read the appendix                                 ---
---                                                   ---
---------------------------------------------------------    

  
--- part test ---

con.execute('''
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
--                    AND card.id_higher_card=core.id 
                    AND lang.name=:lang
                ) merged_appendix,
                Card_Media cm,
                MediaType mt
                
            WHERE
--                merged_appendix.card_id=2
                cm.id_card=merged_appendix.id
                AND mt.id=cm.id_mediatype
                
            GROUP BY merged_appendix.id
            )
        GROUP BY card_id
                
''', {'core_id': '2', 'category': 'movie', 'date': '1995', 'decade': '90s', 'actor': None, 'director': None, 'origin': '_NOT_hu', 'lang': 'en', 'limit': 20}).fetchall()
  
      
------------------------      
--- WORKING SOLUTION ---
------------------------


con.execute('''
    SELECT
        core.*,

        storyline,
        lyrics,

        sounds,
        subs,
        directors,
        writers,
        voices,
        stars,
        actors,
        
        hosts,
        guests,
--        interviewers,
--        interviewees,
--        presenters,
--        reporters,
--        lecturers,
--        performers,
        
        genres,
        themes,
        origins,
        appendix,
        medium
                    FROM
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

                                card.decade decade,
                                card.date date,
                                card.length length,
                                
                                card.source_path source_path
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
                        ) unioned

                        -- because of the title required and origin
                        GROUP BY unioned.id               

                    ) core, Category cat

                      
    --- STORYLINE ---
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

    
    --- LYRICS ---
    LEFT JOIN
    (
        SELECT ord, lyrics, id_card
        FROM
        (

            --- Select the storyline on the requested language, not the original ---

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

            --- Select the storyline on the original language ---

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
--        HAVING MIN(ord)
--        ORDER BY ord
    )lrx
    ON lrx.id_card=core.id    
    
    --- MEDIUM ---                  
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

    --- APPENDIX ---    
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
    ON rgn.id_card=core.id

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
    ON thm.id_card=core.id

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
    ON gnr.id_card=core.id
    
    --- SOUNDS ---
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

    --- SUBTITLE ---
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
    ON dr.id_card=core.id

    --- WRITERS ---
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

    --- VOICES ---
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

    --- STARS ---
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
    ON act.id_card=core.id

    --- HOSTS ---
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
    
    --- GUESTS ---
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

        --- category --- 
        core.id_category=cat.id
        AND cat.name=:category

        --- decade - conditional ---
        AND core.decade=:decade
                            
        --- date - conditional ---
--        AND core.date = :date
    
        --- WHERE ORIGIN - conditional ---
--        AND ',' || origins || ',' LIKE '%,us,%'

        --- WHERE THEMES - conditional ---
--        AND ',' || themes || ',' LIKE '%,maffia,%'

        --- WHERE GENRES - conditional ---
        AND ',' || genres || ',' LIKE '%,scifi,%'

        --- WHERE ACTORS - conditional ---
--        AND ',' || actors || ',' LIKE '%,Robert De Niro,%'

        --- WHERE DIRECTORS - conditional ---
--        AND ',' || directors || ',' LIKE '%,Martin Scorsese,%'


ORDER BY CASE WHEN title_req IS NOT NULL THEN title_req ELSE title_orig END
        
LIMIT :limit;
''', {'category': 'movie', 'date': None, 'decade': '60s', 'actor': None, 'director': None, 'origin': '_NOT_hu', 'lang': 'hu', 'limit': 100}).fetchall()



