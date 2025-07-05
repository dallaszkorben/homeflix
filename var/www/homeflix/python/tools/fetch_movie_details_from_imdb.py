import requests
from bs4 import BeautifulSoup
import re
import os
import yaml
import json
import urllib.parse

class FetchImdb:
    # Class level locator variables
    DETAILS_SECTION = 'section[data-testid="Details"]'
    COUNTRIES_LOCATOR = 'li[data-testid="title-details-origin"] a'
    LANGUAGE_LOCATOR = 'li[data-testid="title-details-languages"] a'
    TITLE_LOCATOR = 'h1[data-testid="hero__pageTitle"] span'
    ORIGINAL_TITLE_LOCATOR = 'li[data-testid="title-details-originaltitle"]'
    AKA_COUNTRY_LOCATOR = 'span.ipc-metadata-list-item__label'

    AKA_SECTION_LOCATOR = 'div[data-testid="sub-section-akas"]'
    AKA_LABEL_LOCATOR = 'span.ipc-metadata-list-item__label'
    AKA_CONTENT_LOCATOR = 'div.ipc-metadata-list-item__content-container'
    AKA_TITLE_LOCATOR = 'span.ipc-metadata-list-item__list-content-item'
    TYPE_METADATA_LOCATOR = 'ul[data-testid="hero-title-block__metadata"] li'
    PAGE_TITLE_LOCATOR = 'title'
    YEAR_LOCATOR = 'a[href*="releaseinfo"]'
    LENGTH_LOCATOR = 'li[data-testid="title-techspec_runtime"] div'
    GENRES_LOCATOR = 'div[data-testid="interests"] a'

    MAIN_CAST_SECTION_LOCATOR = 'li[data-testid="title-pc-principal-credit"]'
    MAIN_CAST_PERSON_LOCATOR = 'div.ipc-metadata-list-item__content-container ul a'

    CAST_ROW_LOCATOR = 'div[data-testid="sub-section-cast"] li[data-testid="name-credits-list-item"] '
    ACTOR_NAME_LOCATOR = 'a[class="ipc-link ipc-link--base name-credits--title-text name-credits--title-text-big"]'
    CHARACTER_LOCATOR = 'a[class="ipc-link ipc-link--base ipc-link--inherit-color"]'

    WRITERS_ROW_LOCATOR = 'div[data-testid="sub-section-writer"] li a[class="ipc-link ipc-link--base name-credits--title-text name-credits--title-text-big"]'

    DIRECTORS_ROW_LOCATOR = 'div[data-testid="sub-section-director"] li a[class="ipc-link ipc-link--base name-credits--title-text name-credits--title-text-big"]'

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
        'ro': ['ro'],
        'br': ['pt']
    }

    def __init__(self, imdb_id):
        self.imdb_id = imdb_id
        self.url = f"https://www.imdb.com/title/{imdb_id}/"
        self.soup = None
        self._fetch_page()
        self._load_dictionary()
        self._collect_data()

    def _fetch_page(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(self.url, headers=headers)
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def _load_dictionary(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dictionary_path = os.path.join(current_dir, '..', 'homeflix', 'translator', 'dictionary.yaml')
        with open(dictionary_path, 'r') as file:
            self.dictionary = yaml.safe_load(file)

    def _collect_data(self):
        self.original_countries = self._extract_countries()
        self.original_language = self._extract_language()
        self.original_title = self._extract_title()
        self.type = self._extract_type()
        self.year = self._extract_year()
        self.titles = self._extract_titles()
        self.length = self._extract_length()
        self.genres = self._extract_genres()
        self.stars = self._extract_stars()
        self.actors = self._extract_actors()
        self.writers = self._extract_writers()
        self.directors = self._extract_directors()

    def _get_country_code_by_name(self, country_name):
        country_map = {v.lower(): k for k, v in self.dictionary['country']['long'].items()}
        return country_map.get(country_name.lower())

    def _get_language_code_by_name(self, language_name):
        language_map = {v.lower(): k for k, v in self.dictionary['language']['long'].items()}
        return language_map.get(language_name.lower())

    def _get_language_code_list_by_country_code_list(self, country_code_list):
        """Convert country codes to their primary language codes"""
        language_code_list = []
        for country in country_code_list:
            if country in self.country_language:
                lang = self.country_language[country][0]
                language_code_list.append(lang)
        return list(set(language_code_list))

    def _extract_countries(self):
        countries = self.soup.select(self.COUNTRIES_LOCATOR)
        country_codes = []
        for country in countries:
            country_name = country.get_text(strip=True)
            country_code = self._get_country_code_by_name(country_name)
            if country_code:
                country_codes.append(country_code)
        return country_codes

    def _extract_language(self):
        language_elem = self.soup.select_one(self.LANGUAGE_LOCATOR)
        if language_elem:
            language_name = language_elem.get_text(strip=True)
            return self._get_language_code_by_name(language_name)
        return None

    def _extract_title(self):
        # Fetch releaseinfo page for full AKA list
        releaseinfo_url = f"https://www.imdb.com/title/{self.imdb_id}/releaseinfo"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
        response = requests.get(releaseinfo_url, headers=headers)
        releaseinfo_soup = BeautifulSoup(response.content, 'html.parser')

        # Look for (original title) in AKA section on releaseinfo page
        aka_section = releaseinfo_soup.select_one(self.AKA_SECTION_LOCATOR)
        if aka_section:

            # Find the list item with (original title) label
            original_items = aka_section.find_all(self.AKA_LABEL_LOCATOR.split('.')[1], class_=self.AKA_LABEL_LOCATOR.split('.')[1], string='(original title)')
            for item in original_items:
                # Get the content container next to the label
                content_container = item.find_next_sibling(self.AKA_CONTENT_LOCATOR.split('.')[0], class_=self.AKA_CONTENT_LOCATOR.split('.')[1])
                if content_container:
                    title_span = content_container.select_one(self.AKA_TITLE_LOCATOR)
                    if title_span:
                        return title_span.get_text(strip=True)

        # Fallback to main title
        title_elem = self.soup.select_one(self.TITLE_LOCATOR)
        return title_elem.get_text(strip=True) if title_elem else None

    def _extract_titles(self):

        # Fetch the values:
        # 1. Use Firefox (Chrome will encode the result what we need)
        # 1. F12
        # 2. Go to 'Details' section
        # 3. Click on 'Also Known as'
        # 4. Investigator -> Network -> XHR -> Headers
        # 5. Clear Network log
        # 6. Find the last successful network call (Response->data:{title:{...}}) -> click on it
        # 7. base_url = Headers -> Request Headers -> Host
        # 8. graphQL = Headers -> Get -> extensions={"persistedQuery":{"sha256Hash":"{graphQL}","version":1}}
        base_url = "https://caching.graphql.imdb.com/"
        graphQL =  "48d4f7bfa73230fb550147bd4704d8050080e65fe2ad576da6276cac2330e446"

        variables = {
            "const": self.imdb_id,
            "first": 100,
            "locale": "en-US",
            "originalTitleText": True
        }

        extensions = {
            "persistedQuery": {
                "sha256Hash": graphQL,
                "version": 1
            }
        }

        params = {
            'operationName': 'TitleAkasPaginated',
            'variables': json.dumps(variables, separators=(',', ':')),
            'extensions': json.dumps(extensions, separators=(',', ':'))
        }

        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Referer': f'https://www.imdb.com/title/{self.imdb_id}/releaseinfo'
        }

        titles = {}
        response = requests.get(url, headers=headers)
        titles_json = response.json()
        titles_list = titles_json['data']['title']['akas']['edges']
        for title_json in titles_list:
            title = title_json['node']['displayableProperty']['value']['plainText']
            language = title_json['node']['language']
            if language:
                lang_code = language["id"]
                if lang_code not in self.dictionary['language']['short']:
                    continue
                titles[lang_code] = title
            else:
                country_code = title_json['node']['country']['id'].lower()
                if country_code not in self.country_language:
                    continue
                if country_code and title:
                    language_codes = self._get_language_code_list_by_country_code_list([country_code])
                    for lang_code in language_codes:
                        titles[lang_code] = title
        return titles

    def _extract_type(self):
        # Check for TV series in title metadata
        title_type = self.soup.select_one(self.TYPE_METADATA_LOCATOR)
        if title_type and 'TV Series' in title_type.get_text():
            return 'series'

        # Check page title for series indicator
        page_title = self.soup.find(self.PAGE_TITLE_LOCATOR)
        if page_title and 'TV Series' in page_title.get_text():
            return 'series'

        return 'movie'

    def _extract_year(self):
        year_elem = self.soup.select_one(self.YEAR_LOCATOR)
        if year_elem:
            year_match = re.search(r'\d{4}', year_elem.get_text())
            return year_match.group() if year_match else None
        return None

    def _extract_length(self):
        length_elem = self.soup.select_one(self.LENGTH_LOCATOR)
        if length_elem:
            length_text = length_elem.get_text(strip=True)
            # Extract minutes from text like "119 minutes" or "1h 59m"
            if 'h' in length_text and 'm' in length_text:
                # Format: "1h 59m"
                hours_match = re.search(r'(\d+)h', length_text)
                minutes_match = re.search(r'(\d+)m', length_text)
                hours = int(hours_match.group(1)) if hours_match else 0
                minutes = int(minutes_match.group(1)) if minutes_match else 0
                total_minutes = hours * 60 + minutes
            else:
                # Format: "119 minutes"
                minutes_match = re.search(r'(\d+)', length_text)
                total_minutes = int(minutes_match.group(1)) if minutes_match else 0

            # Convert to hh:mm:ss format
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours:02d}:{minutes:02d}:00"
        return None

    def _extract_genres(self):
        genre_elems = self.soup.select(self.GENRES_LOCATOR)
        genres = []
        for genre_elem in genre_elems:
            genre = genre_elem.get_text(strip=True).lower()
            translated_genre = self._translate_genre(genre)
            genres.append(translated_genre)
        return genres

    def _translate_genre(self, genre):
        genre_dict = {
            "scifi": "sci-fi",
            "film-noir": "film_noir"
        }

        # Convert input to lowercase to make the search case-insensitive
        genre_lower = genre.lower()

        # Return the translated genre if found, otherwise return the original genre
        return genre_dict.get(genre_lower, genre_lower)

    # Add extraction method
    def _extract_stars(self):
        # Find the li element that contains "Stars" text and get the actor links
        stars_li = None
        for li in self.soup.select(self.MAIN_CAST_SECTION_LOCATOR):
            if li.find('a', string='Stars'):
                stars_li = li
                break
        if stars_li:
            # Get all actor links from the content container
            star_elems = stars_li.select(self.MAIN_CAST_PERSON_LOCATOR)
            stars = []
            for star_elem in star_elems:
                star_name = star_elem.get_text(strip=True)
                if star_name:
                    stars.append(star_name)
            return stars

        return []

    def _fetch_fullcredits_page(self):
        """Fetch fullcredits page once and store the soup"""
        if not hasattr(self, 'fullcredits_soup'):
            fullcredits_url = f"https://www.imdb.com/title/{self.imdb_id}/fullcredits"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
            response = requests.get(fullcredits_url, headers=headers)
            self.fullcredits_soup = BeautifulSoup(response.content, 'html.parser')


    def _extract_actors(self):
        self._fetch_fullcredits_page()

        actors = {}
        cast_rows = self.fullcredits_soup.select(self.CAST_ROW_LOCATOR)

        for row in cast_rows:
            actor_elem = row.select_one(self.ACTOR_NAME_LOCATOR)
            character_elem = row.select_one(self.CHARACTER_LOCATOR)

            if actor_elem and character_elem:
                actor_name = actor_elem.get_text(strip=True)
                character = character_elem.get_text(strip=True)

                # Clean up character text (remove extra whitespace, newlines)
                character = re.sub(r'\s+', ' ', character).strip()

                if actor_name and character:
                    actors[actor_name] = character

        return actors

    def _extract_writers(self):
        self._fetch_fullcredits_page()

        writers = []
        writer_rows = self.fullcredits_soup.select(self.WRITERS_ROW_LOCATOR)

        for row in writer_rows:
            writer_name = row.get_text(strip=True)
            if writer_name:
                writers.append(writer_name)
        return writers

    def _extract_directors(self):
        self._fetch_fullcredits_page()

        directors = []
        director_rows = self.fullcredits_soup.select(self.DIRECTORS_ROW_LOCATOR)

        for row in director_rows:
            director_name = row.get_text(strip=True)
            if director_name:
                directors.append(director_name)
        return directors

    def getOriginalCountries(self):
        return self.original_countries

    def getOriginalLanguage(self):
        return self.original_language

    def getOriginalTitle(self):
        return self.original_title

    def getType(self):
        return self.type

    def getYear(self):
        return self.year
    def getTitles(self):
        return self.titles

    def getLength(self):
        return self.length

    def getGenres(self):
        return self.genres

    def getStars(self):
        return self.stars

    def getActors(self):
        return self.actors

    def getWriters(self):
        return self.writers

    def getDirectors(self):
        return self.directors

if __name__ == "__main__":

    EXTRA_ISO_COUNTRY_CODE_LIST = ["hu-HU"]
    CATEGORY = "movie"
    PRIMARYMEDIATYPE = "video"
    SOUNDS = ["hu", "en"]
    SUBS = ["en"]
    THEMES = []

    IMDB_ID = "tt0163978"  # IMDB ID for individual movie - The beach
#    IMDB_ID = "tt0308671"  # IMDB ID for individual movie - Tycoon A new russion
#    IMDB_ID = "tt0137523"  # IMDB ID for individual movie - Fight club

#    IMDB_ID = "tt0098936"  # IMDB ID for series - Twin Peaks
#    IMDB_ID = "tt0108778"  # IMDB ID for series - Friends
#    IMDB_ID = "tt0106179"  # IMDB ID for series - X Files
#    IMDB_ID = "tt0078350"  # IMDB ID for individual movie - The Swarm

    cons_path = os.path.expanduser('~/tmp/homeflix/')
    dest_path = os.path.expanduser('/media/akoel/vegyes/MEDIA/01.Movie/01.Standalone')

    need_to_copy_to_destination_path = False
    need_to_file = True

    imdb = FetchImdb(IMDB_ID)
    type = imdb.getType()
    original_title = imdb.getOriginalTitle()
    original_countries = imdb.getOriginalCountries()
    original_language = imdb.getOriginalLanguage()
    year = imdb.getYear()
    titles = imdb.getTitles()
    length = imdb.getLength()
    genres = imdb.getGenres()
    stars = imdb.getStars()
    actors = imdb.getActors()
    writers = imdb.getWriters()
    directors = imdb.getDirectors()

    print(f"Type: {type}")
    print(f"Year: {year}")
    print(f"Original Title: {original_title}")
    print(f"Original Countries: {original_countries}")
    print(f"Original Language: {original_language}")
    print(f"Titles: {titles}")
    print(f"Length: {length}")
    print(f"Genres: {genres}")
    print(f"Stars: {stars}")
    print(f"Actors: {actors}")
    print(f"Writers: {writers}")
    print(f"Directors: {directors}")



