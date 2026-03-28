import requests
import json
import os
import re
import yaml
import urllib.parse
import shutil

# ============================================================
# INPUT PARAMETERS
# ============================================================
CARD_FILE_NAME = 'card.yaml'
EXTRA_ISO_COUNTRY_CODE_LIST = ["hu-HU"]
CATEGORY = "movie"
PRIMARYMEDIATYPE = "video"
SOUNDS = ["hu", "en"]
SUBS = ["en"]
THEMES = ["corruption", "evil"]
GENRE = ["satire", "drama"]
IMDB_ID = "tt2452242"

CONSTRUCTION_PATH = os.path.expanduser('~/tmp/homeflix/')

# ============================================================

GRAPHQL_URL = "https://graphql.imdb.com/"
GRAPHQL_HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
}

AKA_BASE_URL = "https://caching.graphql.imdb.com/"
AKA_GRAPHQL_HASH = "48d4f7bfa73230fb550147bd4704d8050080e65fe2ad576da6276cac2330e446"

country_language = {
    'eu': ['en'], 'hu': ['hu'], 'us': ['en'], 'gb': ['en'],
    'de': ['de'], 'fr': ['fr'], 'es': ['es'], 'it': ['it'],
    'ru': ['ru'], 'pl': ['pl'], 'no': ['no'], 'dk': ['dk'],
    'kr': ['ko'], 'hr': ['hr'], 'cn': ['zh'], 'nl': ['nl'],
    'fi': ['fi'], 'ca': ['en', 'fr'], 'ch': ['de', 'fr', 'it'],
    'be': ['nl', 'fr', 'de'], 'mx': ['es'], 'se': ['sv'],
    'at': ['de'], 'au': ['en'], 'nz': ['en'], 'cz': ['cs'],
    'ar': ['es'], 'jp': ['ja'], 'ie': ['en', 'ga'], 'ro': ['ro'],
    'br': ['pt']
}

genre_map = {
    "sci-fi": "scifi",
    "science fiction": "scifi",
    "film-noir": "film_noir",
}

# ============================================================
# YAML Dumper
# ============================================================
class LiteralStr(str):
    pass

class QuotedStr(str):
    pass

def literal_str_representer(dumper, data):
    if '\n' in data or len(data) > 80:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style=None if data else '')

def quoted_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
    def represent_int_as_str(self, data):
        """Represent strings that look like integers without quotes."""
        return self.represent_scalar('tag:yaml.org,2002:str', data)

MyDumper.add_representer(LiteralStr, literal_str_representer)
MyDumper.add_representer(QuotedStr, quoted_str_representer)

YAML_SPECIAL_CHARS = ':\'\"#[]{}|>&*!%@`'
YAML_SPECIAL_RE = re.compile('[' + re.escape(YAML_SPECIAL_CHARS) + ']')

def sanitize_role(role):
    """Replace YAML-problematic characters in actor roles with space."""
    return YAML_SPECIAL_RE.sub(' ', role).strip()

def safe_title(title):
    """Wrap title in QuotedStr if it contains YAML-special characters."""
    if YAML_SPECIAL_RE.search(title):
        return QuotedStr(title)
    return title

# ============================================================
# Helper functions
# ============================================================
def graphql_query(query):
    r = requests.post(GRAPHQL_URL, json={"query": query}, headers=GRAPHQL_HEADERS, timeout=30)
    return r.json()

def load_dictionary():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dictionary_path = os.path.join(current_dir, '..', 'homeflix', 'translator', 'dictionary.yaml')
    with open(dictionary_path, 'r') as file:
        return yaml.safe_load(file)

def translate_genre(genre_text, existing_genres):
    g = genre_text.lower().replace("-", "_").replace(" ", "_")
    g = genre_map.get(genre_text.lower(), g)
    return g if g in existing_genres else None

def seconds_to_hh_mm_ss(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def sanitize_title(title):
    sanitized = re.sub(r'[\'\":,!?\^%&#]', '', title)
    sanitized = sanitized.replace(' ', '.')
    return sanitized

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def format_number(num):
    return f"{int(num):02d}"

def write_card(path, data):
    # Convert storylines to block scalar format
    if 'storylines' in data:
        for lang in data['storylines']:
            data['storylines'][lang] = LiteralStr(data['storylines'][lang])
    # Write YAML
    with open(path, 'w') as f:
        content = yaml.dump(data, allow_unicode=True, default_flow_style=False, Dumper=MyDumper, sort_keys=False, width=500)
        # Remove quotes from date values like '2005' -> 2005
        content = re.sub(r"^(date: )'(\d{4})'$", r'\1\2', content, flags=re.MULTILINE)
        # Fix storyline block scalars: |- to | and empty '' to |
        content = re.sub(r": \|-\n", ": |\n", content)
        content = re.sub(r"^(\s+\w+): ''\s*$", r"\1: |", content, flags=re.MULTILINE)
        f.write(content)

def fetch_aka_titles(imdb_id, dictionary):
    variables = {"const": imdb_id, "first": 100, "locale": "en-US", "originalTitleText": True}
    extensions = {"persistedQuery": {"sha256Hash": AKA_GRAPHQL_HASH, "version": 1}}
    params = {
        'operationName': 'TitleAkasPaginated',
        'variables': json.dumps(variables, separators=(',', ':')),
        'extensions': json.dumps(extensions, separators=(',', ':'))
    }
    url = f"{AKA_BASE_URL}?{urllib.parse.urlencode(params)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': f'https://www.imdb.com/title/{imdb_id}/releaseinfo'
    }
    titles = {}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        edges = data.get('data', {}).get('title', {}).get('akas', {}).get('edges', [])
        for edge in edges:
            node = edge['node']
            title = node['displayableProperty']['value']['plainText']
            lang = node.get('language')
            if lang:
                lang_code = lang['id']
                if lang_code in dictionary.get('language', {}).get('short', {}):
                    titles[lang_code] = title
            elif node.get('country'):
                cc = node['country']['id'].lower()
                if cc in country_language:
                    for lc in country_language[cc]:
                        titles[lc] = title
    except Exception:
        pass
    return titles

def parse_credits(principal_credits, full_credits=None):
    """Parse principalCredits and full credits into stars, actors, writers, directors."""
    stars = []
    actors = {}
    writers = []
    directors = []

    for group in (principal_credits or []):
        cat = group['category']['text']
        for credit in group['credits']:
            name = credit['name']['nameText']['text']
            chars = credit.get('characters', [])

            if cat == 'Stars':
                stars.append(name)
                if chars:
                    actors[name] = sanitize_role(chars[0]['name'])
            elif cat in ('Cast', 'Actors'):
                if chars:
                    actors[name] = sanitize_role(chars[0]['name'])
            elif cat in ('Writers', 'Creators'):
                if name not in writers:
                    writers.append(name)
            elif cat in ('Director', 'Directors'):
                if name not in directors:
                    directors.append(name)

    # Merge full credits (from credits(first:50) query) for more actors
    for edge in (full_credits or []):
        node = edge['node']
        name = node['name']['nameText']['text']
        cat = node['category']['text']
        chars = node.get('characters', [])
        if cat in ('Actor', 'Actress') and name not in actors and chars:
            actors[name] = sanitize_role(chars[0]['name'])
        elif cat in ('Writer',) and name not in writers:
            writers.append(name)
        elif cat in ('Director',) and name not in directors:
            directors.append(name)

    return stars, actors, writers, directors

def extract_genres(title_genres, existing_genres):
    genres = []
    if title_genres:
        for g in title_genres['genres']:
            translated = translate_genre(g['genre']['text'], existing_genres)
            if translated and translated not in genres:
                genres.append(translated)
    return genres

def extract_countries(countries_of_origin):
    if countries_of_origin and countries_of_origin.get('countries'):
        return [c['id'].lower() for c in countries_of_origin['countries']]
    return []

def refresh_progress_bar(count, index, text=None, value=None):
    terminal_width = shutil.get_terminal_size().columns
    progress_width = terminal_width - 30
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

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":

    dictionary = load_dictionary()
    existing_genres = list(dictionary['genre']['movie'].keys())

    print(f"Fetching data for {IMDB_ID}...")

    result = graphql_query(f'''
query {{
  title(id: "{IMDB_ID}") {{
    titleText {{ text }}
    originalTitleText {{ text }}
    releaseYear {{ year }}
    titleType {{ text }}
    runtime {{ seconds }}
    plot {{ plotText {{ plainText }} }}
    titleGenres {{ genres {{ genre {{ text }} }} }}
    countriesOfOrigin {{ countries {{ id }} }}
    principalCredits {{
      category {{ text }}
      credits(limit: 30) {{
        name {{ id nameText {{ text }} }}
        attributes {{ text }}
        ... on Cast {{
          characters {{ name }}
        }}
      }}
    }}
    credits(first: 50) {{
      edges {{
        node {{
          name {{ nameText {{ text }} }}
          category {{ text }}
          ... on Cast {{ characters {{ name }} }}
        }}
      }}
    }}
    episodes {{
      seasons {{ number }}
      episodes(first: 500) {{
        edges {{
          node {{
            id
            titleText {{ text }}
            originalTitleText {{ text }}
            releaseYear {{ year }}
            runtime {{ seconds }}
            plot {{ plotText {{ plainText }} }}
            titleGenres {{ genres {{ genre {{ text }} }} }}
            countriesOfOrigin {{ countries {{ id }} }}
            series {{ displayableEpisodeNumber {{ displayableSeason {{ text }} episodeNumber {{ text }} }} }}
            principalCredits {{
              category {{ text }}
              credits(limit: 30) {{
                name {{ id nameText {{ text }} }}
                attributes {{ text }}
                ... on Cast {{
                  characters {{ name }}
                }}
              }}
            }}
            credits(first: 50) {{
              edges {{
                node {{
                  name {{ nameText {{ text }} }}
                  category {{ text }}
                  ... on Cast {{ characters {{ name }} }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}''')

    title = result['data']['title']
    type_text = title['titleType']['text'] if title.get('titleType') else ''
    is_series = 'Series' in type_text

    # Base info
    original_title = (title.get('originalTitleText') or title.get('titleText', {})).get('text', '')
    year = str(title['releaseYear']['year']) if title.get('releaseYear') else ''
    storyline = title['plot']['plotText']['plainText'] if title.get('plot') and title['plot'].get('plotText') else ''
    imdb_genres = extract_genres(title.get('titleGenres'), existing_genres)
    origins = extract_countries(title.get('countriesOfOrigin'))
    stars, actors, writers, directors = parse_credits(title.get('principalCredits'), (title.get('credits') or {}).get('edges'))

    # Merge GENRE input with imdb genres (input takes priority)
    all_genres = list(GENRE)
    for g in imdb_genres:
        if g not in all_genres:
            all_genres.append(g)

    # Series folder name
    sanitized_title = f"{sanitize_title(original_title)}-{year}"
    series_folder = os.path.join(CONSTRUCTION_PATH, sanitized_title)

    if is_series:
        # ========================================
        # SERIES
        # ========================================
        print(f"Generating series: {original_title} ({year})")

        # Create series folder
        create_folder(series_folder)
        create_folder(os.path.join(series_folder, 'screenshots'))
        create_folder(os.path.join(series_folder, 'thumbnails'))

        series_data = {
            "category": CATEGORY,
            "mediatypes": [],
            "level": "series",
            "title": {
                "onthumbnail": True,
                "showsequence": "part",
                "orig": "en",
                "titles": {
                    "en": safe_title(original_title)
                }
            },
            "storylines": {
                "en": storyline,
                "hu": ""
            },
            "date": year,
            "genres": all_genres,
            "origins": origins,
            "id": {"name": "imdb", "value": IMDB_ID}
        }

        write_card(os.path.join(series_folder, CARD_FILE_NAME), series_data)

        # Parse episodes grouped by season
        episodes_data = title.get('episodes', {})
        season_numbers = sorted(s['number'] for s in episodes_data.get('seasons', []))
        episodes_by_season = {}
        for edge in episodes_data.get('episodes', {}).get('edges', []):
            node = edge['node']
            ep_info = node['series']['displayableEpisodeNumber']
            sn = int(ep_info['displayableSeason']['text'])
            en = int(ep_info['episodeNumber']['text'])
            if sn not in episodes_by_season:
                episodes_by_season[sn] = []
            episodes_by_season[sn].append((en, node))

        total_episodes = sum(len(eps) for eps in episodes_by_season.values())
        episode_counter = 0

        for season_idx, season_num in enumerate(season_numbers):
            # Create season folder
            formatted_season = f"S{format_number(season_num)}"
            season_folder = os.path.join(series_folder, formatted_season)
            create_folder(season_folder)
            create_folder(os.path.join(season_folder, 'screenshots'))
            create_folder(os.path.join(season_folder, 'thumbnails'))

            season_data = {
                "category": CATEGORY,
                "mediatypes": [],
                "level": "series",
                "sequence": season_num,
                "title": {
                    "onthumbnail": True,
                    "showsequence": "part",
                    "orig": "en",
                    "titles": {
                        "en": f"Season {season_num}"
                    }
                }
            }

            write_card(os.path.join(season_folder, CARD_FILE_NAME), season_data)

            # Episodes
            episodes = episodes_by_season.get(season_num, [])
            episodes.sort(key=lambda x: x[0])

            for ep_num, node in episodes:
                episode_counter += 1
                refresh_progress_bar(total_episodes, episode_counter, text='Season', value=season_num)

                ep_folder = os.path.join(season_folder, f"E{format_number(ep_num)}")
                create_folder(ep_folder)
                create_folder(os.path.join(ep_folder, 'screenshots'))
                create_folder(os.path.join(ep_folder, 'thumbnails'))
                create_folder(os.path.join(ep_folder, 'media'))

                ep_title = (node.get('originalTitleText') or node.get('titleText', {})).get('text', '')
                ep_year = str(node['releaseYear']['year']) if node.get('releaseYear') else year
                ep_storyline = node['plot']['plotText']['plainText'] if node.get('plot') and node['plot'].get('plotText') else ''
                ep_genres = extract_genres(node.get('titleGenres'), existing_genres)
                ep_origins = extract_countries(node.get('countriesOfOrigin'))
                ep_stars, ep_actors, ep_writers, ep_directors = parse_credits(node.get('principalCredits'), (node.get('credits') or {}).get('edges'))
                ep_imdb_id = node['id']

                # Merge genres
                ep_all_genres = list(GENRE)
                for g in ep_genres:
                    if g not in ep_all_genres:
                        ep_all_genres.append(g)

                # Runtime
                rt = node.get('runtime')
                if rt and rt.get('seconds'):
                    secs = rt['seconds']
                    ep_length = seconds_to_hh_mm_ss(secs)
                    netstart_sec = 90
                    netstop_sec = (secs - 90) if secs > 90 else 90
                    ep_netstart = seconds_to_hh_mm_ss(netstart_sec)
                    ep_netstop = seconds_to_hh_mm_ss(netstop_sec)
                else:
                    ep_length = None
                    ep_netstart = None
                    ep_netstop = None

                # Stars: first 3 only (names without roles)
                ep_stars_top3 = ep_stars[:3]

                episode_data = {
                    "category": CATEGORY,
                    "primarymediatype": PRIMARYMEDIATYPE,
                    "sequence": ep_num,
                    "title": {
                        "onthumbnail": True,
                        "showsequence": "part",
                        "orig": "en",
                        "titles": {
                            "en": safe_title(ep_title)
                        }
                    },
                    "storylines": {
                        "en": ep_storyline,
                        "hu": ""
                    },
                    "date": ep_year,
                    "length": ep_length,
                    "netstart": ep_netstart,
                    "netstop": ep_netstop,
                    "directors": ep_directors,
                    "writers": ep_writers,
                    "stars": ep_stars_top3,
                    "actors": ep_actors,
                    "sounds": SOUNDS,
                    "subs": SUBS,
                    "genres": ep_all_genres,
                    "themes": THEMES,
                    "origins": ep_origins if ep_origins else origins,
                    "id": {"name": "imdb", "value": ep_imdb_id}
                }

                write_card(os.path.join(ep_folder, CARD_FILE_NAME), episode_data)

        print()
        print(f"Done! Output: {series_folder}")

    else:
        # ========================================
        # MOVIE
        # ========================================
        print(f"Generating movie: {original_title} ({year})")

        create_folder(series_folder)
        create_folder(os.path.join(series_folder, 'screenshots'))
        create_folder(os.path.join(series_folder, 'thumbnails'))
        create_folder(os.path.join(series_folder, 'media'))

        rt = title.get('runtime')
        if rt and rt.get('seconds'):
            secs = rt['seconds']
            length = seconds_to_hh_mm_ss(secs)
            netstart = seconds_to_hh_mm_ss(90)
            netstop = seconds_to_hh_mm_ss(secs - 90 if secs > 90 else 90)
        else:
            length = None
            netstart = None
            netstop = None

        stars_top3 = stars[:3]

        movie_data = {
            "category": CATEGORY,
            "primarymediatype": PRIMARYMEDIATYPE,
            "title": {
                "onthumbnail": True,
                "showsequence": "part",
                "orig": "en",
                "titles": {
                    "en": safe_title(original_title)
                }
            },
            "storylines": {
                "en": storyline,
                "hu": ""
            },
            "date": year,
            "length": length,
            "netstart": netstart,
            "netstop": netstop,
            "directors": directors,
            "writers": writers,
            "stars": stars_top3,
            "actors": actors,
            "sounds": SOUNDS,
            "subs": SUBS,
            "genres": all_genres,
            "themes": THEMES,
            "origins": origins,
            "id": {"name": "imdb", "value": IMDB_ID}
        }

        write_card(os.path.join(series_folder, CARD_FILE_NAME), movie_data)
        print(f"Done! Output: {series_folder}")
