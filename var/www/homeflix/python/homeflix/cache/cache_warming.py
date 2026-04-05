"""
Cache warming — background job that pre-populates the server-side file cache
after Rebuild Static DB completes.

Reads card_menu.yaml, finds all entries with cacheable: true, and calls the
corresponding database methods to generate cache files. Runs in a background
thread so the GUI returns immediately after rebuild.

The warming job:
- Clears existing cache before starting
- Skips queries whose cache file already exists (e.g., user browsed during warming)
- Runs for each user (different users get different cache files)
- Can be stopped and restarted (threading.Event stop flag)
- Yields between queries (time.sleep) to not starve user requests

See .kiro/steering/cache-warming-spec.md for full specification.
"""

import inspect
import logging
import time
import threading
import yaml
import os

# Path mapping from card_menu.yaml request paths to database method names
PATH_TO_METHOD = {
    '/collect/highest/mixed': 'get_highest_level_cards',
    '/collect/highest/mixed/abc': 'get_highest_level_abc',
    '/collect/lowest': 'get_lowest_level_cards',
    '/collect/directors/by/movie/count': 'get_list_of_directors_by_movie_count',
    '/collect/actors/by/role/count': 'get_list_of_actors_by_role_count',
    '/collect/directors': 'get_list_of_directors',
    '/collect/actors': 'get_list_of_actors',
    '/collect/voices': 'get_list_of_voices',
    '/collect/voices/by/role/count': 'get_list_of_voices_by_role_count',
    '/collect/performers': 'get_list_of_performers',
    '/collect/writers': 'get_list_of_writers',
    '/collect/tags': 'get_list_of_tags',
}

# Current warming thread reference and stop event
_warming_thread = None
_stop_event = threading.Event()


def start_warming(db, card_menu_path):
    """
    Start cache warming in a background thread.
    Stops any existing warming job first.

    Args:
        db: SqlDatabase instance
        card_menu_path: Path to card_menu.yaml
    """
    global _warming_thread, _stop_event

    # Stop existing job if running
    if _warming_thread and _warming_thread.is_alive():
        logging.debug("Stopping existing cache warming job...")
        _stop_event.set()
        _warming_thread.join(timeout=5)

    _stop_event = threading.Event()
    _warming_thread = threading.Thread(
        target=_warming_job,
        args=(db, card_menu_path, _stop_event),
        daemon=True
    )
    _warming_thread.start()
    logging.debug("Cache warming job started in background")


def _warming_job(db, card_menu_path, stop_event):
    """
    Background job that iterates through cacheable entries and pre-populates cache.
    """
    try:
        print("Cache warming: started", flush=True)
        logging.debug("Cache warming: loading card_menu.yaml...")
        with open(card_menu_path, 'r') as f:
            card_menu = yaml.safe_load(f)

        # Collect all cacheable entries
        entries = _find_cacheable_entries(card_menu)
        print(f"Cache warming: found {len(entries)} cacheable entries", flush=True)

        # Get all users
        users = _get_users(db)
        print(f"Cache warming: warming for {len(users)} users", flush=True)

        for user_id, lang, username in users:
            if stop_event.is_set():
                print("Cache warming: stopped by request", flush=True)
                return

            print(f"Cache warming: user '{username}' (id={user_id}, lang={lang})", flush=True)

            # Set user context for background thread
            db._warming_user_id = user_id
            db._warming_lang = lang

            try:
                _warm_entries(db, entries, lang, stop_event)
            finally:
                db._warming_user_id = None
                db._warming_lang = None

        print("Cache warming: completed", flush=True)

    except Exception as e:
        print(f"Cache warming failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        db._warming_user_id = None
        db._warming_lang = None


def _get_users(db):
    """Get list of (user_id, language_code, username) for all users."""
    users = []
    try:
        with db.lock:
            cur = db.conn.cursor()
            rows = cur.execute("SELECT id, id_language, name FROM User").fetchall()
            for row in rows:
                lang_row = cur.execute("SELECT name FROM Language WHERE id=?", (row['id_language'],)).fetchone()
                lang = lang_row['name'] if lang_row else 'en'
                users.append((row['id'], lang, row['name']))
            cur.close()
    except Exception as e:
        logging.error(f"Cache warming: failed to get users: {e}")
        users = [(-1, 'en', 'unknown')]
    return users


def _warm_entries(db, entries, lang, stop_event):
    """Run all cacheable queries for one user."""
    total = len(entries)

    # Calculate column widths for aligned log output
    idx_width = len(str(total))
    ctx_width = max(len(entry.get('context', '')) for entry in entries)

    for idx, entry in enumerate(entries):
        if stop_event.is_set():
            return

        try:
            if entry['type'] == 'dhc':
                _warm_dhc(db, entry, lang)
            elif entry['type'] == 'dq':
                _warm_dq(db, entry, lang, stop_event)
        except Exception as e:
            logging.warning(f"Cache warming: error on {entry.get('context','?')}: {e}")

        detail = entry.get('label_detail', '')
        ctx = entry.get('context', '?')
        print(f"Cache warming: {idx+1:>{idx_width}}/{total} - {ctx:<{ctx_width}} [{detail}]", flush=True)

        # Yield to user requests
        time.sleep(0.1)


def _call_method(method, params):
    """Call a database method, filtering out parameters it doesn't accept."""
    sig = inspect.signature(method)
    accepted = set(sig.parameters.keys()) - {'self'}
    filtered = {k: v for k, v in params.items() if k in accepted}
    return method(**filtered)


def _warm_dhc(db, entry, lang):
    """Warm a single dynamic_hard_coded entry."""
    method_name = PATH_TO_METHOD.get(entry['path'])
    if not method_name:
        return

    params = dict(entry['data'])
    params['lang'] = lang
    params['cacheable'] = True

    method = getattr(db, method_name, None)
    if method:
        _call_method(method, params)


def _warm_dq(db, entry, lang, stop_event):
    """Warm a dynamic_queried entry (pre-query + query loop)."""
    # Run pre-query
    pre_method_name = PATH_TO_METHOD.get(entry['pre_path'])
    if not pre_method_name:
        return

    pre_params = dict(entry['pre_data'])
    pre_params['lang'] = lang
    pre_params['cacheable'] = True

    pre_method = getattr(db, pre_method_name, None)
    if not pre_method:
        return

    pre_result = _call_method(pre_method, pre_params)

    # Extract data from pre-query result
    data_list = None
    if isinstance(pre_result, dict):
        data_list = pre_result.get('data', [])
    elif isinstance(pre_result, list):
        data_list = pre_result

    if not data_list:
        return

    # Run query loop for each result
    loop_method_name = PATH_TO_METHOD.get(entry['loop_path'])
    if not loop_method_name:
        return

    loop_method = getattr(db, loop_method_name, None)
    if not loop_method:
        return

    data_from_pre = entry.get('data_from_pre', {})
    pre_type = data_from_pre.get('type', 'value')

    for item in data_list:
        if stop_event.is_set():
            return

        loop_params = dict(entry['loop_data'])
        loop_params['lang'] = lang
        loop_params['cacheable'] = True

        if pre_type == 'dict' and isinstance(item, dict):
            mapping = data_from_pre.get('dict', {})
            for param_key, response_key in mapping.items():
                loop_params[param_key] = item.get(response_key, '')
        elif pre_type == 'value':
            value_key = data_from_pre.get('value', '')
            loop_params[value_key] = item

        try:
            _call_method(loop_method, loop_params)
        except Exception as e:
            logging.warning(f"Cache warming: query loop error: {e}")

        time.sleep(0.1)


def _find_cacheable_entries(card_menu):
    """
    Walk the card_menu structure and collect all entries with cacheable: true.
    Returns list of dicts with type, path, data, context info.
    """
    results = []
    _walk(card_menu, results, "")
    # Deduplicate
    seen = set()
    unique = []
    for e in results:
        key = str(sorted(e.items()))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def _make_label_detail(typ, data, pre_path=''):
    """Build the detail part of the log label (the part inside brackets)."""
    if typ == 'dq':
        short_path = pre_path.replace('/collect/', '')
        return f"dq: {short_path}"
    parts = []
    for k in ('genres', 'themes', 'decade', 'level', 'filter_on'):
        if k in data:
            val = str(data[k])
            if len(val) > 25:
                val = val[:25] + '...'
            parts.append(f"{k}={val}")
    if not parts:
        parts.append(f"category={data.get('category', '')}")
    return ', '.join(parts)


def _walk(obj, results, context):
    """Recursively walk card_menu structure to find cacheable entries."""
    if isinstance(obj, dict):
        # Track context from title keys
        for k in ['thumbnail', 'description']:
            if k in obj and isinstance(obj[k], dict):
                for t in obj[k].get('title', []):
                    if isinstance(t, dict) and 'trans' in t:
                        context = t['trans'].get('key', context)
                        break

        for key, val in obj.items():
            if key == 'dynamic_hard_coded' and isinstance(val, dict):
                data = val.get('data', {})
                if data.get('cacheable'):
                    req = val.get('request', {})
                    path = req.get('path', '') if isinstance(req, dict) else ''
                    clean_data = {k: v for k, v in data.items() if k != 'cacheable'}
                    results.append({
                        'type': 'dhc',
                        'context': context,
                        'label_detail': _make_label_detail('dhc', clean_data),
                        'path': path,
                        'data': clean_data,
                    })

            elif key == 'dynamic_queried' and isinstance(val, dict):
                pre = val.get('pre_query', {})
                pre_data = pre.get('data', {})
                pre_req = pre.get('request', {})
                loop = val.get('query_loop', {})
                loop_data = loop.get('data', {})

                if pre_data.get('cacheable') or loop_data.get('cacheable'):
                    loop_req = loop.get('request', {})
                    pre_path = pre_req.get('path', '')
                    results.append({
                        'type': 'dq',
                        'context': context,
                        'label_detail': _make_label_detail('dq', pre_data, pre_path),
                        'pre_path': pre_path,
                        'pre_data': {k: v for k, v in pre_data.items() if k != 'cacheable'},
                        'loop_path': loop_req.get('path', '') if isinstance(loop_req, dict) else '',
                        'loop_data': {k: v for k, v in loop_data.items() if k != 'cacheable'},
                        'data_from_pre': loop.get('data_from_pre_response_list', {}),
                    })
            else:
                _walk(val, results, context)

    elif isinstance(obj, list):
        for item in obj:
            _walk(item, results, context)
