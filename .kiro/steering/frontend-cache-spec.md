# Frontend Response Cache — Specification & Implementation Plan

## Problem Statement
When a user clicks on a dynamic_hard_coded or dynamic_queried thumbnail (e.g., Movies > Movies by Genre > Action), the frontend sends expensive SQL queries to the backend. These queries take 270ms-1900ms each on the Pi, and there can be 25+ sequential requests. The data rarely changes (only when the static DB is rebuilt via Apache restart/update). Caching the responses would make the second visit instant.

## Design Evolution

### Phase 1 (implemented, to be reverted): Browser localStorage
Initially implemented caching in browser localStorage. Works but has a critical flaw: when Rebuild Static DB runs from one device (e.g., desktop), other devices (laptop, TV) still have stale cached data with no way to detect the change.

### Phase 2 (current plan): Server-side file cache
Cache JSON responses as files on the server. All clients benefit from the same cache. Server controls invalidation — Rebuild Static DB clears the cache in one place, affecting all clients.

## Specification

### What to cache
- The **JSON responses** from expensive `/collect/*` endpoint queries
- Cache is **user-independent** — the catalog data is the same for all users (personal data like history/ratings is NOT cached)
- Cache key: derived from the request parameters (endpoint path + sorted query parameters)
- Cache value: the JSON response string, stored as a file

**Why JSON responses and not built DOM/HTML:**
- DOM elements contain JavaScript closures (click handlers creating SubLevelRestGenerator, playlist references) that cannot be serialized
- The main bottleneck is network + SQL (1.5s per request × 25 = 37s on Pi), not JavaScript DOM construction
- DOM construction from cached JSON is near-instant (milliseconds)
- JSON is cleanly serializable and simple to implement

### Technology choice: File-based server cache
Options considered:
1. **In-memory Python dict** — fast but lost on Apache restart. Not persistent.
2. **File-based cache (JSON files on disk)** — persistent, fast (OS file cache), easy to clear. **CHOSEN.**
3. **SQLite cache table** — adds more load to the already-slow SQLite. Defeats the purpose.

**Why file-based:**
- Very fast reads — OS file cache keeps frequently accessed files in RAM
- No SQL overhead — just file read, no query parsing, no locking
- Easy to clear — delete the cache directory on Rebuild Static DB
- Persistent across Apache restarts
- All clients share the same cache — no stale data across devices

### Cache location
```
/home/pi/.homeflix/cache/
```
- Same parent as `homeflix.db` and `config.yaml`
- `pi` user (Apache/wsgi process) has write permissions
- Not in git repo
- Not in `/tmp` — survives reboots

### Cache key → filename mapping
Hash the request parameters to create a unique filename:
```
/home/pi/.homeflix/cache/{md5_of_request_signature}.json
```
The request signature is: `{endpoint_path}:{sorted_query_params}`
Example: `/collect/highest/mixed:category=movie&filter_on=-&lang=en&title=A%` → `a1b2c3d4e5f6.json`

### When to use cache
- In the database query methods (`get_highest_level_cards`, `get_highest_level_abc`, etc.)
- Before running the SQL query, check if a cache file exists
- If cached: read and return the file contents, skip SQL entirely
- If not cached: run SQL, save result to cache file, return result

### When to invalidate cache
- **Rebuild Static DB** (`recreate_static_dbs()`) — delete all files in the cache directory
- **Update SW** — also triggers Apache reload which rebuilds static DB
- Cache directory is created on first write if it doesn't exist

### What to cache / not cache
- **Cache**: `/collect/highest/*`, `/collect/lowest/*`, `/collect/next/*`, `/collect/highest/mixed/abc`, `/collect/directors/*`, `/collect/actors/*`, `/collect/writers/*`, `/collect/voices/*`, `/collect/performers/*`, `/collect/tags/*`
- **Do NOT cache**: `/personal/*`, `/auth/*`, `/stream/*`, `/control/*`, `/translate/*` (translations are small and loaded once at page load)

### Architecture

```
Client (browser) → HTTP request → Flask endpoint (ep_collect_*.py)
                                        ↓
                                  database.py query method
                                        ↓
                                  ResponseCache.get(key)
                                   ↙          ↘
                              HIT              MISS
                               ↓                ↓
                          return cached     run SQL query
                          JSON file          ↓
                                        ResponseCache.set(key, result)
                                            ↓
                                        return result
```

## Implementation Plan

### New file: `homeflix/cache/response_cache.py`
A standalone cache module with:
- `get(cache_key)` — read cache file, return parsed JSON or None
- `set(cache_key, data)` — write JSON to cache file
- `clear()` — delete all files in cache directory
- `make_key(**params)` — create cache key from request parameters

### Files to modify

1. **`homeflix/cache/__init__.py`** — new empty init file
2. **`homeflix/cache/response_cache.py`** — new cache module
3. **`homeflix/card/database.py`** — wrap query methods with cache check/store
4. **`homeflix/card/database.py`** — call `cache.clear()` in `recreate_static_dbs()`

### Files NOT modified
- No frontend changes needed (revert the localStorage changes from Phase 1)
- No endpoint changes needed — cache is transparent, handled inside database.py

## Step-by-step Implementation

### Step 1: Revert frontend localStorage changes
- Revert `generators.js` to remove the `ResponseCache` object and all localStorage logic
- The frontend goes back to making normal HTTP requests every time

### Step 2: Create `homeflix/cache/__init__.py`
- Empty file

### Step 3: Create `homeflix/cache/response_cache.py`
```python
class ResponseCache:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
    
    def make_key(self, **params) -> str:
        # Sort params, create stable string, MD5 hash it
    
    def get(self, cache_key) -> dict or None:
        # Read file, parse JSON, return or None
    
    def set(self, cache_key, data):
        # Write JSON to file, create dir if needed
    
    def clear(self):
        # Delete all .json files in cache_dir
```

### Step 4: Integrate into database.py
- Import ResponseCache
- Initialize in `SqlDatabase.__init__()` with cache_dir from config
- In each cacheable query method: check cache before SQL, store after SQL
- In `recreate_static_dbs()`: call `self.cache.clear()`

### Step 5: Test
- First request: slow (SQL runs, cache file created)
- Second request: fast (cache file served)
- Rebuild Static DB: cache cleared
- Third request: slow again (cache rebuilt)
- Test from two different browsers — both should benefit from same cache

## Risks & Weaknesses

1. **Disk space**: Cache files accumulate. With ~300 unique queries × ~50KB average = ~15MB. Negligible.
2. **Stale cache on manual DB edit**: If someone manually edits the SQLite DB without going through Rebuild Static DB, cache would be stale. Mitigation: document that Rebuild Static DB must be used after manual changes.
3. **Concurrent writes**: Two simultaneous requests for the same uncached query could both write the same cache file. Not a problem — they'd write identical content, and file writes are atomic on ext4 for small files.
4. **Cache key collisions**: MD5 hash collisions are theoretically possible but practically impossible for this use case.

## Progress Tracking

### TODO
- [x] Revert frontend localStorage changes in generators.js
- [x] Create homeflix/cache/__init__.py
- [x] Create homeflix/cache/response_cache.py
- [x] Integrate cache into database.py query methods
- [x] Add cache.clear() to recreate_static_dbs()
- [x] Test on localhost (first visit slow, second fast, rebuild clears)
- [x] Add cacheable flag to card_menu.yaml and endpoints
- [x] Test cacheable vs non-cacheable (playlists always fresh, catalog cached)
- [ ] Review for weaknesses
