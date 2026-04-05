# Performance Optimizations — Implementation Reference

## Overview

HomeFlix had a significant performance problem: clicking on dynamic_hard_coded or dynamic_queried thumbnails (e.g., Movies > Movies in ABC) caused 30-40 seconds of spinner time on the Raspberry Pi. Two optimizations were implemented to address this.

## Optimization 1: ABC Pre-query filter_on Fix

### Problem
The ABC pre-query (`/collect/highest/mixed/abc`) was called without the `filter_on` parameter, defaulting to `None`. This caused the SQL query to start from ALL media-level cards (episodes, records — 1,636 for movies) with 18+ LEFT JOINs each, then walk UP the hierarchy recursively. Meanwhile, the per-letter query_loop that follows used `filter_on="-"` which starts directly from top-level cards (285 for movies) with no recursion.

This was an inconsistency — the pre-query collected first letters from lowest-level titles, while the per-letter queries searched by highest-level titles.

### Measured Impact
| | Without fix | With fix | Speedup |
|---|---|---|---|
| Dev machine | 4,500ms | 337ms | 13.5x |
| Raspberry Pi | 32,300ms | 2,400ms | 13.5x |

### Fix Applied
Added `filter_on: "-"` to the pre_query data section of all 5 ABC entries in `home/pi/.homeflix/card_menu.yaml`:
- `movie_by_title_abc` (category: movie)
- `music_by_band_abc` (category: music_video, level: band)
- `music_by_band_abc` (category: music_audio, level: band)
- `music_by_soundtrack_abc` (category: music_audio, level: soundtrack)
- `music_by_composer_abc` (category: music_audio, level: composer)

All other dynamic entries were reviewed and confirmed to be intentionally without `filter_on` — they need to filter at the lowest level (e.g., "find series containing a Sci-Fi episode").

### Understanding filter_on

The `filter_on` parameter controls at which hierarchy level filtering happens:

- `filter_on=None` or `'v'` (default): Filter at the **lowest level** (episodes, records). The recursive CTE starts from media-level cards, applies WHERE filters there, then walks UP to find parent containers. Use case: "find all series that contain a Sci-Fi episode", "search by record name but show the band".

- `filter_on='-'`: Filter at the **highest level** (franchises, series, bands). No recursive walk — filters applied directly on top-level cards. Use case: "Movies in ABC by franchise name", "search by band name".

Both modes show the appropriate level in results, but the difference is where filter criteria are applied. This design supports many combinations: search by record name but show band, search by band name but show records, etc.

## Optimization 2: Server-side Response Cache

### Problem
Even after the filter_on fix, each `/collect/*` query still takes 270ms-1900ms on the Pi. With 25+ sequential requests for an ABC page, the total is still ~37 seconds. The catalog data rarely changes — only when Rebuild Static DB runs.

### Solution
A server-side file cache that stores JSON query results on disk. When the same query is requested again, the cached file is returned in ~1-2ms instead of running the expensive SQL.

### Architecture

```
Client (browser) → HTTP request → Flask endpoint
                                        ↓
                                  database.py query method
                                        ↓
                                  ResponseCache.get(key)
                                   ↙          ↘
                              HIT              MISS
                               ↓                ↓
                          return cached     run SQL query
                          JSON file (~1ms)   (~300-4500ms)
                                                ↓
                                        ResponseCache.set(key, result)
                                            ↓
                                        return result
```

### Why Server-side (not Browser localStorage)

An earlier approach used browser localStorage. It worked but had a critical flaw: when Rebuild Static DB runs from one device (e.g., desktop), other devices (laptop, TV) still have stale cached data with no way to detect the change.

Server-side cache solves this — the server owns the cache, so Rebuild Static DB clears it in one place, affecting all clients immediately.

### Why File-based (not SQLite or In-memory)

- **In-memory dict**: Fast but lost on Apache restart. Not persistent.
- **SQLite cache table**: The whole point is to avoid SQLite. Adding more SQLite reads to speed up SQLite is counterproductive. SQLite uses a single writer lock — cache writes would block real queries.
- **File-based**: Fast reads (OS file cache keeps files in RAM), no SQL overhead, easy to clear, persistent across restarts.

### Implementation Details

#### Cache Module: `homeflix/cache/response_cache.py`

A standalone class with 4 methods:
- `make_key(**params)` — sorts parameters alphabetically, joins as `key=value&...`, returns MD5 hash. This becomes the filename.
- `get(cache_key)` — reads `/home/pi/.homeflix/cache/{hash}.json`, returns parsed JSON or None if file doesn't exist.
- `set(cache_key, data)` — writes JSON to cache file. Creates cache directory if needed. Silently handles write errors (QuotaExceeded, permissions, etc.).
- `clear()` — deletes the entire cache directory with `shutil.rmtree()`.

#### Cache Location
```
/home/pi/.homeflix/cache/
```
Same parent as `homeflix.db` and `config.yaml`. The `pi` user (Apache/wsgi process) has write permissions. Not in git repo. Not in `/tmp` — survives reboots.

#### Cache Key Format
The cache key is an MD5 hash of the sorted request parameters:
```
{method_name}&{param1}={value1}&{param2}={value2}&...
```
Example: `method=get_highest_level_cards&category=movie&filter_on=-&lang=en&title=A%&user_id=1234`
→ MD5 hash → `38371566fd2a4ae80c89c3bbfaee5d05.json`

The `user_id` is included in the cache key because query results contain user-specific data (tags, ratings, history). Different users get separate cache files.
#### Integration in database.py

Four methods are cached:
- `get_highest_level_cards()` — the main catalog query (Movies by Genre, etc.)
- `get_highest_level_abc()` — the ABC letter list query
- `get_lowest_level_cards()` — lowest-level media query (record lists, etc.)
- `get_next_level_cards()` — child cards query (episodes of a series, tracks of an album)
- `get_list_of_directors_by_movie_count()` — directors list pre-query
- `get_list_of_actors_by_role_count()` — actors list pre-query
- `get_list_of_directors()` — directors list (alphabetical)
- `get_list_of_actors()` — actors list (alphabetical)
- `get_list_of_voices()` — voices list
- `get_list_of_voices_by_role_count()` — voices by role count
- `get_list_of_performers()` — performers list
- `get_list_of_writers()` — writers list
- `get_list_of_tags()` — user tags list (includes user_id in cache key)

Each method follows the same pattern:
1. Build cache key from all parameters
2. Check `self.cache.get(cache_key)` — if hit, return immediately
3. If miss, run the SQL query as before
4. After SQL completes, call `self.cache.set(cache_key, records)` to store result
5. Return result

#### Cache Invalidation

`recreate_static_dbs()` in database.py calls `self.cache.clear()` before dropping and recreating tables. This is triggered by:
- **Rebuild Static DB** — user clicks in Server Settings menu
- **Update SW** — git pull + Apache reload, which triggers DB rebuild on restart

### The `cacheable` Flag

Not all queries should be cached. Playlists (Continue Playing, Last Watched, Most Watched) and Search results contain personal/dynamic data that changes on every user action. Caching them would serve stale results.

The `cacheable` flag in `card_menu.yaml` controls which queries use the cache:

- `cacheable: true` in the `data` section → query result is cached on disk
- No `cacheable` flag (default: false) → query always hits the database

The flag flows: `card_menu.yaml` → frontend reads it → sends as HTTP parameter → endpoint extracts it → passes to database method → method checks it before using cache.

#### What gets `cacheable: true`:
- All `dynamic_hard_coded` catalog entries (genres, themes, series, franchises, decades, etc.)
- All `dynamic_queried` catalog entries (directors, actors, ABC) — both pre_query and query_loop data sections

#### What does NOT get `cacheable`:
- Playlist entries with `view_state` (interrupted, last_watched, most_watched)
- Personal tag queries (`/personal/tag/get`)
- Search entries

### Measured Impact
| | First call (cache miss) | Second call (cache hit) |
|---|---|---|
| Per-letter query (dev) | 290ms | 2ms |
| ABC pre-query (dev) | 4,428ms | 1ms |

On the Raspberry Pi, the improvement is proportionally the same — the first call is slow (SQL runs), but every subsequent call is near-instant.

### What is NOT Cached
- `/personal/*` endpoints — history, ratings, tags change on every user action
- `/auth/*` endpoints — login/logout
- `/stream/*` endpoints — media file streaming
- `/control/*` endpoints — server control operations
- `/translate/*` endpoints — translations are small and loaded once at page load

### Cache File Statistics
With a typical media collection (~7500 cards), the cache accumulates ~300 unique query results totaling ~15MB on disk. Negligible for any storage device.

### Apache WSGI Timeout
The `WSGIDaemonProcess` in `etc/apache2/site-enabled/homeflix.conf` needs `socket-timeout=120` (or higher) to prevent 504 Gateway Timeout errors on the first uncached request. The default is 60 seconds, which is too short for the expensive recursive SQL queries on the Raspberry Pi. After the cache is populated, this is no longer an issue since cached responses return in milliseconds.

## Optimization 3: Cache Warming (Background Job)

### Problem
Even with the file cache, the first visit to each menu after a Rebuild Static DB is slow — the SQL query runs and the cache file is created. With ~113 unique cacheable entries, the first user to browse each menu pays the full SQL cost.

### Solution
After Rebuild Static DB completes and the GUI returns to normal, a background thread automatically pre-populates the cache by running all cacheable queries. This way, every menu is instant from the first visit.

### How It Works

1. User clicks "Rebuild Static DB" in Server Settings menu
2. Frontend sends `POST /control/rebuild/db/static`
3. Backend rebuilds the database (drops tables, recreates, scans filesystem)
4. Cache is cleared (`self.cache.clear()`)
5. HTTP response is sent back to browser — GUI returns to normal
6. A background thread starts: `cache_warming.start_warming(db, card_menu_path)`
7. The thread reads `card_menu.yaml`, finds all entries with `cacheable: true`
8. For each entry, it calls the corresponding database method with `cacheable=True`
9. The method runs the SQL, stores the result in cache, returns
10. The thread repeats for each user (different users get different cache files)
11. If a cache file already exists (user browsed during warming), it's skipped

### Implementation: `homeflix/cache/cache_warming.py`

#### Key Functions

- `start_warming(db, card_menu_path)` — starts the background thread. Stops any existing warming job first (single instance).
- `_warming_job(db, card_menu_path, stop_event)` — the main loop. Reads card_menu, finds cacheable entries, iterates through users and entries.
- `_warm_entries(db, entries, lang, stop_event)` — runs all cacheable queries for one user. Prints progress to Apache error.log.
- `_warm_dhc(db, entry, lang)` — warms a single `dynamic_hard_coded` entry.
- `_warm_dq(db, entry, lang, stop_event)` — warms a `dynamic_queried` entry (pre-query + query loop for each result).
- `_call_method(method, params)` — calls a database method, filtering out parameters it doesn't accept (using `inspect.signature`). This is needed because some methods accept `lang` and some don't.
- `_find_cacheable_entries(card_menu)` — walks the card_menu structure and collects all entries with `cacheable: true`.
- `_get_users(db)` — queries the User table to get all users (id, language, name).

#### Path-to-Method Mapping

The warming job maps card_menu.yaml request paths to database method names:

| card_menu path | Database method |
|---|---|
| `/collect/highest/mixed` | `get_highest_level_cards()` |
| `/collect/highest/mixed/abc` | `get_highest_level_abc()` |
| `/collect/lowest` | `get_lowest_level_cards()` |
| `/collect/directors/by/movie/count` | `get_list_of_directors_by_movie_count()` |
| `/collect/actors/by/role/count` | `get_list_of_actors_by_role_count()` |
| `/collect/directors` | `get_list_of_directors()` |
| `/collect/actors` | `get_list_of_actors()` |
| `/collect/voices` | `get_list_of_voices()` |
| `/collect/voices/by/role/count` | `get_list_of_voices_by_role_count()` |
| `/collect/performers` | `get_list_of_performers()` |
| `/collect/writers` | `get_list_of_writers()` |
| `/collect/tags` | `get_list_of_tags()` |

#### User Context for Background Thread

The database methods use `get_user_id_and_lang()` which reads from Flask session. The background thread has no session. To solve this:

- The warming job sets `db._warming_user_id` and `db._warming_lang` before calling methods
- `get_user_id_and_lang()` checks these attributes first, before falling back to session
- After each user's warming completes, the attributes are reset to `None`

#### Parameter Filtering with `_call_method`

Not all database methods accept the same parameters. For example, `get_highest_level_cards` accepts `lang`, but `get_list_of_directors_by_movie_count` does not. The warming job builds a parameter dict that includes `lang` and `cacheable` for all calls.

`_call_method` uses `inspect.signature()` to check which parameters the method actually accepts, and filters out any extras before calling. Without this, methods that don't accept `lang` would raise `TypeError` and be silently skipped.

#### Thread Management

- Uses `threading.Thread` with `daemon=True` (dies when main process exits)
- Uses `threading.Event` as stop flag — checked between queries
- Before starting a new warming job, the old one is stopped (`_stop_event.set()`) and joined with a 5-second timeout
- The warming loop calls `time.sleep(0.1)` between queries to yield I/O bandwidth to user requests

#### Atomic File Writes

Cache files are written atomically: write to a `.tmp` file first, then `os.replace()` for atomic rename. This prevents corrupted cache files if the warming thread and a user request write the same key simultaneously.

#### Progress Logging

The warming job prints progress to Apache error.log (via `print(..., flush=True)`):
```
Cache warming: started
Cache warming: found 113 cacheable entries
Cache warming: warming for 2 users
Cache warming: user 'admin' (id=1234, lang=hu)
Cache warming: 1/113 - movie_by_genre
Cache warming: 2/113 - movie_by_genre
...
Cache warming: 113/113 - personal
Cache warming: user 'default' (id=1235, lang=en)
Cache warming: 1/113 - movie_by_genre
...
Cache warming: completed
```

Monitor with: `tail -F /var/www/homeflix/logs/error.log | grep warming`

### Warming Statistics
- **113 unique cacheable entries** in card_menu.yaml
- **~500 cache files** generated (113 entries × 2 users + dynamic_queried expansions like per-director and per-letter queries)
- **~15MB** total cache size
- **~4 minutes** on dev machine, **~15-20 minutes** estimated on Raspberry Pi
- Runs in background — user can browse normally during warming

## Files Modified/Created

### New Files
- `homeflix/cache/__init__.py` — empty package init
- `homeflix/cache/response_cache.py` — file-based cache module
- `homeflix/cache/cache_warming.py` — background cache warming job

### Modified Files
- `homeflix/card/database.py` — cache import, initialization, cache check/store in 13 query methods, cache clear in `recreate_static_dbs()`, `_warming_user_id`/`_warming_lang` override in `get_user_id_and_lang()`
- `homeflix/restserver/endpoints/ep_control_rebuild_db_static.py` — starts warming thread after rebuild
- `homeflix/restserver/endpoints/ep_collect_*.py` (12 files) — extract `cacheable` from payload and pass to database methods
- `home/pi/.homeflix/card_menu.yaml` — `filter_on: "-"` on ABC pre-queries, `cacheable: true` on catalog entries, header comment explaining cacheable flag
- `etc/apache2/site-enabled/homeflix.conf` — `socket-timeout=120` on WSGIDaemonProcess
