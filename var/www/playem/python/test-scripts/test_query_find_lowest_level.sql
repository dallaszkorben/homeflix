---------------------------------------------------------------
--- FULL QUERY for lowest (medium) level list               ---
--- Returns only medium level cards level cards             ---
--- With filters category/genre/theme/origin/director/actor ---
---                                                         ---
--- query_lowest_level()                                    ---
---------------------------------------------------------------




con.execute('''
    
SELECT 
    recursive_list.*,

    category.name category,
    themes,
    genres,
    origins,
    directors,
    actors,

    sounds,
    subs,
    writers,
    voices,
    stars,
    lecturers,
    
    hosts,
    guests,
    interviewers,
    interviewees,
    presenters,
    reporters,
    performers,
    
    storyline,
    lyrics,
    medium,
    appendix
FROM
    (
    WITH RECURSIVE
        rec(id, id_higher_card,level, source_path, title_req, title_orig, lang_orig, lang_req, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, ord) AS
        
        (
            SELECT
            
                card.id, 
                card.id_higher_card, 
                card.level,
                card.source_path,
                
                core.title_req, 
                core.title_orig, 
                core.lang_orig,
                core.lang_req,
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                NULL decade,
                NULL date,
                NULL length,
              
                CASE 
                    WHEN sequence IS NULL AND core.title_req IS NOT NULL THEN core.title_req
                    WHEN sequence IS NULL AND core.title_orig IS NOT NULL THEN core.title_orig
                    WHEN sequence<0 THEN basename
                END ord

            FROM 
                Card card,
                
                (
                SELECT 
                    unioned.id id,
                
                    MAX(title_req) title_req, 
                    MAX(title_orig) title_orig, 
                    MAX(lang_orig) lang_orig,
                    MAX(lang_req) lang_req

                FROM 
                    (
                    SELECT 
                        card.id id, 

                        NULL title_req, 
                        NULL lang_req, 
                        tcl.text title_orig, 
                        lang.name lang_orig
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

                        tcl.text title_req, 
                        lang.name lang_req, 
                        NULL title_orig, 
                        NULL lang_orig
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

                ) core,               
                
                
                --- Conditional ---
                Category category
            
            ------------------------
            --- Initial WHERE    ---
            --- the lowest level ---
            ------------------------
            
            WHERE 

                core.id = card.id
            
                -- connect card to category --
                AND category.id=card.id_category

                -- card can not be appendix --
                AND card.isappendix == 0

                -- Find the highest level --
                --- if :level is set, then takes that specific level as highest level
                --- if :level is NOT set, then takes the highest level
                AND CASE
                    WHEN :level IS NULL THEN id_higher_card IS NULL ELSE card.level = :level
                END                
   
                -- Select the given category --
                AND category.name = :category
                
            UNION ALL

            SELECT                
                card.id,
                card.id_higher_card,
                card.level,
                card.source_path,
                
                core.title_req, 
                core.title_orig, 
                core.lang_orig,
                core.lang_req,                
                
                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,
                
                card.decade,
                card.date,
                card.length,     
                
                CASE 
                    WHEN card.sequence IS NULL AND core.title_req IS NOT NULL THEN ord || '_' || core.title_req
                    WHEN card.sequence IS NULL AND core.title_orig IS NOT NULL THEN ord || '_' || core.title_orig
                    WHEN card.sequence<0 THEN ord || '_' || card.basename
                    WHEN card.sequence>=0 THEN ord || '_' || card.sequence
                END ord                
  
            FROM
                rec,
                Card card,
                
                
                (
                SELECT 
                    unioned.id id,
                
                    MAX(title_req) title_req, 
                    MAX(title_orig) title_orig, 
                    MAX(lang_orig) lang_orig,
                    MAX(lang_req) lang_req

                FROM 
                    (
                    SELECT 
                        card.id id, 

                        NULL title_req, 
                        NULL lang_req, 
                        tcl.text title_orig, 
                        lang.name lang_orig
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

                        tcl.text title_req, 
                        lang.name lang_req, 
                        NULL title_orig, 
                        NULL lang_orig
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
                
                
            WHERE
 
                card.id_higher_card=rec.id
                AND core.id = card.id

        )
    SELECT id, id_higher_card, level, source_path, title_req, title_orig, lang_orig, lang_req, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, ord
    
    FROM
        rec
    WHERE

        level IS NULL

    GROUP BY id
   
    ) recursive_list,
    Card card,
    Category category
    
    -------------
    --- GENRE ---
    -------------
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
            
    -------------
    --- THEME ---
    -------------
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
    
    ---------------
    --- ORIGINS ---
    ---------------
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
    
    -----------------
    --- DIRECTORS ---
    -----------------
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

    --------------
    --- ACTORS ---
    --------------
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
       
    ----------------
    --- LECTURER ---
    ----------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) lecturers,  card_lecturer.id_card
        FROM 
            Person person,
            Card_Lecturer card_lecturer
        WHERE 
            card_lecturer.id_lecturer = person.id
        GROUP BY card_lecturer.id_card
    ) lctr
    ON lctr.id_card=card.id       
       
    --- No filter ---
       
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
    ON snd.id_card=card.id

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
    ON sb.id_card=card.id

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
    ON wr.id_card=card.id

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
    ON vc.id_card=card.id

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
    ON str.id_card=card.id

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
    ON hst.id_card=card.id
    
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
    ON gst.id_card=card.id

    ---------------------
    --- INTERWIEVERS  ---
    ---------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) interviewers,  card_interviewer.id_card
        FROM 
            Person person,
            Card_Interviewer card_interviewer
        WHERE 
            card_interviewer.id_interviewer = person.id
        GROUP BY card_interviewer.id_card
    ) ntrvwr
    ON ntrvwr.id_card=card.id

    ---------------------
    --- INTERVIEWEES  ---
    ---------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) interviewees,  card_interviewee.id_card
        FROM 
            Person person,
            Card_Interviewee card_interviewee
        WHERE 
            card_interviewee.id_interviewee = person.id
        GROUP BY card_interviewee.id_card
    ) ntrw
    ON ntrw.id_card=card.id

    -------------------
    --- PRESENTERS  ---
    -------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) presenters,  card_presenter.id_card
        FROM 
            Person person,
            Card_Presenter card_presenter
        WHERE 
            card_presenter.id_presenter = person.id
        GROUP BY card_presenter.id_card
    ) prsntr
    ON prsntr.id_card=card.id

    ------------------
    --- REPORTERS  ---
    ------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) reporters,  card_reporter.id_card
        FROM 
            Person person,
            Card_Reporter card_reporter
        WHERE 
            card_reporter.id_reporter = person.id
        GROUP BY card_reporter.id_card
    ) rprtr
    ON rprtr.id_card=card.id
    
    ------------------
    --- PERFORMER  ---
    ------------------
    LEFT JOIN    
    (
        SELECT group_concat(person.name) performers,  card_performer.id_card
        FROM 
            Person person,
            Card_Performer card_performer
        WHERE 
            card_performer.id_performer = person.id
        GROUP BY card_performer.id_card
    ) prfrmr
    ON prfrmr.id_card=card.id    
    
    ---
    
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
    ON strl.id_card=card.id
   
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
    ON lrx.id_card=card.id       
   
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
    ON mdt.id_card=card.id
   
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
    ON pndx.card_id=card.id     

WHERE
    card.id=recursive_list.id
    AND category.id=card.id_category
    
    -------------------
    -------------------
    --- Conditional ---
    ---   filter    ---
    -------------------
    -------------------

    --- WHERE DECADE ---
    AND CASE
        WHEN :decade IS NOT NULL THEN card.decade = :decade ELSE 1
    END
                
    --- WHERE THEMES - conditional ---
    AND CASE
        WHEN :theme IS NOT NULL THEN ',' || themes || ',' LIKE '%,' || :theme || ',%' ELSE 1
    END
                
    --- WHERE GENRES - conditional ---
    AND CASE
        WHEN :genre IS NOT NULL THEN ',' || genres || ',' LIKE '%,' || :genre || ',%' ELSE 1
    END    
    
    --- WHERE DIRECTORS - conditional ---
    AND CASE
        WHEN :director IS NOT NULL THEN ',' || directors || ',' LIKE '%,' || :director || ',%' ELSE 1
    END
                
    --- WHERE ACTORS - conditional ---
    AND CASE
        WHEN :actor IS NOT NULL THEN ',' || actors || ',' LIKE '%,' || :actor || ',%' ELSE 1
    END

    --- WHERE ORIGINS - conditional ---
    AND CASE
        WHEN :origin IS NOT NULL THEN ',' || origins || ',' LIKE '%,' || :origin || ',%' ELSE 1
    END

    --- WHERE LECTURERS - conditional ---
    AND CASE
        WHEN :lecturer IS NOT NULL THEN ',' || lecturers || ',' LIKE '%,' || :lecturer || ',%' ELSE 1
    END

ORDER BY ord
      
    
''', {'level': None, 'category': 'movie', 'genre': 'scifi', 'theme': 'alien', 'origin': 'us', 'director': None, 'actor': None, 'lecturer': None, 'decade': None, 'lang': 'en'}).fetchall()



