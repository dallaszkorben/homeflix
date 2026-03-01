import http.client
import json
import os
import re
import yaml
from pytlib.fetch_imdb import FetchImdb
from pytlib.generate_cards_from_imdb import GenerateCardsFromImdb

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
    IMDB_ID = "tt0069113"   # IMDB ID for individual movie - The Poseidon Adventure
    IMDB_ID = "tt0093870"   # IMDB ID for individual movie - Robocop
    IMDB_ID = "tt0121403"   # IMDB ID for individual movie - The Stationmaster Meets His Match
    IMDB_ID = "tt0085404"   # IMDB ID for individual movie - The Day After
    IMDB_ID = "tt1645170"   # IMDB ID for individual movie - The Dictator
    IMDB_ID = "tt0066921"   # IMDB ID for individual movie - A Clockwork Orange
    IMDB_ID = "tt0258463"   # IMDB ID for individual movie - The Bourne Identity
    IMDB_ID = "tt0121387"   # IMDB ID for individual movie - Hófehér
    IMDB_ID = "tt0155267"   # IMDB ID for individual movie - The Thomas Crown Affair

    IMDB_ID = "tt0098936"   # IMDB ID for series - Twin Peaks
    IMDB_ID = "tt0106179"   # IMDB ID for series - X Files
    IMDB_ID = "tt0407362"   # IMDB ID for series - Battlestar Galactica
    IMDB_ID = "tt0108778"   # IMDB ID for series - Friends
    IMDB_ID = "tt2861424"   # IMDB ID for series - Rick and Morty
    IMDB_ID = "tt0182576"   # IMDB ID for series - Family Guy
    IMDB_ID = "tt0096697"   # IMDB ID for series - Simpsons
    IMDB_ID = "tt1466074"   # IMDB ID for series - Columbo
    IMDB_ID = "tt0372183"   # IMDB ID for series - The Bourne Supremacy
    IMDB_ID = "tt0440963"   # IMDB ID for series - The Bourne Ultimatum
    IMDB_ID = "tt1194173"   # IMDB ID for series - The Bourne Legacy
    IMDB_ID = "tt4196776"   # IMDB ID for series - Jason Bourne
    IMDB_ID = "tt0124218"   # IMDB ID for series - Csengetett mylord


    IMDB_ID = "tt0155267"

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

