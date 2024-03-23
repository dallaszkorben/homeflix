---------------------------------------------------------------
--- FULL QUERY for lowest (medium) level list               ---
--- Returns only medium level cards level cards             ---
--- With filters category/genre/theme/origin/director/actor ---
---                                                         ---
--- query_lowest_level()                                    ---
---------------------------------------------------------------

con.execute('''
SELECT
    core.*,
    lowest_id_list.themes,
    lowest_id_list.genres,
    lowest_id_list.origins,
    lowest_id_list.directors,
    lowest_id_list.actors,

    lowest_id_list.sounds,
    lowest_id_list.subs,
    lowest_id_list.writers,
    lowest_id_list.voices,
    lowest_id_list.stars,
    lowest_id_list.lecturers,
    
    lowest_id_list.hosts,
    lowest_id_list.guests,
    lowest_id_list.interviewers,
    lowest_id_list.interviewees,
    lowest_id_list.presenters,
    lowest_id_list.reporters,
    lowest_id_list.performers

    storyline,
    lyrics,
    medium,
    appendix
    
FROM

    ----------------------------
    --- lowest level id list ---
    ----------------------------
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
        actors, 
        lecturers,

        sounds,
        subs,
        writers,
        voices,
        stars,        
        hosts,
        guests,
        interviewers,
        interviewees,
        presenters,
        reporters,
        performers
        
    FROM 
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
       
        --- WHERE ---

        WHERE 
            card.isappendix == 0
            AND card.level IS NULL
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
--            AND ',' || directors || ',' LIKE '%,' || :director || ',%'
                
            --- WHERE ACTORS - conditional ---
--            AND ',' || actors || ',' LIKE '%,' || :actor || ',%'

            --- WHERE LECTURERS - conditional ---
--            AND ',' || lecturers || ',' LIKE '%,' || :lecturer || ',%'

            --- WHERE ORIGINS - conditional ---
--            AND ',' || origins || ',' LIKE '%,' || :origin || ',%'

    ) lowest_id_list,
    
    --------------------------
    --- unioned with title ---
    --------------------------
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
--        unioned.id_category,
        unioned.basename basename
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
                                
            card.source_path source_path,
            card.basename basename
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
                                
            card.source_path source_path,
            card.basename basename
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
  
   
WHERE
    lowest_id_list.id=core.id
ORDER BY CASE 
    WHEN title_show_sequence IS NULL AND title_req IS NOT NULL THEN title_req
    WHEN title_show_sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
    WHEN title_show_sequence<0 THEN basename
    WHEN title_show_sequence>=0 THEN title_show_sequence
END    

''', {'category': 'movie', 'genre': 'scifi', 'theme': 'ai', 'origin': 'us', 'director': 'Ridley Scott', 'actor': '*', 'lang': 'en'}).fetchall()
---''', {'category': 'entertainment', 'genre': 'skit', 'theme': '*', 'origin': '*', 'director': '*', 'actor': '*', 'lecturer': '*', 'lang': 'en'}).fetchall()


