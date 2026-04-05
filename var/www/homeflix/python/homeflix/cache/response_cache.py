"""
Server-side file-based response cache for expensive SQL query results.

Stores JSON responses as individual files in a cache directory.
Each unique query (identified by its parameters) gets its own cache file.
Cache is shared across all clients — any browser/device benefits from
cached results created by any other client.

Cache lifecycle:
  - Created on first query (cache miss → SQL runs → result saved to file)
  - Served on subsequent queries (cache hit → file read, no SQL)
  - Cleared on Rebuild Static DB (recreate_static_dbs() calls clear())

Cache location: /home/pi/.homeflix/cache/
Cache files: {md5_hash}.json

The 'cacheable' flag in card_menu.yaml controls which queries use the cache.
Queries without cacheable=true (e.g., playlists, search) always hit the database.

See .kiro/steering/performance-optimizations.md for full documentation.
"""

import hashlib
import json
import logging
import os
import shutil


class ResponseCache:

    def __init__(self, cache_dir):
        """
        Initialize cache with the directory path for storing cache files.
        The directory is created automatically on first write.

        Args:
            cache_dir: Absolute path to cache directory (e.g., /home/pi/.homeflix/cache/)
        """
        self.cache_dir = cache_dir

    def make_key(self, **params):
        """
        Create a unique cache key from query parameters.

        Sorts parameters alphabetically, joins them as key=value pairs,
        and returns an MD5 hash. None values are excluded so that
        queries with default parameters match correctly.

        Args:
            **params: All query parameters including method name, user_id,
                      category, filters, etc.

        Returns:
            MD5 hex string used as the cache filename (without extension)

        Example:
            make_key(method='get_highest_level_cards', category='movie', lang='en')
            → 'a1b2c3d4e5f6...'
        """
        sig = '&'.join(f'{k}={v}' for k, v in sorted(params.items()) if v is not None)
        return hashlib.md5(sig.encode('utf-8')).hexdigest()

    def get(self, cache_key):
        """
        Read cached response from file.

        Args:
            cache_key: MD5 hash string from make_key()

        Returns:
            Parsed JSON data (dict or list) on cache hit, None on cache miss
        """
        path = os.path.join(self.cache_dir, cache_key + '.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def set(self, cache_key, data):
        """
        Write query response to cache file atomically.

        Writes to a temporary file first, then uses os.replace() for
        atomic rename. This prevents corrupted cache files if the warming
        thread and a user request write the same key simultaneously.

        Creates the cache directory if it doesn't exist.
        Silently handles write errors (disk full, permissions, etc.)
        to avoid breaking the query flow.

        Args:
            cache_key: MD5 hash string from make_key()
            data: JSON-serializable response data to cache
        """
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            path = os.path.join(self.cache_dir, cache_key + '.json')
            tmp_path = path + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp_path, path)
        except Exception as e:
            logging.warning(f"Cache write failed: {e}")

    def clear(self):
        """
        Delete all cached responses by removing the entire cache directory.

        Called by recreate_static_dbs() when the user triggers
        'Rebuild Static DB' from the Server Settings menu.
        This ensures all clients get fresh data after a rebuild.
        """
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                logging.debug(f"Cache cleared: {self.cache_dir}")
        except Exception as e:
            logging.warning(f"Cache clear failed: {e}")
