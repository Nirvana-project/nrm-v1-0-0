"""
File watcher sederhana berbasis polling (mtime) memakai GLib.timeout_add.
Dipilih dibanding inotify/watchdog supaya nol dependency eksternal dan
tetap ringan di hardware lawas.
"""
import os
from gi.repository import GLib

from .config import WATCH_INTERVAL_SECONDS


class FileWatcher:
    def __init__(self, on_change_callback):
        """
        on_change_callback: dipanggil dengan argumen (filepath) saat file
        yang diawasi berubah (mtime berubah) atau muncul kembali setelah hilang.
        """
        self._on_change = on_change_callback
        self._watched = {}   # filepath -> last_mtime
        self._source_id = None

    def watch(self, filepath):
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            mtime = None
        self._watched[filepath] = mtime
        self._ensure_running()

    def unwatch(self, filepath):
        self._watched.pop(filepath, None)
        if not self._watched and self._source_id is not None:
            GLib.source_remove(self._source_id)
            self._source_id = None

    def _ensure_running(self):
        if self._source_id is None:
            self._source_id = GLib.timeout_add(
                int(WATCH_INTERVAL_SECONDS * 1000), self._poll
            )

    def _poll(self):
        for filepath, last_mtime in list(self._watched.items()):
            try:
                mtime = os.path.getmtime(filepath)
            except OSError:
                mtime = None
            if mtime != last_mtime:
                self._watched[filepath] = mtime
                if mtime is not None:
                    self._on_change(filepath)
        return True  # tetap jalan terus (GLib.SOURCE_CONTINUE)

    def stop(self):
        if self._source_id is not None:
            GLib.source_remove(self._source_id)
            self._source_id = None
        self._watched.clear()
