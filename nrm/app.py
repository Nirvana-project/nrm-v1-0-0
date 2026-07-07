"""
Gtk.Application utama untuk NRM. Menangani pembukaan file dari argumen
command-line maupun dari file manager (mis. klik-kanan "Open With NRM").
"""
import os
import sys
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib

from .config import APP_ID, APP_NAME
from .settings import Settings
from .window import NRMWindow


class NRMApplication(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.window = None
        self.settings = Settings()
        self._pending_files = []

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        if not self.window:
            self.window = NRMWindow(self, self.settings)
        self.window.present()
        for filepath in self._pending_files:
            self.window.open_path(filepath)
        self._pending_files = []

    def do_open(self, files, n_files, hint):
        # Dipanggil saat aplikasi dibuka dengan file (mis. "nrm file.md"
        # atau lewat file manager).
        paths = [f.get_path() for f in files if f.get_path()]
        if not self.window:
            self.activate()
        for path in paths:
            self.window.open_path(path)
        self.window.present()
        return 0

    def do_command_line(self, command_line):
        args = command_line.get_arguments()[1:]
        files = [os.path.abspath(a) for a in args if os.path.isfile(a)]
        if files:
            self._pending_files = files
        self.activate()
        return 0


def main():
    app = NRMApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
