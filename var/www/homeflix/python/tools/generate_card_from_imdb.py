import http.client
import json
import os
import re
import yaml
from pytlib.fetch_imdb import FetchImdb
from pytlib.generate_cards_from_imdb import GenerateCardsFromImdb

#class MyDumper(yaml.Dumper):
#    def increase_indent(self, flow=False, indentless=False):
#        return super(MyDumper, self).increase_indent(flow, False)
#
#class GenerateMediaFileSystem:
#
#    season_title_translate = {
#        'en': 'Season {0}',       # English
#        'hu': '{0}. évad',        # Hungarian
#        'de': '{0}. Staffel',     # German
#        'fr': 'Saison {0}',       # French
#        'es': 'Temporada {0}',    # Spanish
#        'it': 'Stagione {0}',     # Italian
#        'ru': 'Сезон {0}',        # Russian
#        'pl': 'Sezon {0}',        # Polish
#        'no': 'Sesong {0}',       # Norwegian
#        'dk': 'Sæson {0}',        # Danish
#        'ko': '{0}시즌',           # Korean
#        'hr': '{0}. sezona',      # Croatian
#        'zh': '第{0}季',           # Chinese
#        'nl': 'Seizoen {0}',      # Dutch
#        'fi': 'Kausi {0}',        # Finnish
#        'sv': 'Säsong {0}',       # Swedish
#        'cs': '{0}. série',       # Czech
#        'ja': 'シーズン{0}',       # Japanese
#        'ga': 'Séasúr {0}',       # Irish
#        'ro': 'Sezonul {0}'       # Romanian
#    }
#
#    def __init__(self,
#        imdb_id,
#        card_file_name='card.yaml',
#        construction_path=os.path.expanduser('~/tmp/homeflix/'),
#        destination_path=os.path.expanduser('~/tmp/homeflix/'),
#        need_to_copy_to_destination_path=False,
#        need_to_file=True,
#        category='movie',
#        primary_media_type='video',
#        sounds=[],
#        subs=[],
#        themes=[],
#        extra_iso_country_code_list=[]):
#
#        self.imdb_id = imdb_id
#        self.card_file_name = card_file_name
#        self.construction_path = construction_path
#        self.destination_path = destination_path
#        self.need_to_copy_to_destination_path = need_to_copy_to_destination_path
#        self.need_to_file = need_to_file
#        self.category = category
#        self.primary_media_type = primary_media_type
#        self.sounds = sounds
#        self.subs = subs
#        self.themes = themes
#        self.extra_iso_country_code_list = extra_iso_country_code_list
#
#        self.imdb = FetchImdb(imdb_id)
#
#        if self.imdb.getType() == "movie":
#            self._generate_movie(imdb_id, self.imdb)
#        elif self.imdb.getType() == "series":
#            self._generate_series(imdb_id, self.imdb)
#        else:
#            print(f"Unknown type: {self.imdb.getType()}")
#            exit()
#
#    def _format_number(self, num):
#        return f"{int(num):02d}"
#
#    def _create_folder(self, path):
#        if not os.path.exists(path):
#            os.makedirs(path)
#
#    def _seconds_to_hh_mm_ss(self, seconds):
#        hours = seconds // 3600
#        minutes = (seconds % 3600) // 60
#        remaining_seconds = seconds % 60
#        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
#
#    def _sanitize_title(self, title):
#        # Remove special characters and replace spaces with dots
#        sanitized = re.sub(r'[\'\":,]', '', title)
#        sanitized = sanitized.replace(' ', '.')
#        return sanitized
#
#    def _generate_movie(self, imdb_id, imdb):
#        year = imdb.getYear()
#
#        # Extract basic movie information
#        title = imdb.getOriginalTitle()
#
#        storyline = imdb.getStoryline()
#        length = imdb.getLength()
#        runtime_sec = imdb.getRuntimeSec()
#        genres = imdb.getGenres()
#
#        netstart_sec = 90
#        netstop_sec = runtime_sec - 90
#        netstart = self._seconds_to_hh_mm_ss(netstart_sec)
#        netstop = self._seconds_to_hh_mm_ss(netstop_sec)
#
#        directors = imdb.getDirectors()
#        writers = imdb.getWriters()
#        actors = imdb.getActors()
#        stars = imdb.getStars()
#
#        origins = imdb.getOriginalCountries()
#        id = imdb.getId()
#
#
#        # Create movie data structure
#        movie_data_structure = {
#            "category": self.category,
#            "primarymediatype": self.primary_media_type,
#            "title": {
#                "onthumbnail": True,
#                "showsequence": "part",
#                "orig": "en",
#                "titles": {"en": title}
#            },
#            "storylines": {
#                "en": storyline,
#                "hu": ""
#            },
#            "date": year,
#            "length": length,
#            "netstart": netstart,
#            "netstop": netstop,
#            "directors": directors,
#            "writers": writers,
#            "stars": stars,
#            "actors": actors,
#            "sounds": self.sounds,
#            "subs": self.subs,
#            "genres": genres,
#            "themes": self.themes,
#            "origins": origins,
#            "id": id
#        }
#
#        # Create folder structure
#        sanitized_title = f"{self._sanitize_title(title)}-{year}"
#        construction_folder = os.path.join(self.construction_path, sanitized_title)
#
#        header = f"= Individual movie: {sanitized_title} ="
#        header_length = len(header)
#        print(header_length * "=")
#        print(header)
#        print(header_length * "=")
#
#        if not self.need_to_file:
#            print(construction_folder)
#        else:
#            print(construction_folder)
#            self._create_folder(construction_folder)
#            self._create_folder(os.path.join(construction_folder, 'screenshots'))
#            self._create_folder(os.path.join(construction_folder, 'thumbnails'))
#            self._create_folder(os.path.join(construction_folder, 'media'))
#
#            # Write movie data to card.yaml
#            card_path = os.path.join(construction_folder, self.card_file_name)
#            with open(card_path, 'w') as f:
#                yaml.dump(movie_data_structure, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
#
#        if self.need_to_file and self.need_to_copy_to_destination_path:
#            os.system(f"cp -r {construction_folder} {self.destination_path}")
#
#        print(movie_data_structure)
#
#    def _generate_series(self, imdb_id, imdb):
#
#        series_storyline = imdb.getStoryline()
#        series_year = imdb.getYear()
#        series_title = imdb.getOriginalTitle()
#        series_origin = imdb.getOriginalCountries()
#        series_id = imdb.getId()
#        series_genres = imdb.getGenres()
#        series_level = 'series'
#        series_origin_lang = 'en'
#
#        # The series folder only once should be created
#        series_sanitized_title = f"{self._sanitize_title(series_title)}-{series_year}"
#        construction_series_folder = os.path.join(self.construction_path, series_sanitized_title)
#
#        self._create_folder(construction_series_folder)
#        self._create_folder(os.path.join(construction_series_folder, 'screenshots'))
#        self._create_folder(os.path.join(construction_series_folder, 'thumbnails'))
#
#        series_data = {
#            "category": self.category,
#            "mediatypes": [],
#            "level": series_level,
#            "title": {
#                "onthumbnail": True,
#                "showsequence": "part",
#                "orig": series_origin_lang,
#                "titles": {
#                    series_origin_lang: series_title
#                }
#            },
#            "storylines": {
#                "en": series_storyline,
#                "hu": ""
#            },
#            "date": series_year,
#            "genres": series_genres,
#            "origins": series_origin,
#            "id": series_id
#        }
#
#        # Write series data to card.yaml
#        card_path = os.path.join(construction_series_folder, self.card_file_name)
#        with open(card_path, 'w') as f:
#            yaml.dump(series_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
#
#        seasons_counts = imdb.getSeasonCounts()
#        for season_index in range(0, seasons_counts):
#
#            # Create season folder structure
#            formatted_season = f"S{self._format_number(season_index + 1)}"
#            season_folder = os.path.join(construction_series_folder, formatted_season)
#            self._create_folder(season_folder)
#            self._create_folder(os.path.join(season_folder, 'screenshots'))
#            self._create_folder(os.path.join(season_folder, 'thumbnails'))
#
#            season_title = self.season_title_translate.get(series_origin_lang, "Season {0}").format(season_index + 1)
#
#            season_data = {
#                "category": self.category,
#                "mediatypes": [],
#                "level": series_level,
#                "sequence": season_index + 1,
#                "title": {
#                    "onthumbnail": True,
#                    "showsequence": "part",
#                    "orig": series_origin_lang,
#                    "titles": {
#                        series_origin_lang: season_title
#                    }
#                }
#            }
#
#            card_path = os.path.join(season_folder, self.card_file_name)
#            with open(card_path, 'w') as f:
#                yaml.dump(season_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
#
#            episode_counts = imdb.getEpisodeCounts(season_index)
#            for episode_index in range(0, episode_counts):
#
#                # Create episode folder structure
#                episode_folder = os.path.join(season_folder, f"E{self._format_number(episode_index + 1)}")
#                self._create_folder(episode_folder)
#                self._create_folder(os.path.join(episode_folder, 'screenshots'))
#                self._create_folder(os.path.join(episode_folder, 'thumbnails'))
#                self._create_folder(os.path.join(episode_folder, 'media'))
#
#                episode_sequence = imdb.getSequence(season_index, episode_index)
#                episode_year = imdb.getYear(season_index, episode_index)
#                episode_title = imdb.getOriginalTitle(season_index, episode_index)
#
#                episode_storyline = imdb.getStoryline(season_index, episode_index)
#                episode_length = imdb.getLength(season_index, episode_index)
#                episode_runtime_sec = imdb.getRuntimeSec(season_index, episode_index)
#                episode_genres = imdb.getGenres(season_index, episode_index)
#
#                episode_netstart_sec = 90
#                episode_netstop_sec = episode_runtime_sec - 90
#                episode_netstart = self._seconds_to_hh_mm_ss(episode_netstart_sec)
#                episode_netstop = self._seconds_to_hh_mm_ss(episode_netstop_sec)
#
#                episode_directors = imdb.getDirectors(season_index, episode_index)
#                episode_writers = imdb.getWriters(season_index, episode_index)
#                episode_actors = imdb.getActors(season_index, episode_index)
#                episode_stars = imdb.getStars(season_index, episode_index)
#
#                episode_origins = imdb.getOriginalCountries(season_index, episode_index)
#                episode_id = imdb.getId(season_index, episode_index)
#
#                episode_data = {
#                    "category": self.category,
#                    "primarymediatype": self.primary_media_type,
#                    "sequence": episode_sequence,
#
#                    "title": {
#                        "onthumbnail": True,
#                        "showsequence": "part",
#                        "orig": "en",
#                        "titles": {"en": episode_title}
#                    },
#                    "storylines": {
#                        "en": episode_storyline,
#                        "hu": ""
#                    },
#                    "date": episode_year,
#                    "length": episode_length,
#                    "netstart": episode_netstart,
#                    "netstop": episode_netstop,
#                    "directors": episode_directors,
#                    "writers": episode_writers,
#                    "stars": episode_stars,
#                    "actors": episode_actors,
#                    "sounds": self.sounds,
#                    "subs": self.subs,
#                    "genres": episode_genres,
#                    "themes": self.themes,
#                    "origins": episode_origins,
#                    "id": episode_id
#                }
#
#                card_path = os.path.join(episode_folder, self.card_file_name)
#                with open(card_path, 'w') as f:
#                    yaml.dump(episode_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
#


if __name__ == "__main__":
    CARD_FILE_NAME = 'card.yaml'
    EXTRA_ISO_COUNTRY_CODE_LIST = ["hu-HU"]
    CATEGORY = "movie"
    PRIMARYMEDIATYPE = "video"
    SOUNDS = ["hu", "en"]
    SUBS = ["en"]
    THEMES = []

    IMDB_ID = "tt0137523"   # IMDB ID for individual movie - Fight Club
    IMDB_ID = "tt0078350"   # IMDB ID for individual movie - The Swarm
    IMDB_ID = "tt0308671"   # IMDB ID for individual movie - Tycoon A new russion
    IMDB_ID = "tt0074937"   # IMDB ID for individual movie - Murder by Death
    IMDB_ID = "tt0074937"   # IMDB ID for individual movie - Murder by Death
    IMDB_ID = "tt0069113"   # IMDB ID for individual movie - The Poseidon Adventure
    IMDB_ID = "tt0093870"   # IMDB ID for individual movie - Robocop
    IMDB_ID = "tt0121403"   # IMDB ID for individual movie - The Stationmaster Meets His Match


    IMDB_ID = "tt0098936"   # IMDB ID for series - Twin Peaks
    IMDB_ID = "tt0106179"   # IMDB ID for series - X Files
    IMDB_ID = "tt0407362"   # IMDB ID for series - Battlestar Galactica
    IMDB_ID = "tt0108778"   # IMDB ID for series - Friends
    IMDB_ID = "tt2861424"   # IMDB ID for series - Rick and Morty
    IMDB_ID = "tt0182576"   # IMDB ID for series - Family Guy
    IMDB_ID = "tt0096697"   # IMDB ID for series - Simpsons
    IMDB_ID = "tt1466074"   # IMDB ID for series - Columbo



    IMDB_ID = "tt0121403"   #

    cons_path = os.path.expanduser('~/tmp/homeflix/')
    dest_path = os.path.expanduser('/media/akoel/vegyes/MEDIA/01.Movie/01.Standalone')

    need_to_copy_to_destination_path = False
    need_to_file = True

    GenerateCardsFromImdb(
        imdb_id=IMDB_ID,
        card_file_name=CARD_FILE_NAME,
        construction_path=cons_path,
        destination_path=dest_path,
        need_to_copy_to_destination_path=need_to_copy_to_destination_path,
        need_to_file=need_to_file,
        category=CATEGORY,
        primary_media_type=PRIMARYMEDIATYPE,
        sounds=SOUNDS,
        subs=SUBS,
        themes=THEMES,
        extra_iso_country_code_list=EXTRA_ISO_COUNTRY_CODE_LIST
    )

