import requests
import yaml
from imdb import IMDb

# Replace with your OMDb API key
API_KEY = "4388f276"

IMDB_ID = "tt0386676"  # IMDb ID for the series
RECENT_SEASON = 6      # Change this to the desired season

CATEGORY = "movie"
PRIMARYMEDIATYPE = "video"
LENGTH = "0:20:22"
NETSTART = "0:01:28"
NETSTOP = "0:19:00"
sounds = ["hu", "en"]
subs = ["en"]
genres = ["comedy"]
themes = []

def get_episode_details(ia, episode_id, origins):

    episode = ia.get_movie(episode_id[2:])  # Remove 'tt' from IMDb ID
    sequence = episode.get("episode", 0)
    en_title = episode.get("episode title", "")
    en_storyline = episode.get('plot')[0]
    year = episode.get('year')

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
            "orig": "en",
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
    episode = ia.get_movie(IMDB_ID[2:])
    origins = episode.get("country codes", [])

    # for getting the episode list
    url = f"http://www.omdbapi.com/?i={IMDB_ID}&Season={RECENT_SEASON}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

#    if "Episodes" not in data:
#        print(f"Error fetching season {season}: {data.get('Error', 'Unknown error')}")
#        return

    episode_list = []
    for idx, episode in enumerate(data["Episodes"], start=1):
        episode_id = episode["imdbID"]


#        url = f"http://www.omdbapi.com/?i={episode_id}&apikey={API_KEY}"
#        response = requests.get(url)
#        data = response.json()
#        print(data.get("Country", "non"))

        episode_data = get_episode_details(ia, episode_id, origins)
        yaml_output = yaml.dump(episode_data, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
        print(yaml_output)
        print("\n\n")


if __name__ == "__main__":
    main()
