
#
# start python
#
# cd /var/www/playem/python
$ source /var/www/playem/python/env/bin/activate
$ python3


#
# intitialization
#
import sqlite3
from playem.card.database import SqlDatabase as DB
db=DB(None)
con = sqlite3.connect("/home/akoel/.playem/playem.db")


--------------------------------------------------------
--- FULL QUERY for highest level list                ---
--- Returns mixed standalone media and level cards   ---
--- With filters category/genre                      ---
---                                                  ---
--- Why need to use recursive search?                ---
--- Because I filter by the lower level card (media) ---
--- but I show the highest                           ---
---                                                  ---
--- gurey_highest_level_mixed()                      ---
--------------------------------------------------------

con.execute('''
SELECT
    core.*,

    mixed_id_list.id_higher_card,
    mixed_id_list.category,
    mixed_id_list.level,
    mixed_id_list.source_path,
    mixed_id_list.basename,
    mixed_id_list.sequence,

    mixed_id_list.title_on_thumbnail,
    mixed_id_list.title_show_sequence,

    mixed_id_list.decade,
    mixed_id_list.date,
    mixed_id_list.length,
    mixed_id_list.full_time,
    mixed_id_list.net_start_time,
    mixed_id_list.net_stop_time,

    mixed_id_list.themes,
    mixed_id_list.genres,
    mixed_id_list.origins,
    mixed_id_list.directors,
    mixed_id_list.actors,

    mixed_id_list.sounds,
    mixed_id_list.subs,
    mixed_id_list.writers,
    mixed_id_list.voices,
    mixed_id_list.stars,
    mixed_id_list.lecturers,

    mixed_id_list.hosts,
    mixed_id_list.guests,
    mixed_id_list.interviewers,
    mixed_id_list.interviewees,
    mixed_id_list.presenters,
    mixed_id_list.reporters,
    mixed_id_list.performers,

    strl.ord,
    strl.storyline,
    lyrics,
    medium,
    appendix

FROM

    ---------------------------
    --- mixed level id list ---
    ---------------------------
    (
    WITH RECURSIVE
        rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, recent_state, rate, skip_continuous_play, tags) AS

        (
            SELECT
                card.id,
                card.id_higher_card,
                category.name category,
                card.level,
                card.source_path,

                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,

                card.decade,
                card.date,
                card.length,
                card.full_time,
                card.net_start_time,
                card.net_stop_time,

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
                performers,

                hstr.recent_state, rtng.rate, rtng.skip_continuous_play, tggng.tags

            FROM
                Card card,

                --- Conditional ---
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

            --- No Filter ---

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
            --- INTERVIEWERS  ---
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

            ---------------
            --- HISTORY ---
            ---------------
            LEFT JOIN
            (
                SELECT
                    ('start_epoch=' || start_epoch || ';recent_epoch=' || recent_epoch || ';recent_position=' || recent_position || ';play_count=' || count(*) ) recent_state,
                    id_card,
                    start_epoch,
                    recent_position
                FROM (
                    SELECT id_card, start_epoch, recent_epoch, recent_position
                    FROM History
                    WHERE id_user=:user_id
                    ORDER BY start_epoch DESC
                )
                GROUP BY id_card
            )hstr
            ON hstr.id_card=card.id

            --------------
            --- RATING ---
            --------------
            LEFT JOIN
            (
                SELECT
                    id_card,
                    rate,
                    skip_continuous_play
                FROM Rating
                WHERE id_user=:user_id
            )rtng
            ON rtng.id_card=card.id

            ---------------
            --- TAGGING ---
            ---------------
            LEFT JOIN
            (
               SELECT
                  group_concat(name) tags,
                  id_card
               FROM
                  Tag tag
               WHERE
                  id_user=:user_id
               GROUP BY id_card
            ) tggng
            ON tggng.id_card=card.id

            ------------------------
            --- Initial WHERE    ---
            --- the lowest level ---
            ------------------------

            WHERE
                -- card can not be appendix --
                card.isappendix == 0

                -- connect card to category --
                AND category.id=card.id_category

                -- Find the lowest level --
                AND card.level IS NULL

                -- Select the given category --
                AND category.name = :category

                -------------------
                -------------------
                --- Conditional ---
                ---   filter    ---
                -------------------
                -------------------

                --- WHERE HISTORY ---
                AND CASE
                    WHEN :view_state = 'interrupted' THEN
                        hstr.start_epoch >= :history_back
                        AND hstr.recent_position < card.net_stop_time
                        AND hstr.recent_position > card.net_start_time
                    WHEN :view_state = 'last_watched' THEN
                        hstr.start_epoch >= :history_back
                    WHEN :view_state = 'most_watched' THEN
                        hstr.start_epoch >= :history_back
                        AND hstr.recent_position > card.net_start_time
                    ELSE 1
                END

                --- WHERE DECADE ---
                -- AND card.decade = :decade
                AND CASE
                    WHEN :decade IS NOT NULL THEN card.decade = :decade ELSE 1
                END

                --- WHERE THEMES - conditional ---
                -- AND ',' || themes || ',' LIKE '%,' || :theme || ',%'
                AND CASE
                    WHEN :theme IS NOT NULL THEN ',' || themes || ',' LIKE '%,' || :theme || ',%' ELSE 1
                END

                --- WHERE GENRES - conditional ---
                -- AND ',' || genres || ',' LIKE '%,' || :genre || ',%'
                AND CASE
                    WHEN :genre IS NOT NULL THEN ',' || genres || ',' LIKE '%,' || :genre || ',%' ELSE 1
                END

                --- WHERE DIRECTORS - conditional ---
                -- AND ',' || directors || ',' LIKE '%,' || :director || ',%'
                AND CASE
                    WHEN :director IS NOT NULL THEN ',' || directors || ',' LIKE '%,' || :director || ',%' ELSE 1
                END

                --- WHERE ACTORS - conditional ---
                -- AND ',' || actors || ',' LIKE '%,' || :actor || ',%'
                AND CASE
                    WHEN :actor IS NOT NULL THEN ',' || actors || ',' LIKE '%,' || :actor || ',%' ELSE 1
                END

                --- WHERE ORIGINS - conditional ---
                -- AND ',' || origins || ',' LIKE '%,' || :origin || ',%'
                AND CASE
                    WHEN :origin IS NOT NULL THEN ',' || origins || ',' LIKE '%,' || :origin || ',%' ELSE 1
                END

                --- WHERE LECTURERS - conditional ---
                -- AND ',' || lecturers || ',' LIKE '%,' || :lecturer || ',%'
                AND CASE
                    WHEN :lecturer IS NOT NULL THEN ',' || lecturers || ',' LIKE '%,' || :lecturer || ',%' ELSE 1
                END

            UNION ALL

            SELECT
                card.id,
                card.id_higher_card,
                category.name category,
                card.level,
                card.source_path,

                card.basename,
                card.sequence,
                card.title_on_thumbnail,
                card.title_show_sequence,

                NULL decade,
                NULL date,
                NULL length,
                NULL full_time,
                NULL net_start_time,
                NULL net_stop_time,

                NULL themes,
                NULL genres,
                NULL origins,
                NULL directors,
                NULL actors,
                NULL lecturers,
                NULL sounds,
                NULL subs,
                NULL writers,
                NULL voices,
                NULL stars,
                NULL hosts,
                NULL guests,
                NULL interviewers,
                NULL interviewees,
                NULL presenters,
                NULL reporters,
                NULL performers,

                NULL recent_state,
                NULL rate,
                NULL skip_continuous_play,
                NULL tags

            FROM
                rec,
                Card card,
                Category category
            WHERE
                rec.id_higher_card=card.id
                AND category.id=card.id_category
        )
    SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, recent_state, rate, skip_continuous_play, tags

    FROM
        rec
    WHERE

        -------------------
        -------------------
        --- Conditional ---
        ---   filter    ---
        -------------------
        -------------------

        --- if :level is set, then takes that specific level as highest level
        --- if :level is NOT set, then takes the highest level
        CASE
            WHEN :level IS NULL THEN id_higher_card IS NULL ELSE level = :level
        END

    GROUP BY id
    ) mixed_id_list,

    --------------------------
    --- unioned with title ---
    --------------------------
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
    mixed_id_list.id=core.id

ORDER BY CASE
    WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
    WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
    WHEN sequence<0 THEN basename
    WHEN sequence>=0 THEN sequence
END

''', {'user_id': 1234, 'history_back': 0, 'view_state': 'interrupted', 'level': None, 'category': 'movie', 'genre': None, 'theme': None, 'origin': None, 'director': None, 'actor': None, 'lecturer': None, 'decade': None, 'lang': 'en'}).fetchall()




-- Only sequels
--''', {'level': None, 'category': 'movie', 'genre': 'scifi', 'theme': None, 'origin': None, 'director': 'Ridley Scott', 'actor': None, 'lecturer': None, 'decade': '80s', 'lang': 'en'}).fetchall()

-- ONly 1 movie
--''', {'user_id': 1235, 'level': None, 'category': 'movie', 'genre': 'scifi', 'theme': None, 'origin': None, 'director': 'John Carpenter', 'actor': 'Kurt Russell', 'lecturer': None, 'decade': '80s', 'lang': 'en'}).fetchall()

--''', {'level': 'sequel', 'category': 'movie', 'genre': 'scifi', 'theme': 'alien', 'origin': 'us', 'director': None, 'actor': None, 'lecturer': None, 'decade': None, 'lang': 'en'}).fetchall()
--''', {'level': 'series', 'category': 'movie', 'genre': None, 'theme': None, 'origin': None, 'director': None, 'actor': None, 'lecturer': None, 'decade': None, 'lang': 'it'}).fetchall()
--''', {'level': None, 'category': 'movie', 'genre': 'scifi', 'theme': 'alien', 'origin': 'us', 'director': None, 'actor': None, 'lecturer': None, 'decade': None, 'lang': 'en'}).fetchall()
--''', {'category': 'movie', 'genre': 'scifi', 'theme': 'ai', 'origin': 'us', 'director': 'Ridley Scott', 'actor': '*', 'decade': '90s', 'lang': 'en'}).fetchall()
--''', {'category': 'entertainment', 'genre': 'speech', 'theme': '*', 'origin': '*', 'director': '*', 'actor': '*', 'lecturer': '*', 'decade': '60s', 'lang': 'en'}).fetchall()


-- -------
--
-- HISTORY
--
-- -------

-- give back the latest history
res = con.execute('SELECT start_epoch, recent_epoch, recent_position FROM History WHERE id_card=:id_card AND id_user=:id_user ORDER BY start_epoch DESC LIMIT 1 ;',{'id_card': '0b2704fd17e87d003dd9364af90c9899', 'id_user': 1235})
for rec in res.fetchall():
    print(rec)

-- give back the latest history with concatenated result fields
--res = con.execute('SELECT (start_epoch || "|" || recent_epoch || "|" || recent_position) as history FROM History WHERE id_card=:id_card AND id_user=:id_user ORDER BY start_epoch DESC LIMIT 1 ;',{'id_card': '0b2704fd17e87d003dd9364af90c9899', 'id_user': 1235})
res = con.execute('SELECT ("{\'start_epoch\':" || start_epoch || ",\'recent_epoch\':" || recent_epoch || ",\'recent_position\':" || recent_position || "}") as recent_state FROM History WHERE id_card=:id_card AND id_user=:id_user ORDER BY start_epoch DESC LIMIT 1 ;',{'id_card': '0b2704fd17e87d003dd9364af90c9899', 'id_user': 1235})
for rec in res.fetchall():
    print(rec)

-- give back the latest history for ALL cards for a specific user
res = con.execute('''
    SELECT
        ('start_epoch=' || start_epoch || ';recent_epoch=' || recent_epoch || ';recent_position=' || recent_position || ';play_count=' || count(*) ) as recent_state,
--        ("{\'start_epoch\':" || start_epoch || ",\'recent_epoch\':" || recent_epoch || ",\'recent_position\':" || recent_position || ",\'play_count\':" || count(*) || "}") as recent_state
--        (start_epoch || "|" || recent_epoch || "|" || recent_position || "|" || count(*) ) as recent_state,
        id_card
    FROM (
        SELECT id_card, start_epoch, recent_epoch, recent_position
        FROM History
        WHERE id_user=:id_user
        ORDER BY start_epoch DESC
    )
    GROUP BY id_card;
    ''',{'id_card': '0b2704fd17e87d003dd9364af90c9899', 'id_user': 1234})
for rec in res.fetchall():
    print(rec)



-- ------
--
-- RATING
--
-- ------

curl -c cookies_1.txt --header "Content-Type: application/json" --request POST --data '{ "username": "default", "password": "default"}' http://localhost:80/auth/login
curl -b cookies_1.txt --header "Content-Type: application/json" --request POST --data '{ "card_id": "e663001a5066ca994d06621e22d332da", "rate": 2, "skip_continuous_play": 0}' http://localhost:80/personal/rating/update

res = con.execute('''
    SELECT id_card, rate, skip_continuous_play
    FROM Rating
    WHERE id_user=:id_user
    ''',{'id_card': 'e663001a5066ca994d06621e22d332da', 'id_user': 1235})
for rec in res.fetchall():
    print(rec)







--- Call directly the python database method:
db.get_highest_level_cards(1235, 'movie', genres='scifi', themes=None, origins=None, directors='John Carpenter', actors=None, lecturers=None, decade='80s')

db.get_next_level_cards(1235, 'bde37d4b910d053e72ca16bf88df9d64', 'movie', genres='scifi', themes=None, origins=None, directors='John Carpenter', actors=None, lecturers=None, decade='80s')

get_lowest_level_cards(1235, 'movie', genres='scifi', themes=None, origins=None, directors='John Carpenter', actors=None, lecturers=None, decade='80s')







--------------------------------------------
---         TITLE REQUESTED              ---
--- On the requested language, if exists ---
--------------------------------------------
res = con.execute('''

SELECT card.id, card.source_path, ttlrq.ttitle_req, llang_req
FROM
    Card card,
    Category category
--

    LEFT JOIN
    (
        SELECT tcl.id_card id_card, tcl.text ttitle_req, lang.name llang_req, lang.id lang_id
        FROM
            Text_Card_Lang tcl,
            Language lang
        WHERE
            tcl.id_language=lang.id
            AND tcl.type="T"

            AND lang.name = :lang
    ) ttlrq
    ON ttlrq.id_card=card.id AND ttlrq.lang_id=card.id_title_orig


WHERE
    category.id=card.id_category
    AND category.name='movie'

--    card.id=:id_card
--    CASE
--        WHEN :title IS NOT NULL AND ttitle_req IS NOT NULL THEN ttitle_req LIKE :title
--        WHEN :title IS NOT NULL THEN ttitle_orig LIKE :title
--        ELSE 0
--    END


    ''',{'id_card': '6d6c0ba21c7606819297c7e29d0ffdf9', 'id_user': 1235, 'title': 'A hal%', 'lang': 'hu'})
for rec in res.fetchall():
    print(rec)


--------------------------------------------------
---                 TITLE ORIG                ---
--- Orig language if other lang was requested ---
-------------------------------------------------

res = con.execute('''

SELECT *
FROM
    Card card
--
    LEFT JOIN
    (
        SELECT tcl.id_card id_card, tcl.text ttitle_orig, lang.name llang_orig, lang.id lang_id
        FROM
            Text_Card_Lang tcl,
            Language lang
        WHERE
            tcl.id_language=lang.idx`
            AND tcl.type="T"
            AND lang.name <> :lang
    ) ttlor
    ON ttlor.id_card=card.id AND ttlor.lang_id=card.id_title_orig
--
WHERE
    card.id=:id_card

    ''',{'id_card': '6d6c0ba21c7606819297c7e29d0ffdf9', 'id_user': 1235, 'lang': 'hu'})
for rec in res.fetchall():
    print(rec)



------------------------------
--- show fields of a table ---
------------------------------

con.execute('''
    PRAGMA table_info(Card);
    ''',{'id_card': '6d6c0ba21c7606819297c7e29d0ffdf9', 'id_user': 1235, 'lang': 'hu'}).fetchall()

-- multi language card id: '6d6c0ba21c7606819297c7e29d0ffdf9'


















res = con.execute('''
 SELECT
    title_req,
    title_orig
--                core.*,
--
--                mixed_id_list.id_higher_card,
--                mixed_id_list.category,
--                mixed_id_list.level,
--                mixed_id_list.source_path,
--                mixed_id_list.basename,
--                mixed_id_list.sequence,
--
--                mixed_id_list.title_on_thumbnail,
--                mixed_id_list.title_show_sequence,
--
--                mixed_id_list.decade,
--                mixed_id_list.date,
--                mixed_id_list.length,
--                mixed_id_list.full_time,
--                mixed_id_list.net_start_time,
--                mixed_id_list.net_stop_time,
--
--                mixed_id_list.themes,
--                mixed_id_list.genres,
--                mixed_id_list.origins,
--                mixed_id_list.directors,
--                mixed_id_list.actors,
--
--                mixed_id_list.sounds,
--                mixed_id_list.subs,
--                mixed_id_list.writers,
--                mixed_id_list.voices,
--                mixed_id_list.stars,
--                mixed_id_list.lecturers,
--
--               mixed_id_list.hosts,
--                mixed_id_list.guests,
--                mixed_id_list.interviewers,
--                mixed_id_list.interviewees,
--                mixed_id_list.presenters,
--                mixed_id_list.reporters,
--                mixed_id_list.performers,

--                storyline,
--                lyrics,
--                medium,
--                appendix

--                hstr.recent_state,
--                rtng.rate,
--                rtng.skip_continuous_play,
--                tggng.tags
            FROM

                ---------------------------
                --- mixed level id list ---
                ---------------------------
                (
                WITH RECURSIVE
                    rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, ttitle_req, llang_req, ttitle_orig, llang_orig) AS

                    (
                        SELECT
                            card.id,
                            card.id_higher_card,
                            category.name category,
                            card.level,
                            card.source_path,

                            card.basename,
                            card.sequence,
                            card.title_on_thumbnail,
                            card.title_show_sequence,

                            card.decade,
                            card.date,
                            card.length,
                            card.full_time,
                            card.net_start_time,
                            card.net_stop_time,

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
                            performers,

                            ttitle_req,
                            llang_req,
                            ttitle_orig,
                            llang_orig

                        FROM
                            Card card,

                            --- Conditional ---
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

                            --- No Filter ---

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
                            --- INTERVIEWERS  ---
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

                            --------------------------------------------
                            ---         TITLE REQUESTED              ---
                            --- On the requested language, if exists ---
                            --------------------------------------------
                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_req, lang.name llang_req, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name = :lang
                            ) ttlrq
                            ON ttlrq.id_card=card.id AND ttlrq.lang_id=card.id_title_orig

                            ----------------------------------------
                            ---           TITLE ORIG             ---
                            --- Orig if other lang was requested ---
                            ----------------------------------------

                            LEFT JOIN
                            (
                                SELECT tcl.id_card id_card, tcl.text ttitle_orig, lang.name llang_orig, lang.id lang_id
                                FROM
                                    Text_Card_Lang tcl,
                                    Language lang
                                WHERE
                                    tcl.id_language=lang.id
                                    AND tcl.type="T"

                                    AND lang.name <> :lang
                            ) ttlor
                            ON ttlor.id_card=card.id AND ttlor.lang_id=card.id_title_orig






















                        ------------------------
                        --- INITIAL WHERE    ---
                        --- the lowest level ---
                        ------------------------

                        WHERE
                            -- card can not be appendix --
                            card.isappendix == 0

                            -- connect card to category --
                            AND category.id=card.id_category

                            -- Find the lowest level --
                            AND card.level IS NULL

                            -- Select the given category --
                            AND category.name = :category

                            -------------------
                            -------------------
                            --- Conditional ---
                            ---   filter    ---
                            -------------------
                            -------------------

                            --- WHERE TITLE ---
--                            AND ttitle_req LIKE "The%"

                            AND CASE
                                -- there is
                                WHEN :title IS NOT NULL AND ttitle_req IS NOT NULL THEN ttitle_req LIKE :title
                                WHEN :title IS NOT NULL THEN ttitle_orig LIKE :title
                                ELSE 0
                            END

                            --- WHERE DECADE ---
                            AND CASE
                                WHEN :decade IS NOT NULL THEN card.decade = :decade ELSE 1
                            END















                        UNION ALL

                        SELECT
                            card.id,
                            card.id_higher_card,
                            category.name category,
                            card.level,
                            card.source_path,

                            card.basename,
                            card.sequence,
                            card.title_on_thumbnail,
                            card.title_show_sequence,

                            NULL decade,
                            NULL date,
                            NULL length,
                            NULL full_time,
                            NULL net_start_time,
                            NULL net_stop_time,

                            NULL themes,
                            NULL genres,
                            NULL origins,
                            NULL directors,
                            NULL actors,
                            NULL lecturers,
                            NULL sounds,
                            NULL subs,
                            NULL writers,
                            NULL voices,
                            NULL stars,
                            NULL hosts,
                            NULL guests,
                            NULL interviewers,
                            NULL interviewees,
                            NULL presenters,
                            NULL reporters,
                            NULL performers,

                            NULL ttitle_req,
                            NULL llang_req,
                            NULL ttitle_orig,
                            NULL llang_orig

                        FROM
                            rec,
                            Card card,
                            Category category
                        WHERE
                            rec.id_higher_card=card.id
                            AND category.id=card.id_category
                    )
                SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers

                FROM
                    rec
                WHERE

                    -------------------
                    -------------------
                    --- Conditional ---
                    ---   filter    ---
                    -------------------
                    -------------------

                    --- if :level is set, then takes that specific level as highest level
                    --- if :level is NOT set, then takes the highest level
                    CASE
                        WHEN :level IS NULL THEN id_higher_card IS NULL ELSE level = :level
                    END

                GROUP BY id
                ) mixed_id_list,

                --------------------------
                --- unioned with title ---
                --------------------------
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

                ---------------
                --- HISTORY ---
                ---------------
                LEFT JOIN
                (
                    SELECT
                        ('start_epoch=' || start_epoch || ';recent_epoch=' || recent_epoch || ';recent_position=' || recent_position || ';play_count=' || count(*) ) recent_state,
                        id_card
                    FROM (
                        SELECT id_card, start_epoch, recent_epoch, recent_position
                        FROM History
                        WHERE id_user=:user_id
                        ORDER BY start_epoch DESC
                    )
                    GROUP BY id_card
                )hstr
                ON hstr.id_card=core.id

                --------------
                --- RATING ---
                --------------
                LEFT JOIN
                (
                    SELECT id_card, rate, skip_continuous_play
                    FROM Rating
                    WHERE id_user=:user_id
                )rtng
                ON rtng.id_card=core.id

                ---------------
                --- TAGGING ---
                ---------------
                LEFT JOIN
                (
                   SELECT
                      group_concat(name) tags,
                      id_card
                   FROM
                      Tag tag
                   WHERE
                      id_user=:user_id
                   GROUP BY id_card
                ) tggng
                ON tggng.id_card=core.id

            WHERE
                mixed_id_list.id=core.id
--                AND core.id=:card_id

            ORDER BY CASE
                WHEN sequence IS NULL AND title_req IS NOT NULL THEN title_req
                WHEN sequence IS NULL AND title_orig IS NOT NULL THEN title_orig
                WHEN sequence<0 THEN basename
                WHEN sequence>=0 THEN sequence
            END
            LIMIT :limit;

    ''',{'user_id': 1234, 'level': None, 'category': 'movie', 'title': 'Eszkim%', 'decade': None, 'lang': 'hu', 'limit': 100, 'card_id': 'b255267c44b7e425535a30bc7379e80f'})
for rec in res.fetchall():
    print(rec)



