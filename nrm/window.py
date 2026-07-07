"""
Jendela utama aplikasi NRM: header bar, tab (Gtk.Notebook), sidebar
daftar isi, dan area render markdown via WebKit2.
"""
import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio, GObject, Pango

# WebKit2 punya beberapa versi API tergantung distro (4.0 di Ubuntu 22.04 /
# Zorin OS 17, 4.1 di distro yang lebih baru). Coba keduanya.
WebKit2 = None
for _ver in ("4.1", "4.0"):
    try:
        gi.require_version("WebKit2", _ver)
        from gi.repository import WebKit2 as _wk
        WebKit2 = _wk
        break
    except (ValueError, ImportError):
        continue

if WebKit2 is None:
    raise RuntimeError(
        "WebKit2GTK tidak ditemukan. Install salah satu dari:\n"
        "  sudo apt install gir1.2-webkit2-4.1\n"
        "  sudo apt install gir1.2-webkit2-4.0"
    )

from .config import APP_NAME, APP_FULL_NAME, APP_VERSION
from .document import MarkdownDocument
from .renderer import render_markdown_to_html, render_empty_state_html
from .watcher import FileWatcher


class DocTab:
    """Menyimpan semua widget & state untuk satu tab dokumen."""

    def __init__(self, document, webview, toc_listbox, paned, tab_label):
        self.document = document
        self.webview = webview
        self.toc_listbox = toc_listbox
        self.paned = paned
        self.tab_label = tab_label
        self.zoom = 1.0


class NRMWindow(Gtk.ApplicationWindow):
    def __init__(self, app, settings):
        super().__init__(application=app, title=APP_FULL_NAME)
        self.settings = settings
        self.set_default_size(
            settings.get("window_width", 1000),
            settings.get("window_height", 700),
        )
        self.set_icon_name("nrm")

        self.theme = settings.get("theme", "light")
        self.font_size = settings.get("font_size", 16)
        self.auto_reload = settings.get("auto_reload", True)
        self.show_sidebar_pref = settings.get("show_sidebar", True)

        self._tabs = {}  # notebook page widget -> DocTab
        self.watcher = FileWatcher(self._on_file_changed)

        self._build_headerbar()
        self._build_body()
        self._setup_drag_and_drop()
        self._setup_shortcuts()

        self.connect("destroy", self._on_destroy)

        # Tampilkan shell window (headerbar, notebook kosong) dulu.
        # Tab dibuat & di-show setelah ini, supaya widget di dalamnya
        # (yang punya show_all() sendiri) tidak konflik dengan show_all()
        # di level window.
        self.show_all()

        # Mulai dengan satu tab kosong (empty state)
        self.new_tab()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_headerbar(self):
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.set_title(APP_FULL_NAME)
        self.set_titlebar(hb)
        self.headerbar = hb

        # Tombol buka file
        open_btn = Gtk.Button()
        open_btn.set_image(Gtk.Image.new_from_icon_name(
            "document-open-symbolic", Gtk.IconSize.LARGE_TOOLBAR))
        open_btn.set_tooltip_text("Buka file Markdown (Ctrl+O)")
        open_btn.connect("clicked", lambda *_: self.open_file_dialog())
        hb.pack_start(open_btn)

        # Toggle sidebar
        sidebar_btn = Gtk.ToggleButton()
        sidebar_btn.set_image(Gtk.Image.new_from_icon_name(
            "view-list-symbolic", Gtk.IconSize.LARGE_TOOLBAR))
        sidebar_btn.set_tooltip_text("Tampilkan/sembunyikan daftar isi")
        sidebar_btn.set_active(self.show_sidebar_pref)
        sidebar_btn.connect("toggled", self._on_toggle_sidebar)
        hb.pack_start(sidebar_btn)
        self.sidebar_btn = sidebar_btn

        # Grup zoom
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom_box.get_style_context().add_class("linked")
        zoom_out_btn = Gtk.Button()
        zoom_out_btn.set_image(Gtk.Image.new_from_icon_name(
            "zoom-out-symbolic", Gtk.IconSize.LARGE_TOOLBAR))
        zoom_out_btn.set_tooltip_text("Perkecil (Ctrl+-)")
        zoom_out_btn.connect("clicked", lambda *_: self.adjust_zoom(-0.1))
        zoom_in_btn = Gtk.Button()
        zoom_in_btn.set_image(Gtk.Image.new_from_icon_name(
            "zoom-in-symbolic", Gtk.IconSize.LARGE_TOOLBAR))
        zoom_in_btn.set_tooltip_text("Perbesar (Ctrl++)")
        zoom_in_btn.connect("clicked", lambda *_: self.adjust_zoom(0.1))
        zoom_box.pack_start(zoom_out_btn, False, False, 0)
        zoom_box.pack_start(zoom_in_btn, False, False, 0)
        hb.pack_start(zoom_box)

        # Toggle tema gelap/terang
        theme_btn = Gtk.Button()
        theme_btn.set_tooltip_text("Ganti tema terang/gelap")
        theme_btn.connect("clicked", self._on_toggle_theme)
        hb.pack_end(theme_btn)
        self.theme_btn = theme_btn
        self._update_theme_icon()

        # Menu hamburger
        menu_btn = Gtk.MenuButton()
        menu_btn.set_image(Gtk.Image.new_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.LARGE_TOOLBAR))
        menu_btn.set_popover(self._build_menu_popover())
        hb.pack_end(menu_btn)

    def _build_menu_popover(self):
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_border_width(8)

        def add_item(label, callback):
            btn = Gtk.ModelButton()
            btn.set_label(label)
            btn.get_child().set_halign(Gtk.Align.START)
            btn.connect("clicked", callback)
            box.pack_start(btn, False, False, 0)
            return btn

        add_item("Tab Baru", lambda *_: self.new_tab())
        add_item("Buka File\u2026", lambda *_: self.open_file_dialog())
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

        self.auto_reload_item = add_item(
            "\u2713 Auto-reload file" if self.auto_reload else "  Auto-reload file",
            self._on_toggle_auto_reload,
        )
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

        add_item("Ekspor ke PDF\u2026", lambda *_: self.export_pdf())
        add_item("Ekspor ke HTML\u2026", lambda *_: self.export_html())
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

        add_item("Tentang NRM", lambda *_: self._show_about_dialog())

        box.show_all()
        popover.add(box)
        return popover

    def _build_body(self):
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.connect("switch-page", self._on_switch_page)
        self.add(self.notebook)

    def _setup_drag_and_drop(self):
        self.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [Gtk.TargetEntry.new("text/uri-list", 0, 0)],
            Gdk.DragAction.COPY,
        )
        self.connect("drag-data-received", self._on_drag_data_received)

    def _setup_shortcuts(self):
        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)

        def bind(accel_str, callback):
            key, mods = Gtk.accelerator_parse(accel_str)
            accel.connect(key, mods, Gtk.AccelFlags.VISIBLE, callback)

        bind("<Control>o", lambda *_: self.open_file_dialog())
        bind("<Control>w", lambda *_: self.close_current_tab())
        bind("<Control>t", lambda *_: self.new_tab())
        bind("<Control>plus", lambda *_: self.adjust_zoom(0.1))
        bind("<Control>equal", lambda *_: self.adjust_zoom(0.1))
        bind("<Control>minus", lambda *_: self.adjust_zoom(-0.1))
        bind("<Control>0", lambda *_: self.reset_zoom())
        bind("<Control>d", lambda *_: self._on_toggle_theme())
        bind("<Control>b", lambda *_: self.sidebar_btn.set_active(not self.sidebar_btn.get_active()))
        bind("<Control>p", lambda *_: self.export_pdf())

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------
    def new_tab(self, filepath=None):
        document = MarkdownDocument(filepath=filepath)
        if filepath:
            document.load()

        webview = WebKit2.WebView()
        webview.connect("decide-policy", self._on_decide_policy)

        toc_listbox = Gtk.ListBox()
        toc_listbox.get_style_context().add_class("nrm-toc")
        toc_listbox.connect("row-activated", self._on_toc_row_activated)

        toc_scroller = Gtk.ScrolledWindow()
        toc_scroller.set_size_request(200, -1)
        toc_scroller.add(toc_listbox)

        webview_scroller = Gtk.ScrolledWindow()
        webview_scroller.add(webview)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.pack1(toc_scroller, False, False)
        paned.pack2(webview_scroller, True, False)
        paned.set_position(220)

        tab_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        label = Gtk.Label(label=document.title)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(20)
        close_btn = Gtk.Button()
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.set_image(Gtk.Image.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.MENU))
        tab_label_box.pack_start(label, True, True, 0)
        tab_label_box.pack_start(close_btn, False, False, 0)
        tab_label_box.show_all()

        paned.show_all()
        page_index = self.notebook.append_page(paned, tab_label_box)
        self.notebook.set_tab_reorderable(paned, True)

        tab = DocTab(document, webview, toc_listbox, paned, label)
        self._tabs[paned] = tab

        close_btn.connect("clicked", lambda *_: self.close_tab(paned))

        toc_scroller.set_visible(self.show_sidebar_pref)

        self.notebook.set_current_page(page_index)
        self._refresh_tab(tab)

        if filepath:
            self.watcher.watch(filepath)

        return tab

    def close_tab(self, paned):
        tab = self._tabs.get(paned)
        if not tab:
            return
        if tab.document.filepath:
            self.watcher.unwatch(tab.document.filepath)
        page_num = self.notebook.page_num(paned)
        if page_num != -1:
            self.notebook.remove_page(page_num)
        del self._tabs[paned]
        if self.notebook.get_n_pages() == 0:
            self.new_tab()

    def close_current_tab(self):
        page_num = self.notebook.get_current_page()
        if page_num == -1:
            return
        paned = self.notebook.get_nth_page(page_num)
        self.close_tab(paned)

    def _current_tab(self):
        page_num = self.notebook.get_current_page()
        if page_num == -1:
            return None
        paned = self.notebook.get_nth_page(page_num)
        return self._tabs.get(paned)

    def _on_switch_page(self, notebook, page, page_num):
        tab = self._tabs.get(page)
        if tab:
            self._update_window_title(tab)

    def _update_window_title(self, tab):
        if tab.document.filepath:
            self.set_title(f"{tab.document.title} \u2014 {APP_NAME}")
        else:
            self.set_title(APP_FULL_NAME)

    # ------------------------------------------------------------------
    # Membuka file
    # ------------------------------------------------------------------
    def open_file_dialog(self):
        dialog = Gtk.FileChooserDialog(
            title="Buka File Markdown",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            "Batal", Gtk.ResponseType.CANCEL,
            "Buka", Gtk.ResponseType.OK,
        )
        filter_md = Gtk.FileFilter()
        filter_md.set_name("Markdown (*.md, *.markdown)")
        filter_md.add_pattern("*.md")
        filter_md.add_pattern("*.markdown")
        dialog.add_filter(filter_md)
        filter_all = Gtk.FileFilter()
        filter_all.set_name("Semua file")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            dialog.destroy()
            self.open_path(filepath)
        else:
            dialog.destroy()

    def open_path(self, filepath):
        if not filepath or not os.path.isfile(filepath):
            self._show_error(f"File tidak ditemukan:\n{filepath}")
            return
        current = self._current_tab()
        # Kalau tab saat ini kosong (belum ada file), pakai tab itu saja.
        if current and current.document.filepath is None and not current.document.text.strip():
            current.document.filepath = filepath
            current.document.load()
            current.tab_label.set_text(current.document.title)
            self._refresh_tab(current)
            self.watcher.watch(filepath)
            self._update_window_title(current)
        else:
            self.new_tab(filepath=filepath)

    # ------------------------------------------------------------------
    # Render & refresh
    # ------------------------------------------------------------------
    def _refresh_tab(self, tab):
        doc = tab.document
        if doc.filepath:
            base_dir = doc.directory
            html_doc, toc_html, headings = render_markdown_to_html(
                doc.text, theme=self.theme, font_size=self.font_size, base_dir=base_dir,
            )
            doc.headings = headings
            base_uri = f"file://{base_dir}/" if base_dir else None
            tab.webview.load_html(html_doc, base_uri)
        else:
            doc.headings = []
            tab.webview.load_html(render_empty_state_html(theme=self.theme), None)

        self._rebuild_toc(tab)
        tab.webview.set_zoom_level(tab.zoom)

    def _rebuild_toc(self, tab):
        listbox = tab.toc_listbox
        for child in listbox.get_children():
            listbox.remove(child)

        if not tab.document.headings:
            placeholder = Gtk.Label(label="(tidak ada heading)")
            placeholder.set_sensitive(False)
            placeholder.set_margin_top(10)
            row = Gtk.ListBoxRow()
            row.add(placeholder)
            row.set_selectable(False)
            listbox.add(row)
            listbox.show_all()
            return

        for heading in tab.document.headings:
            label = Gtk.Label(label=heading["text"])
            label.set_halign(Gtk.Align.START)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_margin_start(12 * max(0, heading["level"] - 1))
            row = Gtk.ListBoxRow()
            row.add(label)
            row.heading_id = heading["id"]
            listbox.add(row)
        listbox.show_all()

    def _on_toc_row_activated(self, listbox, row):
        heading_id = getattr(row, "heading_id", None)
        tab = self._current_tab()
        if tab and heading_id:
            js = (
                "var el = document.getElementById(%r); "
                "if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }"
            ) % heading_id
            try:
                tab.webview.run_javascript(js, None, None, None)
            except TypeError:
                try:
                    tab.webview.run_javascript(js, None, None)
                except Exception:
                    pass
            except Exception:
                pass

    # ------------------------------------------------------------------
    # File watcher callback (auto-reload)
    # ------------------------------------------------------------------
    def _on_file_changed(self, filepath):
        if not self.auto_reload:
            return
        for tab in self._tabs.values():
            if tab.document.filepath == filepath:
                tab.document.load()
                self._refresh_tab(tab)

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------
    def adjust_zoom(self, delta):
        tab = self._current_tab()
        if not tab:
            return
        tab.zoom = max(0.5, min(3.0, tab.zoom + delta))
        tab.webview.set_zoom_level(tab.zoom)

    def reset_zoom(self):
        tab = self._current_tab()
        if not tab:
            return
        tab.zoom = 1.0
        tab.webview.set_zoom_level(1.0)

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------
    def _on_toggle_theme(self, *_args):
        self.theme = "dark" if self.theme == "light" else "light"
        self.settings.set("theme", self.theme)
        self._update_theme_icon()
        for tab in self._tabs.values():
            self._refresh_tab(tab)

    def _update_theme_icon(self):
        icon_name = "weather-clear-night-symbolic" if self.theme == "light" else "weather-clear-symbolic"
        self.theme_btn.set_image(Gtk.Image.new_from_icon_name(
            icon_name, Gtk.IconSize.LARGE_TOOLBAR))
        tip = "Ganti ke tema gelap" if self.theme == "light" else "Ganti ke tema terang"
        self.theme_btn.set_tooltip_text(tip)

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------
    def _on_toggle_sidebar(self, button):
        self.show_sidebar_pref = button.get_active()
        self.settings.set("show_sidebar", self.show_sidebar_pref)
        for tab in self._tabs.values():
            toc_scroller = tab.paned.get_child1()
            toc_scroller.set_visible(self.show_sidebar_pref)

    # ------------------------------------------------------------------
    # Auto reload toggle
    # ------------------------------------------------------------------
    def _on_toggle_auto_reload(self, *_args):
        self.auto_reload = not self.auto_reload
        self.settings.set("auto_reload", self.auto_reload)
        self.auto_reload_item.set_label(
            "\u2713 Auto-reload file" if self.auto_reload else "  Auto-reload file"
        )

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------
    def _on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        uris = data.get_uris()
        for uri in uris:
            filepath = GLib.filename_from_uri(uri)[0]
            if filepath and filepath.lower().endswith((".md", ".markdown", ".txt")):
                self.open_path(filepath)
        Gtk.drag_finish(drag_context, True, False, time)

    # ------------------------------------------------------------------
    # Klik link internal/eksternal di webview
    # ------------------------------------------------------------------
    def _on_decide_policy(self, webview, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            nav_action = decision.get_navigation_action()
            request = nav_action.get_request()
            uri = request.get_uri()
            if uri.startswith("file://") and uri.lower().endswith((".md", ".markdown")):
                filepath = GLib.filename_from_uri(uri)[0]
                decision.ignore()
                self.open_path(filepath)
                return True
            if uri.startswith("http://") or uri.startswith("https://"):
                decision.ignore()
                Gtk.show_uri_on_window(self, uri, Gdk.CURRENT_TIME)
                return True
        return False

    # ------------------------------------------------------------------
    # Ekspor
    # ------------------------------------------------------------------
    def export_pdf(self):
        tab = self._current_tab()
        if not tab or not tab.document.filepath:
            self._show_error("Tidak ada dokumen untuk diekspor.")
            return
        print_op = WebKit2.PrintOperation.new(tab.webview)
        print_op.run_dialog(self)

    def export_html(self):
        tab = self._current_tab()
        if not tab or not tab.document.filepath:
            self._show_error("Tidak ada dokumen untuk diekspor.")
            return

        dialog = Gtk.FileChooserDialog(
            title="Ekspor ke HTML",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            "Batal", Gtk.ResponseType.CANCEL,
            "Simpan", Gtk.ResponseType.OK,
        )
        dialog.set_do_overwrite_confirmation(True)
        base_name = os.path.splitext(os.path.basename(tab.document.filepath))[0]
        dialog.set_current_name(f"{base_name}.html")

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            out_path = dialog.get_filename()
            dialog.destroy()
            html_doc, _, _ = render_markdown_to_html(
                tab.document.text, theme=self.theme, font_size=self.font_size,
                base_dir=tab.document.directory,
            )
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(html_doc)
            except OSError as e:
                self._show_error(f"Gagal menyimpan file:\n{e}")
        else:
            dialog.destroy()

    # ------------------------------------------------------------------
    # Dialog bantu
    # ------------------------------------------------------------------
    def _show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    def _show_about_dialog(self, *_args):
        about = Gtk.AboutDialog(transient_for=self)
        about.set_program_name(APP_FULL_NAME)
        about.set_version(APP_VERSION)
        about.set_comments("Pembaca file Markdown yang ringan untuk Linux.")
        about.set_logo_icon_name("nrm")
        about.run()
        about.destroy()

    # ------------------------------------------------------------------
    def _on_destroy(self, *_args):
        self.settings.set("window_width", self.get_size()[0])
        self.settings.set("window_height", self.get_size()[1])
        self.watcher.stop()
