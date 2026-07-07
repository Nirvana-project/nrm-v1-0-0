"""
Pengelolaan pengaturan aplikasi yang disimpan secara persisten di
~/.config/nrm/settings.json
"""
import json
import os
import copy

from .config import CONFIG_DIR, CONFIG_FILE, DEFAULT_SETTINGS


class Settings:
    def __init__(self):
        self._data = copy.deepcopy(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    self._data.update(saved)
            except (json.JSONDecodeError, OSError):
                # Kalau file rusak, biarkan default settings dipakai.
                pass

    def save(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()
