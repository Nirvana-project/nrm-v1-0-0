"""
NRM (Nirvana Reader MD) - Konfigurasi & konstanta global aplikasi.
"""
import os

APP_ID = "id.nirvana.nrm"
APP_NAME = "NRM"
APP_FULL_NAME = "Nirvana Reader MD"
APP_VERSION = "1.0.0"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "nrm")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "theme": "light",          # "light" atau "dark"
    "zoom": 1.0,                # level zoom webview
    "show_sidebar": True,       # tampilkan sidebar daftar isi
    "auto_reload": True,        # auto-reload saat file berubah
    "window_width": 1000,
    "window_height": 700,
    "font_size": 16,            # ukuran font dasar (px) untuk konten
}

# Interval polling untuk file watcher (detik)
WATCH_INTERVAL_SECONDS = 1.0

MARKDOWN_EXTENSIONS = [
    "extra",            # tables, fenced_code, footnotes, dll
    "sane_lists",
    "codehilite",
    "toc",
    "admonition",
    "nl2br",
    "smarty",
]

MARKDOWN_EXTENSION_CONFIGS = {
    "codehilite": {
        "guess_lang": False,
        "css_class": "highlight",
    },
    "toc": {
        "anchorlink": False,
        "permalink": False,
    },
}
