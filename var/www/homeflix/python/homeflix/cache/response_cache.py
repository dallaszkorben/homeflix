import hashlib
import json
import logging
import os
import shutil


class ResponseCache:

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir

    def make_key(self, **params):
        sig = '&'.join(f'{k}={v}' for k, v in sorted(params.items()) if v is not None)
        return hashlib.md5(sig.encode('utf-8')).hexdigest()

    def get(self, cache_key):
        path = os.path.join(self.cache_dir, cache_key + '.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def set(self, cache_key, data):
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            path = os.path.join(self.cache_dir, cache_key + '.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logging.warning(f"Cache write failed: {e}")

    def clear(self):
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                logging.debug(f"Cache cleared: {self.cache_dir}")
        except Exception as e:
            logging.warning(f"Cache clear failed: {e}")
