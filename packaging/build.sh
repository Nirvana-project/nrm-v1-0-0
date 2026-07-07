#!/usr/bin/env bash
# ============================================================================
# build.sh — Kompilasi NRM (Nirvana Reader MD) dari source Python menjadi
# binary native memakai Nuitka.
#
# Jalankan di mesin Debian/Ubuntu/Zorin target (bukan di sandbox lain),
# karena binary hasil kompilasi akan terikat ke versi libpython & arsitektur
# mesin ini.
#
# Pemakaian:
#   cd packaging
#   ./build.sh
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"

echo "=== [1/4] Cek & pasang dependency build ==="
NEED_APT=()
command -v gcc  >/dev/null 2>&1 || NEED_APT+=(gcc)
command -v ccache >/dev/null 2>&1 || NEED_APT+=(ccache)
python3 -c "import gi" 2>/dev/null || NEED_APT+=(python3-gi gir1.2-gtk-3.0)
python3 -c "import markdown" 2>/dev/null || NEED_APT+=(python3-markdown)
python3 -c "import pygments" 2>/dev/null || NEED_APT+=(python3-pygments)

if python3 -c "import gi; gi.require_version('WebKit2','4.1'); from gi.repository import WebKit2" 2>/dev/null; then
    :
elif python3 -c "import gi; gi.require_version('WebKit2','4.0'); from gi.repository import WebKit2" 2>/dev/null; then
    :
else
    NEED_APT+=(gir1.2-webkit2-4.1)
fi

if [ "${#NEED_APT[@]}" -gt 0 ]; then
    echo "Menginstall paket sistem yang dibutuhkan: ${NEED_APT[*]}"
    sudo apt update
    sudo apt install -y "${NEED_APT[@]}"
fi

echo "=== [2/4] Cek & pasang Nuitka ==="
if ! python3 -c "import nuitka" >/dev/null 2>&1; then
    echo "Nuitka belum terpasang, memasang via pip3 (--user)..."
    pip3 install --user --break-system-packages nuitka 2>/dev/null \
        || pip3 install --user nuitka
fi

echo "=== [3/4] Kompilasi nrm_main.py -> binary native ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$SRC_DIR"

python3 -m nuitka \
    --output-dir="$BUILD_DIR" \
    --remove-output \
    --python-flag=no_docstrings \
    --assume-yes-for-downloads \
    --lto=yes \
    --jobs="$(nproc)" \
    nrm_main.py

if [ -f "$BUILD_DIR/nrm_main.bin" ]; then
    mv "$BUILD_DIR/nrm_main.bin" "$BUILD_DIR/nrm"
elif [ -f "$BUILD_DIR/nrm_main" ]; then
    mv "$BUILD_DIR/nrm_main" "$BUILD_DIR/nrm"
fi

if [ ! -f "$BUILD_DIR/nrm" ]; then
    echo "GAGAL: binary hasil kompilasi tidak ditemukan di $BUILD_DIR"
    exit 1
fi

chmod +x "$BUILD_DIR/nrm"
echo "=== [4/4] Selesai ==="
echo "Binary hasil kompilasi: $BUILD_DIR/nrm"
echo "Jalankan langsung dengan: $BUILD_DIR/nrm"
echo "Atau lanjutkan dengan ./build-deb.sh untuk membuat paket .deb"
