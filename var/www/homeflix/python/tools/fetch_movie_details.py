import requests
import os
import re
import yaml

# $ pip install cinemagoer
from imdb import Cinemagoer

# TODO: The dicts and methods out of Class should go somewhere to the main code

country_language = {
    'eu': ['en'],        # European Union (default to English)
    'hu': ['hu'],
    'us': ['en'],
    'gb': ['en'],
    'de': ['de'],
    'fr': ['fr'],
    'es': ['es'],
    'it': ['it'],
    'ru': ['ru'],
    'pl': ['pl'],
    'no': ['no'],
    'dk': ['dk'],
    'kr': ['ko'],
    'hr': ['hr'],
    'cn': ['zh'],
    'nl': ['nl'],
    'fi': ['fi'],
    'ca': ['en', 'fr'],
    'ch': ['de', 'fr', 'it'],
    'be': ['nl', 'fr', 'de'],
    'mx': ['es'],
    'se': ['sv'],
    'at': ['de'],
    'au': ['en'],
    'nz': ['en'],
    'cz': ['cs'],
    'ar': ['es'],
    'jp': ['ja'],
    'ie': ['en', 'ga'],
    'ro': ['ro']
}

season_title_translate = {
    'en': 'Season {0}',       # English
    'hu': '{0}. évad',        # Hungarian
    'de': '{0}. Staffel',     # German
    'fr': 'Saison {0}',       # French
    'es': 'Temporada {0}',    # Spanish
    'it': 'Stagione {0}',     # Italian
    'ru': 'Сезон {0}',        # Russian
    'pl': 'Sezon {0}',        # Polish
    'no': 'Sesong {0}',       # Norwegian
    'dk': 'Sæson {0}',        # Danish
    'ko': '{0}시즌',           # Korean
    'hr': '{0}. sezona',      # Croatian
    'zh': '第{0}季',           # Chinese
    'nl': 'Seizoen {0}',      # Dutch
    'fi': 'Kausi {0}',        # Finnish
    'sv': 'Säsong {0}',       # Swedish
    'cs': '{0}. série',       # Czech
    'ja': 'シーズン{0}',       # Japanese
    'ga': 'Séasúr {0}',       # Irish
    'ro': 'Sezonul {0}'       # Romanian
}

#def get_country_code_by_country_name(country_name, dictionary):
#    """Get 2-letter country code from country name using dictionary mapping"""
#
#    # Create reverse mapping from country names to codes
#    country_map = {v.lower(): k for k, v in dictionary['country']['long'].items()}
#    return country_map.get(country_name.lower())

def get_language_code_by_language_name(language_name, dictionary):
    """Get 2-letter language code from language name using dictionary mapping"""

    # Create reverse mapping from language names to codes
    language_map = {v.lower(): k for k, v in dictionary['language']['long'].items()}

    # Return the language code if found, None otherwise
    return language_map.get(language_name.lower())

#def get_language_code_list_by_countrie_code_list(country_code_list):
#    """Convert country codes to their primary language codes"""
#    language_code_list = []
#    for country in country_code_list:
#        # Get the first language for each country if it exists in country_language
#        if country in country_language:
#            lang = country_language[country][0]  # Take first language
#            language_code_list.append(lang)
#
#    # Remove duplicates by converting to set and back to list
#    return list(set(language_code_list))

def get_country_code_by_language_code(language_code, origins):
    """
    Convert language code to country code if the country exists in origins list

    Args:
        language_code: str - the language code to look for (e.g., 'en', 'hu')
        origins: list - list of country codes to check against
        country_language: dict - mapping of country codes to their language codes

    Returns:
        str: country code if found
        None: if no matching country found

    Example usage:
    origins = ['us', 'hu', 'ca']
    result = get_country_code_by_language_code('en', origins, country_language)
    print(result)  # Output: 'us' (or 'ca', depending on which comes first in origins)
    result = get_country_code_by_language_code('fr', origins, country_language)
    print(result)  # Output: 'ca'
    result = get_country_code_by_language_code('de', origins, country_language)
    print(result)  # Output: None
    """
    for country in origins:
        if country in country_language:
            # Check if the language_code is in the list of languages for this country
            if language_code in country_language[country]:
                return country
    return None


def get_iso_country_code_list_by_country_code_list(country_code_list):

    iso_country_code_list = []
    for country_code in country_code_list:

        # Get the first language for each country if it exists in country_language
        if country_code in country_language:
            lang = country_language[country_code][0]  # Take first language
            iso_country_code_list.append(lang + "-" + country_code.upper())

    # Remove duplicates by converting to set and back to list
    return list(set(iso_country_code_list))


#def parse_aka_list(aka_list, dictionary):
#    aka_parsed = []
#
#    for item in aka_list:
#        # Extract title and country using regex
#        import re
#        match = re.match(r'(.*?)\s*\((.*?)\)', item)
#        if match:
#            title = match.group(1).strip()
#            country_name = match.group(2).strip()
#
#            # Handle special cases
#            if 'World-wide' in country_name:
#                country_code = 'us'  # Default to US for worldwide
#            else:
#                # Remove any additional info in parentheses
#                country_name = country_name.split(',')[0]
#                country_code = get_country_code_by_country_name(country_name, dictionary)
#
#            if country_code:
#                # Get the first language for this country
#                lang = country_language.get(country_code, ['en'])[0]
#
#                aka_parsed.append({
#                    'title': title,
#                    'country': country_code,
#                    'lang': lang
#                })
#
#    return aka_parsed


class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

class GenerateMediaFileSystem:

    def __init__(self,
        api_key, imdb_id,
        construction_path,
        destination_path,
        need_to_copy_to_destination_path=False,
        need_to_file=True,
        category='movie',
        primary_media_type='video',
        sounds=[], subs=[], themes=[],
        extra_iso_country_code_list=[]
    ):
        self.api_key = api_key
        self.imdb_id = imdb_id
        self.construction_path = construction_path
        self.destination_path = destination_path
        self.need_to_copy_to_destination_path = need_to_copy_to_destination_path
        self.need_to_file = need_to_file
        self.category = category
        self.primary_media_type = primary_media_type
        self.sounds=sounds
        self.subs=subs
        self.themes=themes
        self.extra_iso_country_code_list = extra_iso_country_code_list

        # Get the current file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the dictionary.yaml file
        dictionary_path = os.path.join(current_dir, '..', 'homeflix', 'translator', 'dictionary.yaml')

        # Load the YAML file
        with open(dictionary_path, 'r') as file:
            self.dictionary = yaml.safe_load(file)

        self.ia = Cinemagoer()

        search_results = self.ia.get_movie(imdb_id[2:])
        kind = search_results.get("kind")   #movie/tv series/

        if kind == 'movie':
            self.generate_movie(imdb_id, search_results)
        elif kind == 'tv series':
            self.generate_series(imdb_id, search_results)
        else:
            print(f"Unknown kind: {kind}")
            exit()

    def seconds_to_hh_mm_ss(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

    def sanitize_title(self, title):
        # Remove special characters and replace spaces with dots
        sanitized = re.sub(r'[\'\":,]', '', title)
        sanitized = sanitized.replace(' ', '.')
        return sanitized

    def format_number(self, num):
        return f"{int(num):02d}"

    def create_folder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def translate_genre(self, genre):
        genre_dict = {
            "scifi": "sci-fi",
            "film-noir": "film_noir"
        }

        # Convert input to lowercase to make the search case-insensitive
        genre_lower = genre.lower()

        # Return the translated genre if found, otherwise return the original genre
        return genre_dict.get(genre_lower, genre_lower)

    #
    # Generate Movie
    #
    def generate_movie(self, imdb_id, search_results):

        year = search_results.get("year")

        extra_data = {
            "series": False,
            "id": imdb_id
        }
        movie_data, _ = self.generate_base_data(search_results, extra_data)

        # The folder should be created
        en_title = movie_data['title']['titles']['en']
        sanitized_title = f"{self.sanitize_title(en_title)}-{year}"
        construction_folder = os.path.join(self.construction_path, sanitized_title)

        header = f"= Individual movie: {sanitized_title} ="
        header_length = len(header)
        print( header_length * "=" )
        print( header )
        print( header_length * "=" )

        if not self.need_to_file:
            print(construction_folder)
        else:
            print(construction_folder)
            self.create_folder(construction_folder)
            self.create_folder(os.path.join(construction_folder, 'screenshots'))
            self.create_folder(os.path.join(construction_folder, 'thumbnails'))
            self.create_folder(os.path.join(construction_folder, 'media'))

            # Write series data to card.yaml
            card_path = os.path.join(construction_folder, 'card.yaml')
            with open(card_path, 'w') as f:
                yaml.dump(movie_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)

        if self.need_to_file and self.need_to_copy_to_destination_path:
            os.system(f"cp -r {construction_folder} {self.destination_path}")

        print(movie_data)


    #
    # Generate Series
    #
    def generate_series(self, imdb_id, search_results):

        total_seasons = search_results.get("number of seasons")
        series_story = search_results.get("plot")[0]
        series_year = re.split(r'[-–]', search_results.get("series years"))[0]

        series_title = search_results.get("title")

        # The series folder only once should be created
        series_sanitized_title = f"{self.sanitize_title(series_title)}-{series_year}"
        construction_series_folder = os.path.join(self.construction_path, series_sanitized_title)

        # ---------------------
        # --- Fetch seasons ---
        # ---------------------

        # ! Unfortunatelly the Cinemagoer does not return the episodes, so I have to use the OMDb API instead to fetch the seasons and the belonging episod IDs !

        # Go through all the seasons
        for recent_season in range(1, total_seasons + 1):

            series_data = {
                "series_imdb_id": imdb_id,
                "series_story": series_story,
                "series_sanitized_title": series_sanitized_title,
                "series_title": {},
                "series_year": series_year,
                "recent_season": recent_season,
                "construction_series_folder": construction_series_folder
            }

            # for getting the episode list
            url = f"http://www.omdbapi.com/?i={imdb_id}&Season={recent_season}&apikey={self.api_key}"
            response = requests.get(url)
            data = response.json()

            episode_list = []
            for idx, episode in enumerate(data["Episodes"], start=1):

                episode_id = episode["imdbID"]

                # we have the episode id now, so we can call the Cinemagoer

                # ----------------------
                # --- Fetch episodes ---
                # ----------------------

                episode = self.ia.get_movie(episode_id[2:])  # Remove 'tt' from IMDb ID

                sequence = episode.get("episode", 0)
                en_title = episode.get("episode title", "__")

                extra_data = {
                    "series": True,
                    "sequence": sequence,
                    "id": episode_id
                }
                episode_data, iso_country_code_list = self.generate_base_data(episode, extra_data)

                #
                # --- Fetch the title of the series ---
                #
                origin_lang = episode_data["title"]["orig"]

                titles = {}
                for iso_country_code in iso_country_code_list:
                    ia = Cinemagoer('http', useModule='http', languages=iso_country_code)
                    local_result = ia.get_movie(imdb_id[2:])
                    loc_title = local_result.get('localized title')
                    lang = iso_country_code.split('-')[0]
                    titles[lang] = loc_title
                series_data["series_title"]["titles"] = titles
                series_data["series_title"]["orig"] = origin_lang

                # ---

                self.handle_episode(episode_data, series_data)
                print(episode_data)

        if need_to_file and need_to_copy_to_destination_path:
            # -r: recursive (copy directories and their content)
            # -n: no-clobber (do not overwrite existion files)
            os.system(f"cp -rn {construction_series_folder} {destination_path}")

    def generate_base_data(self, search_results, extra_data):

        sequence = extra_data.get("sequence", None)
#        en_title = extra_data.get("en_title", None)
        id = extra_data.get("id", None)
        series = extra_data.get("series", False)

        en_storyline = search_results.get("plot")[0]
        year = search_results.get("year")

        origins = list({origin for origin in search_results.get("country codes", [])})
        genres = list({self.translate_genre(genre) for genre in search_results.get("genres", [])})
        directors = list({director["name"] for director in search_results.data["director"] if "name" in director})
        writers = list({writer["name"] for writer in search_results.data["writer"] if "name" in writer})
        actors = {actor["name"]: str(actor.currentRole) if actor.currentRole else "" for actor in search_results["cast"]} if "cast" in search_results else {}
        stars = [actor["name"] for actor in search_results["cast"][:3]]

        runtimes_sec = int(search_results["runtimes"][0]) * 60
        netstart_sec = 90
        netstop_sec = runtimes_sec - 90

        length = self.seconds_to_hh_mm_ss(runtimes_sec)
        netstart = self.seconds_to_hh_mm_ss(netstart_sec)
        netstop = self.seconds_to_hh_mm_ss(netstop_sec)

        # Localization
        origin_language_name = search_results.guessLanguage()
        origin_language_code = get_language_code_by_language_name(origin_language_name, self.dictionary   )
        origin_language_code = 'en' if origin_language_code == 'en' else origin_language_code
        origin_country_code = get_country_code_by_language_code(origin_language_code, origins)
        origin_lang = origin_language_code
        origin_iso_country_code = origin_language_code + "-" + origin_country_code.upper()
        origin_iso_country_code_list = get_iso_country_code_list_by_country_code_list(origins)
        iso_country_code_list = list(set(origin_iso_country_code_list + self.extra_iso_country_code_list + [origin_iso_country_code]))

        titles = {}
        for iso_country_code in iso_country_code_list:
            ia = Cinemagoer('http', useModule='http', languages=iso_country_code)
            local_result = ia.get_movie(extra_data["id"][2:])
            loc_title = local_result.get('localized title')
            lang = iso_country_code.split('-')[0]
            titles[lang] = loc_title

        data = {
            "category": self.category,
            "primarymediatype": self.primary_media_type,
            "sequence": sequence,
            "title": {
                "onthumbnail": True,
                "showsequence": "part",
                "orig": origin_lang,
                "titles": titles
            },
            "storylines": {
                "en": en_storyline,
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
            "id": {
                "name": "imdb",
                "value": id
            }
        }

        if not series:
            del data["sequence"]

        return data, iso_country_code_list


    def handle_episode(self, episode_data, series_data):

        series_imdb_id = str(series_data['series_imdb_id'])
        series_story = str(series_data['series_story'])
        series_sanitized_title = str(series_data['series_sanitized_title'])
        series_year = int(series_data['series_year'])
        recent_season = int(series_data['recent_season'])
        series_titles = series_data['series_title']['titles']
        series_origin_lang = series_data['series_title']['orig']
        recent_episode = int(episode_data['sequence'])

        # fetch series folder structure
        construction_series_folder = str(series_data['construction_series_folder'])
        if recent_season == 1 and recent_episode == 1:
            if not need_to_file:
                print("==========")
                print(f"Series: {series_data['series_sanitized_title']}")
                print("==========")
            else:
                print(construction_series_folder)
                self.create_folder(construction_series_folder)
                self.create_folder(os.path.join(construction_series_folder, 'screenshots'))
                self.create_folder(os.path.join(construction_series_folder, 'thumbnails'))
                series_data = {
                    "category": self.category,
                    "mediatypes": [],
                    "level": "series",
                    "title": {
                        "onthumbnail": True,
                        "showsequence": "part",
                        "orig": series_origin_lang,
                        "titles": series_titles
                    },
                    "storylines": {
                        "en": series_story,
                        "hu": ""
                    },
                    "date": series_year,
                    "origins": episode_data['origins'],
                    "id": {
                        "name": "imdb",
                        "value": series_imdb_id
                    }
                }
                # Write series data to card.yaml
                card_path = os.path.join(construction_series_folder, 'card.yaml')
                with open(card_path, 'w') as f:
                    yaml.dump(series_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)

        # Create season folder structure
        formatted_season = f"S{self.format_number(recent_season)}"
        season_folder = os.path.join(construction_series_folder, formatted_season)
        if recent_episode == 1:
            if not need_to_file:
                print("---------")
                print(f"Season: {recent_season}")
                print("---------")
            else:
                print(f'  {season_folder}')
                self.create_folder(season_folder)
                self.create_folder(os.path.join(season_folder, 'screenshots'))
                self.create_folder(os.path.join(season_folder, 'thumbnails'))

                titles ={}
                title_language_list = list(series_titles.keys())
                for language_code in title_language_list:
                    titles[language_code] = season_title_translate.get(language_code, "Season {0}").format(recent_season)

                season_data = {
                    "category": self.category,
                    "mediatypes": [],
                    "level": "season",
                    "sequence": recent_season,
                    "title": {
                        "onthumbnail": True,
                        "showsequence": "part",
                        "orig": series_origin_lang,
                        "titles": titles
                    }
                }
                # Write series data to card.yaml
                card_path = os.path.join(season_folder, 'card.yaml')
                with open(card_path, 'w') as f:
                    yaml.dump(season_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)

        episode_folder = os.path.join(season_folder, f"E{self.format_number(recent_episode)}")
        yaml_output = yaml.dump(episode_data, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
        if not need_to_file:
            print(yaml_output)
        else:
            print(f'    {episode_folder}')

            # Create episode folder structure
            episode_folder = os.path.join(season_folder, f"E{self.format_number(recent_episode)}")
            self.create_folder(episode_folder)
            self.create_folder(os.path.join(episode_folder, 'screenshots'))
            self.create_folder(os.path.join(episode_folder, 'thumbnails'))
            self.create_folder(os.path.join(episode_folder, 'media'))

            # Write episode data to card.yaml
            card_path = os.path.join(episode_folder, 'card.yaml')
            with open(card_path, 'w') as f:
                yaml.dump(episode_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)

if __name__ == "__main__":

    API_KEY = "4388f276"

    # LANGUAGE_COUNTRY
    EXTRA_ISO_COUNTRY_CODE_LIST = ["hu-HU"]
    CATEGORY = "movie"
    PRIMARYMEDIATYPE = "video"
    SOUNDS = ["hu", "en"]
    SUBS = ["en"]
    THEMES = []

    IMDB_ID = "tt0163978"  # IMDB ID for individual movie - The beach
    IMDB_ID = "tt0308671"  # IMDB ID for individual movie - TycoonÉ A new russion
    IMDB_ID = "tt0137523"  # IMDB ID for individual movie - Fight club
    IMDB_ID = "tt0098936"  # IMDB ID for series - Twin Peaks
    IMDB_ID = "tt0108778"  # IMDB ID for series - Friends
#    IMDB_ID = "tt0106179"  # IMDB ID for series - X Files

    cons_path = os.path.expanduser('~/tmp/homeflix/')
    dest_path = os.path.expanduser('/media/akoel/vegyes/MEDIA/01.Movie/01.Standalone')

    need_to_copy_to_destination_path = False
    need_to_file = True

    gmfs = GenerateMediaFileSystem(api_key=API_KEY, imdb_id=IMDB_ID, construction_path=cons_path, destination_path=dest_path, need_to_copy_to_destination_path=need_to_copy_to_destination_path, need_to_file=need_to_file, category=CATEGORY, primary_media_type=PRIMARYMEDIATYPE, sounds=[], subs=[], themes=[], extra_iso_country_code_list=EXTRA_ISO_COUNTRY_CODE_LIST)



