# NRM — Nirvana Reader MD

Pembaca file Markdown (.md) yang ringan untuk Linux (Debian, Ubuntu, Zorin OS,
dan turunannya lainnya). Dibangun dengan Python + GTK3 + WebKit2, lalu
dikompilasi menjadi binary native memakai Nuitka.

## Fitur (v1.0.0)

- Buka file `.md` lewat file picker atau drag-and-drop
- Render Markdown lengkap: heading, tabel, blockquote, list, dll
- Syntax highlighting untuk code block (Pygments)
- Tema terang & gelap (toggle satu klik)
- Zoom in/out konten
- Ekspor ke PDF (lewat dialog print bawaan GTK) dan ke HTML
- Auto-reload: file otomatis ter-render ulang saat disimpan/diedit
- Sidebar daftar isi (table of contents), klik untuk lompat ke bagian
- Multi-tab, bisa buka beberapa file sekaligus

## Struktur Proyek

```
nrm-src/
├── nrm/                 # source code Python (package utama)
│   ├── app.py           # Gtk.Application, handle buka file dari CLI
│   ├── window.py        # jendela utama, tab, toolbar, sidebar
│   ├── renderer.py       # markdown -> HTML + tema CSS
│   ├── document.py       # representasi satu dokumen/tab
│   ├── watcher.py        # auto-reload (polling mtime)
│   ├── settings.py       # simpan pengaturan ke ~/.config/nrm/
│   └── config.py         # konstanta aplikasi
├── nrm_main.py           # entry point (target kompilasi Nuitka)
├── run-dev.sh            # jalankan langsung tanpa compile (testing)
├── data/
│   ├── nrm.desktop       # desktop entry
│   └── icons/            # icon berbagai ukuran (dari logo yang kamu buat)
└── packaging/
    ├── build.sh          # compile nrm_main.py -> binary native (Nuitka)
    └── build-deb.sh      # rakit binary + aset jadi paket .deb
```

## Cara Pakai (Testing Cepat, Tanpa Compile)

Untuk mencoba aplikasinya dulu sebelum compile:

```bash
cd nrm-src
./run-dev.sh
# atau langsung buka file:
./run-dev.sh ~/Documents/catatan.md
```

Script ini otomatis mengecek dependency yang kurang dan memberi tahu perintah
`apt install` yang perlu dijalankan kalau ada yang belum terpasang.

## Cara Compile & Install (Produksi)

### 1. Compile ke binary native

```bash
cd nrm-src/packaging
./build.sh
```

Proses ini akan:
- Mengecek & memasang dependency sistem (`python3-gi`, `gir1.2-gtk-3.0`,
  `gir1.2-webkit2-4.1`/`4.0`, `python3-markdown`, `python3-pygments`) lewat `apt`
- Memasang Nuitka lewat `pip3` kalau belum ada
- Mengompilasi `nrm_main.py` menjadi binary native di `packaging/build/nrm`

Catatan: proses compile butuh koneksi internet (untuk `apt`/`pip`) dan
memakan waktu beberapa menit tergantung spesifikasi mesin.

### 2. Rakit jadi paket .deb

```bash
./build-deb.sh
```

Menghasilkan `packaging/nrm_1.0.0_amd64.deb`.

### 3. Install

```bash
sudo dpkg -i packaging/nrm_1.0.0_amd64.deb
sudo apt --fix-broken install   # kalau ada dependency yang belum terpasang
```

Setelah terinstall, NRM akan muncul di menu aplikasi, dan bisa dibuka lewat
terminal dengan:

```bash
nrm
nrm nama-file.md
```

File `.md` juga bisa langsung diklik-kanan → "Open With NRM" dari file manager
(Files/Nautilus, dsb) karena `nrm.desktop` mendaftarkan MIME type
`text/markdown`.

### Uninstall

```bash
sudo apt remove nrm
```

## Pintasan Keyboard

| Aksi                        | Shortcut       |
|-----------------------------|----------------|
| Buka file                   | `Ctrl+O`       |
| Tab baru                    | `Ctrl+T`       |
| Tutup tab                   | `Ctrl+W`       |
| Perbesar / perkecil          | `Ctrl+ +` / `Ctrl+ -` |
| Reset zoom                  | `Ctrl+0`       |
| Toggle tema gelap/terang     | `Ctrl+D`       |
| Toggle sidebar               | `Ctrl+B`       |
| Ekspor PDF                   | `Ctrl+P`       |

## Kenapa Nuitka (bukan PyInstaller)?

Nuitka mengompilasi Python langsung ke kode C lalu ke binary native — bukan
sekadar membungkus interpreter (seperti PyInstaller). Hasilnya:
- Startup lebih cepat, penting untuk hardware seperti HP Pro 3330 MT
- Source code Python tidak ikut terdistribusi mentah-mentah dalam bentuk `.py`
- Tetap memakai library sistem (`python3-gi`, WebKit2GTK) yang sudah
  teroptimasi oleh distro, bukan membundel ulang versi sendiri yang lebih berat
