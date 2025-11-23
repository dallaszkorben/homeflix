#!/usr/bin/env python3

import os
import sys
import sqlite3
import logging
import locale

from threading import Lock


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from homeflix.translator.translator import Translator

# Add the parent directory to the path to import homeflix modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class SqlDatabase:
    """Minimal test class containing only the get_raw_query_of_abc_highest_level method and its dependencies"""

    MEDIA_CARD_LEVEL_CONDITION = "(card.level IS NULL OR card.level = 'record' OR card.level = 'episode')"

    def __init__(self):
        # Initialize logging
        logging.basicConfig(level=logging.DEBUG)

        self.lock = Lock()

        self.conn = None
        try:
            db_path = "/home/pi/.homeflix/homeflix.db"
            self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=20)
            logging.debug( "Connection to {0} SQLite was successful".format(db_path))
            self.conn.row_factory = sqlite3.Row
        except Error as e:
            logging.error( "Connection to {0} SQLite failed. Error: {1}".format(self.db_path, e))

            # TODO: handle this case
            exit()


    def get_sql_where_condition_from_text_filter(self, text_filter, field_name, start_separator=',', end_separator=','):
        """Helper method for building SQL WHERE conditions from text filters"""
        op = None
        if text_filter is None:
            filter_list = []
        elif '_AND_' in text_filter:
            op = 'and'
            filter_list = [] if text_filter is None else text_filter.split('_AND_')
        elif '_OR_' in text_filter:
            op = 'or'
            filter_list = [] if text_filter is None else text_filter.split('_OR_')
        else:
            op = ''
            filter_list = [text_filter]
        filter_in_list =     [] if text_filter == None else [filter for filter in filter_list if not filter.startswith("_NOT_")]
        filter_not_in_list = [] if text_filter == None else [filter.removeprefix("_NOT_") for filter in filter_list if filter.startswith("_NOT_")]

        filter_where =  None if text_filter == None else '(' + (' OR ' if op == 'or' else ' AND ').join([f"'{start_separator}' || " + field_name + " || ',' " + ("NOT " if filter.startswith("_NOT_") else "") + f"LIKE '%{start_separator}" + filter.removeprefix("_NOT_") + f"{end_separator}%'" for filter in filter_list]) + ')'

        return filter_where


    def get_sql_like_where_condition_from_text_filter(self, text_filter, field_name):
        """Helper method for building SQL LIKE WHERE conditions from text filters"""
        op = None
        if text_filter is None:
            filter_list = []
        elif '_AND_' in text_filter:
            op = 'and'
            filter_list = [] if text_filter is None else text_filter.split('_AND_')
        elif '_OR_' in text_filter:
            op = 'or'
            filter_list = [] if text_filter is None else text_filter.split('_OR_')
        else:
            op = ''
            filter_list = [text_filter]

        filter_in_list =     [] if text_filter == None else [filter for filter in filter_list if not filter.startswith("_NOT_")]
        filter_not_in_list = [] if text_filter == None else [filter.removeprefix("_NOT_") for filter in filter_list if filter.startswith("_NOT_")]
        filter_where =       None if text_filter == None else '(' + (' OR ' if op == 'or' else ' AND ').join(["" + field_name + " " + ("NOT " if filter.startswith("_NOT_") else "") + "LIKE '" + filter.removeprefix("_NOT_") + "'" for filter in filter_list]) + ')'

        # logging.debug("{} IN LIST: {}".format(field_name, filter_in_list))
        # logging.debug("{} NOT IN LIST: {}".format(field_name, filter_not_in_list))
        # logging.debug("{} WHERE: {}".format(field_name, filter_where if filter_where is not None else 'None'))

        return filter_where


    def get_converted_query_to_json(self, sql_record_list, category, lang):
        """
        Convert and translate the given SQL card-response
        """
        records = [{key: record[key] for key in record.keys()} for record in sql_record_list]

        trans = Translator.getInstance(lang)
        for record in records:

            # Lang Orig
            lang_orig = record["lang_orig"]
            lang_orig_translated = trans.translate_language_short(lang_orig)
            record["lang_orig"] = lang_orig_translated
            # Lang Req
            lang_req = record["lang_req"]
            lang_req_translated = trans.translate_language_short(lang_req)
            record["lang_req"] = lang_req_translated
            # Media
            medium_string = record["medium"]
            media_dict = {}
            if medium_string:
                medium_string_list = medium_string.split(',')
                for medium_string in medium_string_list:
                    (media_type, media) = medium_string.split("=")
                    if not media_type in media_dict:
                        media_dict[media_type] = []
                    media_dict[media_type].append(media)
            record["medium"] = media_dict
            # Appendix
            appendix_string = record["appendix"]
            appendix_list = []
            if appendix_string:
                text_list = appendix_string.split(',')
                for appendix_string in text_list:
                    var_list = appendix_string.split(";")
                    appendix_dict = {}
                    for var_pair in var_list:
                        (key, value) = var_pair.split("=")
                        appendix_dict[key] = value
                    appendix_list.append(appendix_dict)
            record["appendix"] = appendix_list
            # Recent State (history)
            recent_state_string = record["recent_state"]
            recent_state_dict = {'recent_position':0, 'play_count':0}
            if recent_state_string and record["medium"]:
                var_list = recent_state_string.split(";")
                for var_pair in var_list:
                    (key, value) = var_pair.split("=")
                    recent_state_dict[key] = value
            record["recent_state"] = recent_state_dict
            # Rate
            record["rate"] = record["rate"] if record["rate"] else 0
            record["skip_continuous_play"] = True if record["skip_continuous_play"] else False
            # Writers
            writers_string = record["writers"]
            writers_list = []
            if writers_string:
                writers_list = writers_string.split(',')
            record["writers"] = writers_list
            # Directors
            directors_string = record["directors"]
            directors_list = []
            if directors_string:
                directors_list = directors_string.split(',')
            record["directors"] = directors_list
            # Stars
            stars_string = record["stars"]
            stars_list = []
            if stars_string:
                stars_list = stars_string.split(',')
            record["stars"] = stars_list

            # Actors
            actors_play_string = record["actors"]
            actors_list = []
            if actors_play_string:
                actors_play_list = actors_play_string.split(';')
                for actor_string in actors_play_list:
                    (actor, characters_string) = actor_string.split(':')
                    characters = []
                    if characters_string:
                        character_list = characters_string.split(',')
                        for character in character_list:
                            characters.append(character)
                    actors_list.append({actor: characters})
            record["actors"] = actors_list

            # Voices
            voices_play_string = record["voices"]
            voices_list = []
            if voices_play_string:
                voices_play_list = voices_play_string.split(';')
                for voice_string in voices_play_list:
                    (voice, characters_string) = voice_string.split(':')
                    characters = []
                    if characters_string:
                        character_list = characters_string.split(',')
                        for character in character_list:
                            characters.append(character)
                    voices_list.append({voice: characters})
            record["voices"] = voices_list

            # Host
            hosts_string = record.get("hosts")
            hosts_list = []
            if hosts_string:
                hosts_list = hosts_string.split(',')
            record["hosts"] = hosts_list
            # Guests
            guests_string = record.get("guests")
            guests_list = []
            if guests_string:
                guests_list = guests_string.split(',')
            record["guests"] = guests_list
            # Interviewers
            interviewers_string = record.get("interviewers")
            interviewers_list = []
            if interviewers_string:
                interviewers_list = interviewers_string.split(',')
            record["interviewers"] = interviewers_list
            # Interviewees
            interviewees_string = record.get("interviewees")
            interviewees_list = []
            if interviewees_string:
                interviewees_list = interviewees_string.split(',')
            record["interviewees"] = interviewees_list
            # Presenters
            presenters_string = record.get("presenters")
            presenters_list = []
            if presenters_string:
                presenters_list = presenters_string.split(',')
            record["presenters"] = presenters_list
            # Lecturers
            lecturers_string = record.get("lecturers")
            lecturers_list = []
            if lecturers_string:
                lecturers_list = lecturers_string.split(',')
            record["lecturers"] = lecturers_list
            # Performers
            performers_string = record.get("performers")
            performers_list = []
            if performers_string:
                performers_list = performers_string.split(',')
            record["performers"] = performers_list
            # Reporters
            reporters_string = record.get("reporters")
            reporters_list = []
            if reporters_string:
                reporters_list = reporters_string.split(',')
            record["reporters"] = reporters_list
            # Genre
            genres_string = record.get("genres")
            genres_list = []
            if genres_string:
                genres_list = genres_string.split(',')
                genres_list = [trans.translate_genre(category=category, genre=genre) for genre in genres_list]
            record["genres"] = genres_list
            # Theme
            themes_string = record["themes"]
            themes_list = []
            if themes_string:
                themes_list = themes_string.split(',')
                themes_list = [trans.translate_theme(theme=theme) for theme in themes_list]
            record["themes"] = themes_list
            # Origin
            origins_string = record["origins"]
            origins_list = []
            if origins_string:
                origins_list = origins_string.split(',')
                origins_list = [trans.translate_country_long(origin) for origin in origins_list]
            record["origins"] = origins_list
            # Sub
            subs_string = record["subs"]
            subs_list = []
            if subs_string:
                subs_list = subs_string.split(',')
                subs_list = [trans.translate_language_long(sub) for sub in subs_list]
            record["subs"] = subs_list
            # Sounds
            sounds_string = record["sounds"]
            sounds_list = []
            if sounds_string:
                sounds_list = sounds_string.split(',')
                sounds_list = [trans.translate_language_long(sounds) for sounds in sounds_list]
            record["sounds"] = sounds_list
            # Tags
            tags_string = record["tags"]
            tags_list = []
            if tags_string:
                tags_list = tags_string.split(',')
            record["tags"] = tags_list
        logging.debug("Converted records: '{0}'".format(records))

        return records


    def get_sql_rate_query(self, value):
        """Helper method for building rate query conditions"""
        return f"rate>={str(value)}" if value else ""


    def get_abc_highest_level_cards(self, category, user_id=0, view_state=None, tags=None, level=None, filter_on=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None, decade=None, lang='en', limit=1000, json=True):

        records = {}

        with self.lock:

            #print("level: {}, filter_on: {}".format(level, filter_on))
            try:
                cur = self.conn.cursor()
                cur.execute("begin")

                query = self.get_raw_query_of_abc_highest_level(category=category, tags=tags, title=title, genres=genres, themes=themes, directors=directors, writers=writers, actors=actors, voices=voices, lecturers=lecturers, performers=performers, origins=origins, rate_value=rate_value)

                query_parameters = {'user_id': user_id, 'level': level, 'filter_on': filter_on, 'category': category, 'title': title, 'decade': decade, 'tags': tags, 'lang': lang, 'limit': limit}

                records=cur.execute(query, query_parameters).fetchall()
                cur.execute("commit")



                # Set locale for proper language-specific sorting
                locale_map = {'hu': 'hu_HU.UTF-8', 'en': 'en_US.UTF-8', 'sv': 'sv_SE.UTF-8'}
                try:
                    locale.setlocale(locale.LC_ALL, locale_map.get(lang, 'en_US.UTF-8'))
                except locale.Error:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')  # fallback

                locale.setlocale(locale.LC_ALL, 'C.UTF-8')  # fallback

                records = [{key: record[key] for key in record.keys()} for record in records]
                records = sorted(records, key=lambda arg: locale.strxfrm(arg['name']))

            #    for record in my_records:
            #        print(f'- {record}')
            #    print("\n\n\n")

            #    if json:
            #        records = self.get_converted_query_to_json(records, category, lang)

            except sqlite3.Error as e:
                error_message = "Fetching the highest level card failed: {0}".format(e)
                logging.error(f'Error in the request process: {error_message}')

            finally:
                cur.close()

                return records
        return records


    def get_raw_query_of_abc_highest_level(self, category, tags=None, title=None, genres=None, themes=None, directors=None, writers=None, actors=None, voices=None, lecturers=None, performers=None, origins=None, rate_value=None):
        tags_where = self.get_sql_where_condition_from_text_filter(tags, 'tags')
        genres_where = self.get_sql_where_condition_from_text_filter(genres, 'genres')
        themes_where = self.get_sql_where_condition_from_text_filter(themes, 'themes')
        actors_where = self.get_sql_where_condition_from_text_filter(actors, 'actors', start_separator=';', end_separator=':')
        voices_where = self.get_sql_where_condition_from_text_filter(voices, 'voices', start_separator=';', end_separator=':')
        writers_where = self.get_sql_where_condition_from_text_filter(writers, 'writers')
        directors_where = self.get_sql_where_condition_from_text_filter(directors, 'directors')
        lecturers_where = self.get_sql_where_condition_from_text_filter(lecturers, 'lecturers')
        performers_where = self.get_sql_where_condition_from_text_filter(performers, 'performers')
        origins_where = self.get_sql_where_condition_from_text_filter(origins, 'origins')
        titles_req_where = self.get_sql_like_where_condition_from_text_filter(title, 'ttitle_req')
        titles_orig_where = self.get_sql_like_where_condition_from_text_filter(title, 'ttitle_orig')
        rate_where = self.get_sql_rate_query(rate_value)

        query = '''

            SELECT

                CASE
                    WHEN UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    )) IN ('0','1','2','3','4','5','6','7','8','9') THEN '0-9'
                    ELSE UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    ))
                END AS name,
                CASE
                    WHEN UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    )) IN ('0','1','2','3','4','5','6','7','8','9') THEN '0%_OR_1%_OR_2%_OR_3%_OR_4%_OR_5%_OR_6%_OR_7%_OR_8%_OR_9%'
                    ELSE UPPER(SUBSTR(
                        CASE
                            WHEN core.title_req IS NOT NULL THEN core.title_req
                            ELSE core.title_orig
                        END, 1, 1
                    )) || '%'
                END AS filter
            FROM

                ---------------------------
                --- mixed level id list ---
                ---------------------------
                (
                WITH RECURSIVE
                    rec(id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play,sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers, ttitle_req, llang_req, ttitle_orig, llang_orig) AS

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

                            tags,
                            rate,
                            skip_continuous_play,

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
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as actors,
                                    card_actor.id_card id_card
                                FROM
                                    Person person,
                                    Card_Actor card_actor,
                                    (
                                        SELECT
                                            actor_role.id_actor,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            actor_role
                                        WHERE
                                            actor_role.id_role = role.id
                                        GROUP BY
                                            actor_role.id_actor, role.id_card
                                    ) roles
                                WHERE
                                    card_actor.id_actor = person.id
                                    AND roles.id_actor = person.id
                                    AND roles.id_card = card_actor.id_card
                                GROUP BY
                                    card_actor.id_card
                            ) act
                            ON act.id_card=card.id

                            --------------
                            --- VOICES ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT
                                    GROUP_CONCAT(
                                        person.name || ': ' || COALESCE(role_names, ''), ';'
                                    ) as voices,
                                    card_voice.id_card id_card
                                FROM
                                    Person person,
                                    Card_Voice card_voice,
                                    (
                                        SELECT
                                            voice_role.id_voice,
                                            role.id_card,
                                            GROUP_CONCAT(role.name, ',') as role_names
                                        FROM
                                            role,
                                            voice_role
                                        WHERE
                                            voice_role.id_role = role.id
                                        GROUP BY
                                            voice_role.id_voice, role.id_card
                                    ) roles
                                WHERE
                                    card_voice.id_voice = person.id
                                    AND roles.id_voice = person.id
                                    AND roles.id_card = card_voice.id_card
                                GROUP BY
                                    card_voice.id_card
                            ) vc
                            ON vc.id_card=card.id

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

                            --------------
                            --- RATING ---
                            --------------
                            LEFT JOIN
                            (
                                SELECT id_card, rate, skip_continuous_play
                                FROM Rating
                                WHERE id_user=:user_id
                            )rtng
                            ON rtng.id_card=card.id

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
                            ON ttlrq.id_card=card.id

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
                            -- AND card.level IS NULL

                            -- Select the given category --
                            AND category.name = :category

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

                            ''' + (
                                '''
                                AND CASE
                                    WHEN ttitle_req IS NOT NULL THEN ''' + titles_req_where + '''
                                    ELSE ''' + titles_orig_where + '''
                                END
                                ''' if titles_orig_where else ''' '''
                            ) + '''

                            ''' + ('''
                            --- WHERE THEMES - conditional ---
                            AND ''' + themes_where if themes_where else '') + '''

                            ''' + ('''
                            --- WHERE GENRES - conditional ---
                            AND ''' + genres_where if genres_where else '') + '''

                            ''' + ('''
                            --- WHERE DIRECTORS - conditional ---
                            AND ''' + directors_where if directors_where else '') + '''

                            ''' + ('''
                            --- WHERE WRITERS - conditional ---
                            AND ''' + writers_where if writers_where else '') + '''

                            ''' + ('''
                            --- WHERE ACTORS - conditional ---
                            AND ''' + actors_where if actors_where else '') + '''

                            ''' + ('''
                            --- WHERE VOICES - conditional ---
                            AND ''' + voices_where if voices_where else '') + '''

                            ''' + ('''
                            --- WHERE ORIGINS - conditional ---
                            AND ''' + origins_where if origins_where else '') + '''

                            ''' + ('''
                            --- WHERE PERFORMERS - conditional ---
                            AND ''' + performers_where if performers_where else '') + '''

                            ''' + ('''
                            --- WHERE LECTURERS - conditional ---
                            AND ''' + lecturers_where if lecturers_where else '') + '''

                            ''' + ('''
                            --- WHERE TAGS - conditional ---
                            AND ''' + tags_where if tags_where else '') + '''

                            ''' + ('''
                            --- WHERE RATE - conditional ---
                            AND ''' + rate_where if rate_where else '') + '''

                            AND CASE

                                -- level: ^ (*, None), filter: v (*, None) => show the HIGHEST level and filter on the LOWEST level on any type => filter LOWEST level
                                -- Genre: Standalone Scifi
                                WHEN (:level IS NULL OR :level = '^') AND (:filter_on IS NULL OR :filter_on = 'v') THEN ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + '''

                                -- level: ^ (*, None), filter: ^ (-) => show the HIGHEST level and filter on the same (HIGHEST) level on any type => filter HIGHEST level
                                -- Title: Standalone or Series
                                WHEN (:level IS NULL OR :level = '^') AND :filter_on IS not NULL AND :filter_on = '-' THEN card.id_higher_card IS NULL

                                -- level: <level>, filter: v (* None) => show the GIVEN level and filter on the LOWEST level on any type => filter LOWEST level
                                WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND (:filter_on IS NULL OR :filter_on = 'v') THEN ''' + SqlDatabase.MEDIA_CARD_LEVEL_CONDITION + ''' AND card.id_higher_card IS not NULL

                                -- level: <level>, filter: - => show the GIVEN level and filter on the same (GIVEN) level on any type => filter GIVEN level
                                WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND :filter_on IS not NULL AND :filter_on = '-' THEN card.level = :level

                                ELSE 0

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

                            NULL tags,
                            NULL rate,
                            NULL skip_continuous_play,

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
                SELECT id, id_higher_card, category, level, source_path, basename, sequence, title_on_thumbnail, title_show_sequence, decade, date, length, full_time, net_start_time, net_stop_time, themes, genres, origins, directors, actors, lecturers, tags, rate, skip_continuous_play, sounds, subs, writers, voices, stars, hosts, guests, interviewers, interviewees, presenters, reporters, performers

                FROM
                    rec
                WHERE

                    -------------------
                    -------------------
                    --- Conditional ---
                    ---   filter    ---
                    -------------------
                    -------------------

                    CASE
                        -- level: ^ (*, None), filter: v (*, None) => show the HIGHEST level and filter on the LOWEST level on any type => show HIGHEST level
                        WHEN (:level IS NULL OR :level = '^') AND (:filter_on IS NULL OR :filter_on = 'v') THEN id_higher_card IS NULL

                        -- level: ^ (*, None), filter: - => show the HIGHEST level and filter on the same (HIGHEST) level on any type => show HIGHEST level
                        WHEN (:level IS NULL OR :level = '^') AND :filter_on IS not NULL AND :filter_on = '-' THEN id_higher_card IS NULL

                        -- level: <level>, filter: v (* None) => show the GIVEN level and filter on the LOWEST level on any type => GIVEN level
                        WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND (:filter_on IS NULL OR :filter_on = 'v') THEN level = :level

                        -- level: <level>, filter: - => show the GIVEN level and filter on the same (GIVEN) level on any type => GIVEN level
                        WHEN :level IS not NULL AND :level != '^' and :level != 'v' AND :filter_on IS not NULL AND :filter_on = '-' THEN level = :level

                        ELSE 0
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
                    MAX(title_orig) title_orig


                FROM
                    (
                    SELECT
                        card.id id,

                        NULL title_req,
                        tcl.text title_orig
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
                        NULL title_orig
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

                mixed_id_list.id=core.id

            GROUP BY name
            ORDER BY name
            LIMIT :limit; '''

        return query






if __name__ == "__main__":
    # Instantiate the test class and call the method
    test_db = SqlDatabase()
    # query = test_db.get_raw_query_of_abc_highest_level(category="movie")
    query = test_db.get_abc_highest_level_cards(category="music_audio", level="soundtrack", lang="hu")
    print("Generated SQL Query:")
    print(query)