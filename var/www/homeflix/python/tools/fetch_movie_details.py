import requests
import os
import re
import yaml
from imdb import IMDb

# Replace with your IMDb API key
API_KEY = "4388f276"

IMDB_ID = "tt0407362"  # IMDb ID for the series - Battlestar Galactica
IMDB_ID = "tt2861424"  # IMDb ID for the series - Rick and Morty
IMDB_ID = "tt0799862"  # IMDb ID for the series - Caprica

CATEGORY = "movie"
PRIMARYMEDIATYPE = "video"
LENGTH = "0:20:22"
NETSTART = "0:01:28"
NETSTOP = "0:19:00"
sounds = ["hu", "en"]
subs = ["en"]
themes = []
orig_lang = "en"

construction_path = os.path.expanduser('~/tmp/homeflix/')
destination_path = os.path.expanduser('/media/akoel/vegyes/MEDIA/01.Movie/03.Series/02-Series')

need_to_copy_to_destination_path = True
need_to_file = True

def sanitize_title(title):
    # Remove special characters and replace spaces with dots
    sanitized = re.sub(r'[\'\":,]', '', title)
    sanitized = sanitized.replace(' ', '.')
    return sanitized

def format_number(num):
    return f"{int(num):02d}"

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def handle_episode(episode_data, extra_data):

    series_imdb_id = str(extra_data['series_imdb_id'])
    series_story = str(extra_data['series_story'])
    series_title = str(extra_data['series_title'])
    series_year = int(extra_data['series_year'])
    recent_season = int(extra_data['recent_season'])
    recent_episode = int(episode_data['sequence'])

    # fetch series folder structure
    construction_series_folder = str(extra_data['construction_series_folder'])
#    construction_series_folder = os.path.join(construction_path, f"{sanitize_title(series_title)}-{series_year}")
    if recent_season == 1 and recent_episode == 1:
        if not need_to_file:
            print("==========")
            print(f"Series: {extra_data['series_title']} - {series_year}")
            print("==========")
        else:
            print(construction_series_folder)
            create_folder(construction_series_folder)
            create_folder(os.path.join(construction_series_folder, 'screenshots'))
            create_folder(os.path.join(construction_series_folder, 'thumbnails'))
            series_data = {
                "category": CATEGORY,
                "mediatypes": [],
                "level": "series",
                "title": {
                    "onthumbnail": True,
                    "showsequence": "part",
                    "orig": orig_lang,
                    "titles": {"en": series_title, "hu": ""}
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
    formatted_season = f"S{format_number(recent_season)}"
    season_folder = os.path.join(construction_series_folder, formatted_season)
    if recent_episode == 1:
        if not need_to_file:
            print("---------")
            print(f"Season: {recent_season}")
            print("---------")
        else:
            print(f'  {season_folder}')
            create_folder(season_folder)
            create_folder(os.path.join(season_folder, 'screenshots'))
            create_folder(os.path.join(season_folder, 'thumbnails'))
            season_data = {
                "category": CATEGORY,
                "mediatypes": [],
                "level": "season",
                "sequence": recent_season,
                "title": {
                    "onthumbnail": True,
                    "showsequence": "part",
                    "orig": orig_lang,
                    "titles": {"en": formatted_season, "hu": f"{recent_season}. évad"}
                }
            }
            # Write series data to card.yaml
            card_path = os.path.join(season_folder, 'card.yaml')
            with open(card_path, 'w') as f:
                yaml.dump(season_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)

    episode_folder = os.path.join(season_folder, f"E{format_number(recent_episode)}")
    yaml_output = yaml.dump(episode_data, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
    if not need_to_file:
        print(yaml_output)
    else:
        print(f'    {episode_folder}')

        # Create episode folder structure
        episode_folder = os.path.join(season_folder, f"E{format_number(recent_episode)}")
        create_folder(episode_folder)
        create_folder(os.path.join(episode_folder, 'screenshots'))
        create_folder(os.path.join(episode_folder, 'thumbnails'))
        create_folder(os.path.join(episode_folder, 'media'))

        # Write episode data to card.yaml
        card_path = os.path.join(episode_folder, 'card.yaml')
        with open(card_path, 'w') as f:
            yaml.dump(episode_data, f, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)

def get_episode_details(ia, episode_id):

    episode = ia.get_movie(episode_id[2:])  # Remove 'tt' from IMDb ID

    sequence = episode.get("episode", 0)
    en_title = episode.get("episode title", "__")
    en_storyline = episode.get('plot')[0]
    year = episode.get('year')

    origins = list({origin for origin in episode.get("country codes", [])})
    genres = list({genre.lower() for genre in episode.get("genres", [])})
    directors = list({director["name"] for director in episode.data["director"] if "name" in director})
    writers = list({writer["name"] for writer in episode.data["writer"] if "name" in writer})
    actors = {actor["name"]: str(actor.currentRole) if actor.currentRole else "" for actor in episode["cast"]} if "cast" in episode else {}
    stars = [actor["name"] for actor in episode["cast"][:3]]

    episode_data = {
        "category": CATEGORY,
        "primarymediatype": PRIMARYMEDIATYPE,
        "sequence": sequence,
        "title": {
            "onthumbnail": True,
            "showsequence": "part",
            "orig": orig_lang,
            "titles": {"en": en_title, "hu": ""}
        },
        "storylines": {
            "en": en_storyline,
            "hu": ""
        },
        "date": year,
        "length": LENGTH,
        "netstart": NETSTART,
        "netstop": NETSTOP,
        "directors": directors,
        "writers": writers,
        "stars": stars,
        "actors": actors,
        "sounds": sounds,
        "subs": subs,
        "genres": genres,
        "themes": themes,
        "origins": origins,
        "id": {
            "name": "imdb",
            "value": episode_id
        }
    }

    return episode_data

class MyDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def main():

    ia = IMDb()

    # for getting the origin countries
#    episode = ia.get_movie(IMDB_ID[2:])
#    origins = episode.get("country codes", [])

    recent_season = 1

    # for getting the total_seasons, series_title and first year
    url = f"http://www.omdbapi.com/?i={IMDB_ID}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    total_seasons = int(data["totalSeasons"])
    series_imdb_id = data["imdbID"]
    series_title = data["Title"]
    series_story = data["Plot"]
    series_year = re.split(r'[-–]', data["Year"])[0]

    # The series folder only once should be created
    construction_series_folder = os.path.join(construction_path, f"{sanitize_title(series_title)}-{series_year}")

    # Go through all the seasons
    for recent_season in range(1, total_seasons + 1):

        extra_data = {
            "series_imdb_id": series_imdb_id,
            "series_story": series_story,
            "series_title": series_title,
            "series_year": series_year,
            "recent_season": recent_season,
            "construction_series_folder": construction_series_folder
        }

        # for getting the episode list
        url = f"http://www.omdbapi.com/?i={IMDB_ID}&Season={recent_season}&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()

        episode_list = []
        for idx, episode in enumerate(data["Episodes"], start=1):
            episode_id = episode["imdbID"]

#        url = f"http://www.omdbapi.com/?i={episode_id}&apikey={API_KEY}"
#        response = requests.get(url)
#        data = response.json()
#        print(data.get("Country", "non"))

            episode_data = get_episode_details(ia, episode_id)
            handle_episode(episode_data, extra_data)

    if need_to_file and need_to_copy_to_destination_path:
        os.system(f"cp -r {construction_series_folder} {destination_path}")

if __name__ == "__main__":
    main()
