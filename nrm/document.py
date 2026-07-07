"""
Representasi satu dokumen markdown yang sedang terbuka (satu tab).
"""
import os


class MarkdownDocument:
    def __init__(self, filepath=None, text=""):
        self.filepath = filepath
        self.text = text
        self.headings = []

    @property
    def title(self):
        if self.filepath:
            return os.path.basename(self.filepath)
        return "Tanpa judul"

    @property
    def directory(self):
        if self.filepath:
            return os.path.dirname(os.path.abspath(self.filepath))
        return None

    def load(self):
        if self.filepath and os.path.isfile(self.filepath):
            with open(self.filepath, "r", encoding="utf-8", errors="replace") as f:
                self.text = f.read()
            return True
        return False
