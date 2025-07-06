import http.client
import json
import os
import re
import yaml
from pytlib.fetch_imdb import FetchImdb

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

class GenerateMediaFileSystem:

    def __init__(self,
        imdb_id,
        card_file_name,
        construction_path,
        destination_path,
        need_to_copy_to_destination_path=False,
        need_to_file=True,
        category='movie',
        primary_media_type='video',
        sounds=[], subs=[], themes=[],
        extra_iso_country_code_list=[]):

        self.imdb_id = imdb_id
        self.card_file_name = card_file_name
        self.construction_path = construction_path
        self.destination_path = destination_path
        self.need_to_copy_to_destination_path = need_to_copy_to_destination_path
        self.need_to_file = need_to_file
        self.category = category
        self.primary_media_type = primary_media_type
        self.sounds = sounds
        self.subs = subs
        self.themes = themes
        self.extra_iso_country_code_list = extra_iso_country_code_list

        self.imdb = FetchImdb(imdb_id)

        if self.imdb.getType() == "movie":
            self.generate_movie(imdb_id, self.imdb)
        elif self.imdb.getType() == "series":
            self.generate_series(imdb_id, self.imdb)
        else:
            print(f"Unknown type: {self.imdb.getType()}")
            exit()

    def _create_folder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _seconds_to_hh_mm_ss(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

    def _sanitize_title(self, title):
        # Remove special characters and replace spaces with dots
        sanitized = re.sub(r'[\'\":,]', '', title)
        sanitized = sanitized.replace(' ', '.')
        return sanitized

    def generate_movie(self, imdb_id, imdb):
        year = imdb.getYear()

        # Extract basic movie information
        title = imdb.getOriginalTitle()

        plot = imdb.getStoryline()
        length = imdb.getLength()
        runtime_sec = imdb.getRuntimeSec()
        genres = imdb.getGenres()

        netstart_sec = 90
        netstop_sec = runtime_sec - 90
        netstart = self._seconds_to_hh_mm_ss(netstart_sec)
        netstop = self._seconds_to_hh_mm_ss(netstop_sec)

        directors = imdb.getDirectors()
        writers = imdb.getWriters()
        actors = imdb.getActors()
        stars = imdb.getStars()

        origins = imdb.getOriginalCountries()
        id = imdb.getId()


        # Create movie data structure
        movie_data_structure = {
            "category": self.category,
            "primarymediatype": self.primary_media_type,
            "title": {
                "onthumbnail": True,
                "showsequence": "part",
                "orig": "en",
                "titles": {"en": title}
            },
            "storylines": {
                "en": plot,
                "hu": ""
            },
            "date": year,
            "length": length,
            "netstart": netstart,
            "netstop": netstop,
            "directors": directors,
            "writers": writers,
            "stars": stars,
            "actors": actors,
            "sounds": self.sounds,
            "subs": self.subs,
            "genres": genres,
            "themes": self.themes,
            "origins": origins,
            "id": id
        }

        # Create folder structure
        sanitized_title = f"{self._sanitize_title(title)}-{year}"
        construction_folder = os.path.join(self.construction_path, sanitized_title)

        header = f"= Individual movie: {sanitized_title} ="
        header_length = len(header)
        print(header_length * "=")
        print(header)
        print(header_length * "=")

        if not self.need_to_file:
            print(construction_folder)
        else:
            print(construction_folder)
            self._create_folder(construction_folder)
            self._create_folder(os.path.join(construction_folder, 'screenshots'))
            self._create_folder(os.path.join(construction_folder, 'thumbnails'))
            self._create_folder(os.path.join(construction_folder, 'media'))

            # Write movie data to card.yaml
            card_path = os.path.join(construction_folder, self.card_file_name)
            with open(card_path, 'w') as f:
                yaml.dump(movie_data_structure, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)

        if self.need_to_file and self.need_to_copy_to_destination_path:
            os.system(f"cp -r {construction_folder} {self.destination_path}")

        print(movie_data_structure)

    def generate_series(self, imdb_id, imdb):
        # Placeholder for series generation - not implemented yet
        print("Series generation not implemented yet")
        pass

if __name__ == "__main__":
    CARD_FILE_NAME = 'card.yaml'
    EXTRA_ISO_COUNTRY_CODE_LIST = ["hu-HU"]
    CATEGORY = "movie"
    PRIMARYMEDIATYPE = "video"
    SOUNDS = ["hu", "en"]
    SUBS = ["en"]
    THEMES = []

    IMDB_ID = "tt0137523"   # Fight Club
    IMDB_ID = "tt0078350"   # The Swarm
    IMDB_ID = "tt0308671"   # IMDB ID for individual movie - Tycoon A new russion
    IMDB_ID = "tt0098936"   # IMDB ID for series - Twin Peaks
#    IMDB_ID = "tt0108778"   # IMDB ID for series - Friends
#    IMDB_ID = "tt0106179"   # IMDB ID for series - X Files

    cons_path = os.path.expanduser('~/tmp/homeflix/')
    dest_path = os.path.expanduser('/media/akoel/vegyes/MEDIA/01.Movie/01.Standalone')

    need_to_copy_to_destination_path = False
    need_to_file = True

    gmfs = GenerateMediaFileSystem(
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
