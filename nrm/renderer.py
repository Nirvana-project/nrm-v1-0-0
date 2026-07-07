"""
Modul untuk mengubah teks Markdown menjadi dokumen HTML lengkap
(siap ditampilkan di WebKit2), termasuk syntax highlighting kode
dan tabel isi (table of contents).
"""
import html
import markdown
from markdown.extensions.toc import TocExtension

from .config import MARKDOWN_EXTENSIONS, MARKDOWN_EXTENSION_CONFIGS

try:
    from pygments.formatters import HtmlFormatter
    PYGMENTS_CSS = HtmlFormatter(style="default").get_style_defs(".highlight")
    PYGMENTS_CSS_DARK = HtmlFormatter(style="monokai").get_style_defs(".highlight")
except ImportError:
    PYGMENTS_CSS = ""
    PYGMENTS_CSS_DARK = ""


BASE_CSS = """
:root {
    --nrm-font-size: __FONT_SIZE__px;
}
* { box-sizing: border-box; }
html, body {
    margin: 0;
    padding: 0;
    background: var(--bg);
    color: var(--fg);
}
body {
    font-family: -apple-system, "Segoe UI", "Cantarell", "Ubuntu", "Noto Sans", sans-serif;
    font-size: var(--nrm-font-size);
    line-height: 1.65;
    padding: 2.5em 3em 5em 3em;
    max-width: 860px;
    margin: 0 auto;
}
h1, h2, h3, h4, h5, h6 {
    font-weight: 650;
    line-height: 1.3;
    margin-top: 1.6em;
    margin-bottom: 0.6em;
    color: var(--heading);
    scroll-margin-top: 1.5em;
}
h1 { font-size: 2em; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }
h2 { font-size: 1.6em; border-bottom: 1px solid var(--border); padding-bottom: 0.25em; }
h3 { font-size: 1.3em; }
h4 { font-size: 1.1em; }
p, ul, ol, blockquote, table, pre { margin-top: 0; margin-bottom: 1.1em; }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
    font-family: "JetBrains Mono", "Fira Code", "DejaVu Sans Mono", monospace;
    background: var(--code-bg);
    color: var(--code-fg);
    padding: 0.15em 0.4em;
    border-radius: 4px;
    font-size: 0.9em;
}
pre {
    background: var(--code-bg);
    padding: 1em 1.2em;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid var(--border);
}
pre code { background: none; padding: 0; border-radius: 0; font-size: 0.88em; }
blockquote {
    border-left: 4px solid var(--accent);
    margin-left: 0;
    padding: 0.2em 1.2em;
    color: var(--muted);
    background: var(--blockquote-bg);
    border-radius: 0 6px 6px 0;
}
table { border-collapse: collapse; width: 100%; display: block; overflow-x: auto; }
th, td { border: 1px solid var(--border); padding: 0.5em 0.9em; text-align: left; }
th { background: var(--table-head-bg); font-weight: 600; }
tr:nth-child(even) { background: var(--table-alt-bg); }
img { max-width: 100%; border-radius: 6px; }
hr { border: none; border-top: 1px solid var(--border); margin: 2.2em 0; }
::selection { background: var(--selection); }
.admonition {
    border-left: 4px solid var(--accent);
    background: var(--blockquote-bg);
    padding: 0.8em 1.2em;
    border-radius: 0 6px 6px 0;
    margin-bottom: 1.1em;
}
.admonition-title { font-weight: 700; margin-bottom: 0.3em; }
.toclink { color: var(--link); }
"""

LIGHT_VARS = """
:root {
    --bg: #ffffff;
    --fg: #24292f;
    --heading: #111318;
    --border: #e4e6ea;
    --link: #0969da;
    --code-bg: #f4f5f7;
    --code-fg: #c7254e;
    --muted: #57606a;
    --blockquote-bg: #f6f8fa;
    --accent: #6b46c1;
    --table-head-bg: #f4f5f7;
    --table-alt-bg: #fafbfc;
    --selection: #cfe4ff;
}
"""

DARK_VARS = """
:root {
    --bg: #1a1b1e;
    --fg: #d8dae0;
    --heading: #f2f3f5;
    --border: #34363b;
    --link: #6cb6ff;
    --code-bg: #26272b;
    --code-fg: #ff9d9d;
    --muted: #9aa0a8;
    --blockquote-bg: #232427;
    --accent: #9575cd;
    --table-head-bg: #26272b;
    --table-alt-bg: #202124;
    --selection: #3a4a63;
}
"""


def render_markdown_to_html(md_text, theme="light", font_size=16, base_dir=None):
    """
    Ubah teks markdown menjadi dokumen HTML lengkap (dengan <html>, <head>, <style>).

    Args:
        md_text: isi file markdown mentah.
        theme: "light" atau "dark".
        font_size: ukuran font dasar dalam px.
        base_dir: direktori tempat file .md berada, dipakai sebagai base
                   href supaya gambar relatif tetap termuat.

    Returns:
        (html_string, toc_html, headings)
        headings: list of dict {level, id, text} untuk sidebar TOC kustom.
    """
    md = markdown.Markdown(
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
        output_format="html5",
    )
    body_html = md.convert(md_text)
    toc_html = getattr(md, "toc", "")
    toc_tokens = getattr(md, "toc_tokens", [])

    headings = []

    def _flatten(tokens):
        for t in tokens:
            headings.append({
                "level": t.get("level", 1),
                "id": t.get("id", ""),
                "text": t.get("name", ""),
            })
            if t.get("children"):
                _flatten(t["children"])

    _flatten(toc_tokens)

    vars_css = DARK_VARS if theme == "dark" else LIGHT_VARS
    pygments_css = PYGMENTS_CSS_DARK if theme == "dark" else PYGMENTS_CSS
    css = vars_css + BASE_CSS.replace("__FONT_SIZE__", str(font_size)) + "\n" + pygments_css

    base_tag = ""
    if base_dir:
        # base_dir dipakai agar tag <img src="relative.png"> tetap termuat
        safe_dir = html.escape(base_dir, quote=True)
        base_tag = f'<base href="file://{safe_dir}/">'

    doc = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
{base_tag}
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>"""
    return doc, toc_html, headings


def render_empty_state_html(theme="light"):
    """HTML placeholder saat belum ada file yang dibuka."""
    vars_css = DARK_VARS if theme == "dark" else LIGHT_VARS
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
{vars_css}
html, body {{ height: 100%; margin: 0; background: var(--bg); }}
.wrap {{
    height: 100%; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-family: -apple-system, "Segoe UI", "Cantarell", sans-serif;
    color: var(--muted);
}}
.wrap h1 {{ color: var(--heading); font-size: 1.4em; margin-bottom: 0.2em; }}
.wrap p {{ margin: 0.2em 0; }}
kbd {{
    background: var(--code-bg); border: 1px solid var(--border);
    border-radius: 4px; padding: 0.1em 0.5em; font-family: monospace;
}}
</style></head>
<body><div class="wrap">
<h1>NRM &mdash; Nirvana Reader MD</h1>
<p>Belum ada file yang dibuka.</p>
<p>Tekan <kbd>Ctrl</kbd>+<kbd>O</kbd> atau seret file .md ke sini.</p>
</div></body></html>"""
