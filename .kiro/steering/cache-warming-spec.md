# Cache Warming — Background Job After Rebuild Static DB

## Overview

After Rebuild Static DB completes and the GUI returns to normal, a background job starts that pre-populates the server-side file cache by running all cacheable queries. This way, the first user visit after a rebuild is instant instead of slow.

## Requirements

1. **Triggered by Rebuild Static DB** — after the DB rebuild finishes and the HTTP response is sent back to the browser, the background job starts automatically
2. **Runs in background** — does not block the GUI. The user can browse while the cache is being warmed
3. **Single instance** — if a new Rebuild Static DB is triggered while cache warming is running, stop the old job and start a new one
4. **Skip existing cache** — if a cache file already exists (e.g., user browsed a menu while warming is in progress), skip that query and move to the next
5. **Clear cache first** — remove all existing cache files before starting the warming process
6. **Per-user cache** — queries include user_id in the cache key because results contain user-specific data (tags, ratings, history). Different users get separate cache files. The warming job must run for each user (currently 2 users: admin/1234, default/1235)

## What Gets Cached

All entries in card_menu.yaml with `cacheable: true` in their data section. Two types:

### dynamic_hard_coded entries (~100 unique queries)
Direct queries with fixed parameters. Example:
- `/collect/highest/mixed?category=movie&genres=action&cacheable=true&lang=hu`
- `/collect/lowest?category=music_audio&level=band&decade=80s&cacheable=true&lang=hu`

### dynamic_queried entries (~8 unique, but expand to many queries)
Two-phase queries:
1. Pre-query returns a list (e.g., list of directors)
2. Query loop runs for each item in the list

Example (movie_by_director):
- Pre-query: `/collect/directors/by/movie/count?category=movie&minimum=2&limit=100&cacheable=true`
- Query loop: For each director → `/collect/highest/mixed?category=movie&directors={name}&cacheable=true&lang=hu`

### Entries to SKIP (not cacheable)
- Playlist entries (view_state: interrupted/last_watched/most_watched)
- Personal tag queries (/personal/tag/get)
- Search entries

Note: Some playlist tag pre-queries currently have `cacheable: true` incorrectly — these should be fixed (pre_query path is `/personal/tag/get`).

## Architecture

```
User clicks "Rebuild Static DB"
        ↓
Frontend sends POST /control/rebuild/db/static
        ↓
Backend: ep_control_rebuild_db_static.py
  1. Drop static tables
  2. Recreate DB (SqlDatabase.__init__)  ← this calls cache.clear()
  3. Send HTTP response back to browser  ← GUI returns to normal
  4. Start background thread: cache_warming_job()
        ↓
Background thread (runs independently):
  1. Read card_menu.yaml
  2. Find all cacheable entries
  3. For each entry:
     a. Build cache key from parameters
     b. Check if cache file exists → skip if yes
     c. Call the database method with cacheable=True
     d. Result is automatically cached by the method
  4. For dynamic_queried entries:
     a. Run pre-query (cached)
     b. For each result, run query_loop (cached)
  5. Repeat for each user (user_id=1234, user_id=1235)
```

## Implementation Details

### Background Thread Management
- Use Python `threading.Thread` with a stop flag
- Store reference to the running thread in `web_gadget` or `SqlDatabase`
- Before starting a new job, set the stop flag on the old thread and wait briefly
- The warming loop checks the stop flag between queries

### Language Handling
- Queries are language-dependent (lang parameter affects title translations)
- Need to warm cache for each user's preferred language
- Get user language from the User table

### Mapping card_menu.yaml paths to database methods
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

### Estimated Warming Time (Raspberry Pi)
- ~113 unique DHC queries × ~1-5s each = ~200-500s
- ~8 DQ pre-queries × ~5s each = ~40s
- DQ query loops (directors: ~50 queries, actors: ~50, ABC: ~25×3 = 75) × ~1.5s = ~260s
- Per user × 2 users = ~1000-1600s total
- **Estimated: 15-25 minutes on the Pi**

This is acceptable since it runs in the background and the user can browse normally.

## Observations

- The `cacheable: true` flag on playlist tag pre-queries (`/personal/tag/get`) is incorrect — those should NOT have cacheable. Need to fix in card_menu.yaml.
- The warming job needs Flask request context for `get_user_id_and_lang()` — may need to mock or bypass this since it runs outside an HTTP request.
- The `get_user_id_and_lang()` method reads from Flask session — in the background thread there's no session. Need to pass user_id and lang explicitly.

## Files to Modify

1. **`ep_control_rebuild_db_static.py`** — start background thread after rebuild
2. **`database.py`** or new module — cache warming logic (read card_menu, iterate entries, call methods)
3. **`card_menu.yaml`** — fix incorrect `cacheable: true` on playlist tag pre-queries

## Risks & Weaknesses

1. **Thread safety** — SQLite connection with `check_same_thread=False` and the existing Lock should handle concurrent access from the warming thread and normal request threads
2. **Memory** — running many queries in sequence shouldn't accumulate memory since results are written to disk and discarded
3. **Apache worker timeout** — the background thread is independent of the HTTP request, so Apache timeouts don't apply
4. **Stop flag race condition** — between checking the flag and starting a query, a new rebuild could be triggered. Acceptable — the query just runs and gets overwritten by the new warming job

### Independent Review Findings

**Critical:**
- **WSGI thread lifecycle**: Apache mod_wsgi can recycle processes, killing the warming thread. Low risk for us since Apache only restarts on Update SW (which triggers new rebuild). But worth noting.
- **SQLite contention**: Long warming queries hold the Lock, blocking user requests. Mitigation: add `time.sleep()` between queries to yield to user requests. Consider WAL mode (`PRAGMA journal_mode=WAL`) for concurrent reads.
- **Cache file write race (TOCTOU)**: Warming thread and user request could write same file simultaneously. Fix: write to temp file, then `os.replace()` for atomic rename.

**Important:**
- **Flask session coupling**: Database methods read user_id from Flask session. Background thread has no session. Must pass user_id/lang explicitly to database methods.
- **Stop flag**: Use `threading.Event` instead of bare boolean for proper thread visibility.
- **Error resilience**: One failed query should not abort the entire warming job. Log error and continue to next query.
- **I/O starvation**: Add small `time.sleep(0.1)` between iterations to yield I/O bandwidth to user requests on Pi's slow SD card.

## Progress Tracking

### TODO
- [x] Fix incorrect cacheable on playlist tag pre-queries in card_menu.yaml
- [x] Design the cache warming function (read card_menu, iterate, call methods)
- [x] Handle Flask session absence in background thread (pass user_id/lang explicitly)
- [x] Implement background thread with stop flag
- [x] Integrate into ep_control_rebuild_db_static.py
- [x] Test on localhost
- [x] Measure warming time
- [x] Fix parameter mismatch (lang not accepted by list methods) — added _call_method with inspect.signature
- [x] Add aligned progress logging with entry details
- [ ] Test concurrent browsing during warming
- [ ] Test stop-and-restart (trigger rebuild while warming is running)
