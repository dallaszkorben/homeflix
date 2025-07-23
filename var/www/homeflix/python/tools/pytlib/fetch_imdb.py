import requests
from bs4 import BeautifulSoup
import re
import os
import yaml
import json
import urllib.parse
import shutil

class FetchImdb:
    # Class level locator variables
    DETAILS_SECTION = 'section[data-testid="Details"]'
    COUNTRIES_LOCATOR = 'li[data-testid="title-details-origin"] a'
    LANGUAGE_LOCATOR = 'li[data-testid="title-details-languages"] a'
    TITLE_LOCATOR = 'h1[data-testid="hero__pageTitle"] span'
    ORIGINAL_TITLE_LOCATOR = 'li[data-testid="title-details-originaltitle"]'
    STORYLINE_LOCATOR = 'div[class="ipc-html-content-inner-div"] div[class="ipc-html-content-inner-div"]'

    AKA_COUNTRY_LOCATOR = 'span.ipc-metadata-list-item__label'
    AKA_SECTION_LOCATOR = 'div[data-testid="sub-section-akas"]'
    AKA_LABEL_LOCATOR = 'span.ipc-metadata-list-item__label'
    AKA_CONTENT_LOCATOR = 'div.ipc-metadata-list-item__content-container'
    AKA_TITLE_LOCATOR = 'span.ipc-metadata-list-item__list-content-item'
    TYPE_METADATA_LOCATOR = 'ul[data-testid="hero-title-block__metadata"] li'
    PAGE_TITLE_LOCATOR = 'title'

    YEAR_LOCATOR = 'li[data-testid="title-details-releasedate"] a[class="ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link"][href*="/releaseinfo/"] '

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
        self.soup = None
        self.movie = {}
        self.movie['base'] = {}
        self.movie['seasons'] = []

        self._load_dictionary()

        self._refresh_progress_bar(count=1, index=0, text='Movie', value=None, progress_width=None)
        self._collect_data(imdb_id, self.movie['base'])
        self._refresh_progress_bar(count=1, index=1, text='Movie', value=None, progress_width=None)
        print()

        if self.movie['base']['type'] == 'series':
            self.seasons_count = self._extract_seasons_count()

            # calculate the length
            full_episode_count_elem = self.soup.select_one('section[data-testid="episodes-widget"] span[class="ipc-title__subtext"]')

            if full_episode_count_elem:
                full_episode_count = int(full_episode_count_elem.get_text(strip=True))
            else:
                full_episode_count = 1
            full_episode_index = 1

            for season in range(1, self.seasons_count + 1):

                seasons_list = []

                # open the recent season's page
                self._fetch_episodes_page(self.imdb_id, season)

                episode_row = self.episodes_soup.select('h4[data-testid="slate-list-card-title"] a[class="ipc-title-link-wrapper"]')
                episode_index = 1
                for episode in episode_row:

                    full_episode_index = self._refresh_progress_bar(count=full_episode_count, index=full_episode_index, text='Season', value=season, progress_width=None)

                    imdb_id = episode['href'].split('/')[2]

                    recent_episode_dict = {}
                    recent_episode_dict['sequence'] = episode_index
                    self._collect_data(imdb_id, recent_episode_dict)

                    seasons_list.append(recent_episode_dict)

                    episode_index += 1

                self.movie['seasons'].append(seasons_list)

            # new line after the progress bar
            print()

    def _refresh_progress_bar(self, count, index, text=None, value=None, progress_width=None):

        if progress_width is None:
            terminal_width = shutil.get_terminal_size().columns
            progress_width = terminal_width - 30  # Reserve space for text

        progress = int((index / count) * progress_width)
        bar = '\033[92m' + '▄' * progress + '\033[94m' + '▁' * (progress_width - progress) + '\033[0m'

        pre_text = ''
        if text:
            pre_text += text
        if value:
            pre_text += f'-{value}'
        if text or value:
            pre_text += ': '

        print(f'\r{pre_text}[{bar}] {index}/{count}\033[K', end='', flush=True)

        return index + 1

    def _reset_pages(self):
        if hasattr(self, 'releaseinfo_soup'):
            del self.releaseinfo_soup

        if hasattr(self, 'fullcredits_soup'):
            del self.fullcredits_soup

        if hasattr(self, 'episode_soup'):
            del self.episode_soup

        if hasattr(self, 'plotsummary_soup'):
            del self.plotsummary_soup

    def _load_dictionary(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dictionary_path = os.path.join(current_dir, '../..', 'homeflix', 'translator', 'dictionary.yaml')
        with open(dictionary_path, 'r') as file:
            self.dictionary = yaml.safe_load(file)

        self.existing_genres = [k for k, v in self.dictionary['genre']['movie'].items()]

    def _collect_data(self, imdb_id, source):
        self._reset_pages()

        self._fetch_main_page(imdb_id)

        source['id'] = {'name': 'imdb', 'value': imdb_id}
        source['category'] = 'movie'
        source['type'] = self._extract_type()
        source['original_countries'] = self._extract_countries()
        source['original_language'] = self._extract_language()
        source['original_title'] = self._extract_title(imdb_id)
        source['storyline'] = self._extract_storyline(imdb_id)
        source['year'] = self._extract_year()
        source['titles'] = self._extract_titles(imdb_id)
        source['length'], source['runtime_sec'] = self._extract_length()
        source['genres'] = self._extract_genres()
        source['stars'] = self._extract_stars()
        source['actors'] = self._extract_actors(imdb_id)
        source['writers'] = self._extract_writers(imdb_id)
        source['directors'] = self._extract_directors(imdb_id)

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

    def _extract_title(self, imdb_id):
        self._fetch_releaseinfo_page(imdb_id)

        # Look for (original title) in AKA section on releaseinfo page
        aka_section = self.releaseinfo_soup.select_one(self.AKA_SECTION_LOCATOR)
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

    def _extract_titles(self, imdb_id):

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
            "const": imdb_id,
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
            'Referer': f'https://www.imdb.com/title/{imdb_id}/releaseinfo'
        }

        titles = {}
        response = requests.get(url, headers=headers)
        titles_json = response.json()

        if not titles_json or not titles_json.get('data') or not titles_json['data'].get('title') or not titles_json['data']['title'].get('akas') or not titles_json['data']['title']['akas'].get('edges'):
            return titles
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
                if title_json['node']['country']:
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
            return f"{hours:02d}:{minutes:02d}:00", total_minutes*60
        return None, None

    def _extract_genres(self):
        genre_elems = self.soup.select(self.GENRES_LOCATOR)
        genres = []
        for genre_elem in genre_elems:
            genre = genre_elem.get_text(strip=True).lower()
            translated_genre = self._translate_genre(genre)
            if translated_genre:
                genres.append(translated_genre)
        return genres

    def _translate_genre(self, genre):
        genre_dict = {
            "scifi": "sci-fi",
            "film-noir": "film_noir"
        }

        converted_genre = genre.lower().replace("-", "_").replace(" ", "_")
        converted_genre = genre_dict.get(converted_genre, converted_genre)
        converted_genre = converted_genre if converted_genre in self.existing_genres else ""

        return converted_genre

    def _extract_storyline(self, imdb_id):
        self._fetch_plotsummary_page(imdb_id)

        storyline_row = self.plotsummary_soup.select_one(self.STORYLINE_LOCATOR)
        if storyline_row:
            storyline = storyline_row.get_text(strip=True)
        else:
            storyline = ''

        return storyline

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

    def _extract_actors(self, imdb_id):
        self._fetch_fullcredits_page(imdb_id)

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

    def _extract_writers(self, imdb_id):
        self._fetch_fullcredits_page(imdb_id)

        writers = []
        writer_rows = self.fullcredits_soup.select(self.WRITERS_ROW_LOCATOR)

        for row in writer_rows:
            writer_name = row.get_text(strip=True)
            if writer_name:
                writers.append(writer_name)

        # remove duplications
        return list(set(writers))

    def _extract_directors(self, imdb_id):
        self._fetch_fullcredits_page(imdb_id)

        directors = []
        director_rows = self.fullcredits_soup.select(self.DIRECTORS_ROW_LOCATOR)

        for row in director_rows:
            director_name = row.get_text(strip=True)
            if director_name:
                directors.append(director_name)
        return directors

# --- open pages ---

    def _fetch_main_page(self, imdb_id):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        url = f"https://www.imdb.com/title/{imdb_id}/"
        response = requests.get(url, headers=headers)
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def _fetch_plotsummary_page(self, imdb_id):
        if not hasattr(self, 'plotsummary_soup'):
            releaseinfo_url = f"https://www.imdb.com/title/{imdb_id}/plotsummary"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
            response = requests.get(releaseinfo_url, headers=headers)
            self.plotsummary_soup = BeautifulSoup(response.content, 'html.parser')

    def _fetch_releaseinfo_page(self, imdb_id):
        if not hasattr(self, 'releaseinfo_soup'):
            releaseinfo_url = f"https://www.imdb.com/title/{imdb_id}/releaseinfo"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
            response = requests.get(releaseinfo_url, headers=headers)
            self.releaseinfo_soup = BeautifulSoup(response.content, 'html.parser')

    def _fetch_fullcredits_page(self, imdb_id):
        """Fetch fullcredits page once and store the soup"""
        if not hasattr(self, 'fullcredits_soup'):
            fullcredits_url = f"https://www.imdb.com/title/{imdb_id}/fullcredits"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
            response = requests.get(fullcredits_url, headers=headers)
            self.fullcredits_soup = BeautifulSoup(response.content, 'html.parser')

    def _fetch_episodes_page(self, imdb_id, season):
        if not hasattr(self, 'episode_soup'):
            episodes_url = f"https://www.imdb.com/title/{imdb_id}/episodes/?season={season}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(episodes_url, headers=headers)
            self.episodes_soup = BeautifulSoup(response.content, 'html.parser')

# --- season related methods ---

    def _extract_seasons_count(self):
        """
        Exctract number of season from the main site (self.soup)
        """
        season_option = self.soup.select_one('select[id="browse-episodes-season"]')
        aria_label = season_option.get('aria-label')
        return int(re.search(r'\d+', aria_label).group())

    def getSeasonCounts(self):
        return self.seasons_count

    def getEpisodeCounts(self, season):
        """
        Get the number of episodes for a given season
        """
        return len(self.movie['seasons'][season])

    def getEpisodes(self, season):
        """
        Get the episodes for a given season
        """
        return self.movie['seasons'][season]

    def getStoryline(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['storyline']
        return self.movie['base']['storyline']

    def getOriginalCountries(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['original_countries']
        return self.movie['base']['original_countries']

    def getOriginalLanguage(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['original_language']
        return self.movie['base']['original_language']

    def getOriginalTitle(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['original_title']
        return self.movie['base']['original_title']

    def getType(self):
        return self.movie['base']['type']

    def getYear(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['year']
        return self.movie['base']['year']

    def getTitles(self):
        return self.movie['base']['titles']

    def getLength(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['length']
        return self.movie['base']['length']

    def getRuntimeSec(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['runtime_sec']
        return self.movie['base']['runtime_sec']

    def getGenres(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['genres']
        return self.movie['base']['genres']

    def getStars(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['stars']
        return self.movie['base']['stars']

    def getActors(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['actors']
        return self.movie['base']['actors']

    def getWriters(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['writers']
        return self.movie['base']['writers']

    def getDirectors(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['directors']
        return self.movie['base']['directors']

    def getId(self, season_index=None, episode_index=None):
        if season_index is not None and episode_index is not None:
            return self.movie['seasons'][season_index][episode_index]['id']
        return self.movie['base']['id']

    def getSequence(self, season_index, episode_index):
        return self.movie['seasons'][season_index][episode_index]['sequence']

if __name__ == "__main__":

#    EXTRA_ISO_COUNTRY_CODE_LIST = ["hu-HU"]
#    CATEGORY = "movie"
#    PRIMARYMEDIATYPE = "video"
#    SOUNDS = ["hu", "en"]
#    SUBS = ["en"]
#    THEMES = []

#    IMDB_ID = "tt0163978"  # IMDB ID for individual movie - The beach
#    IMDB_ID = "tt0308671"  # IMDB ID for individual movie - Tycoon A new russion
    IMDB_ID = "tt0137523"  # IMDB ID for individual movie - Fight club
#    IMDB_ID = "tt0078350"  # IMDB ID for individual movie - The Swarm

#    IMDB_ID = "tt0098936"  # IMDB ID for series - Twin Peaks
#    IMDB_ID = "tt0487831"  # IMDB ID for series - The IT Crowd
#    IMDB_ID = "tt0108778"  # IMDB ID for series - Friends
#    IMDB_ID = "tt0106179"  # IMDB ID for series - X Files

#    cons_path = os.path.expanduser('~/tmp/homeflix/')
#    need_to_copy_to_destination_path = False
#    need_to_file = True

    imdb = FetchImdb(IMDB_ID)
    type = imdb.getType()

    if type == 'series':
        season_counts = imdb.getSeasonCounts()

        print(f"{imdb.getOriginalTitle()}")
        for season_index in range(0, season_counts):

            print(f"  Season {season_index+1}")
            episode_counts = len(imdb.getEpisodes(season_index))
            for episode_index in range(0, episode_counts):
                imdb.getOriginalTitle(season_index, episode_index)
                print(f"    episode:    {imdb.getSequence(season_index, episode_index)}")
                print(f"      title:    {imdb.getOriginalTitle(season_index, episode_index)}")
                print(f"      year:     {imdb.getYear(season_index, episode_index)}")
                print(f"      origin:   {imdb.getOriginalCountries(season_index, episode_index)}")
                print(f"      director: {imdb.getDirectors(season_index, episode_index)}")
                print(f"      writer:   {imdb.getWriters(season_index, episode_index)}")
                #print(f"      actors:   {imdb.getActors(season_index, episode_index)}")

    else:
        print(f"      title:     {imdb.getOriginalTitle()}")
        print(f"      storyline: {imdb.getStoryline()}")
        print(f"      year:      {imdb.getYear()}")
        print(f"      origin:    {imdb.getOriginalCountries()}")
        print(f"      director:  {imdb.getDirectors()}")
        print(f"      writer:    {imdb.getWriters()}")
        print(f"      actors:    {imdb.getActors()}")
        print(f"      genres:    {imdb.getGenres()}")




