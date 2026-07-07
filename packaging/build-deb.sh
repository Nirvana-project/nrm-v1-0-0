#!/usr/bin/env bash
# ============================================================================
# build-deb.sh — Merakit paket .deb dari binary NRM yang sudah dikompilasi
# oleh build.sh.
#
# Pemakaian:
#   ./build.sh          # kompilasi dulu
#   ./build-deb.sh       # baru rakit .deb
#
# Hasil: packaging/nrm_<versi>_amd64.deb
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
VERSION="1.0.0"
ARCH="$(dpkg --print-architecture 2>/dev/null || echo amd64)"
PKG_NAME="nrm"
PKG_ROOT="$SCRIPT_DIR/pkgroot"

if [ ! -f "$BUILD_DIR/nrm" ]; then
    echo "Binary belum ada. Jalankan ./build.sh terlebih dahulu."
    exit 1
fi

echo "=== Menyiapkan struktur paket ==="
rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/DEBIAN"
mkdir -p "$PKG_ROOT/usr/bin"
mkdir -p "$PKG_ROOT/usr/share/applications"
mkdir -p "$PKG_ROOT/usr/share/doc/$PKG_NAME"

for size in 16 22 24 32 48 64 128 256 512; do
    mkdir -p "$PKG_ROOT/usr/share/icons/hicolor/${size}x${size}/apps"
    cp "$SRC_DIR/data/icons/nrm-${size}.png" \
       "$PKG_ROOT/usr/share/icons/hicolor/${size}x${size}/apps/nrm.png"
done

cp "$BUILD_DIR/nrm" "$PKG_ROOT/usr/bin/nrm"
chmod 755 "$PKG_ROOT/usr/bin/nrm"

cp "$SRC_DIR/data/nrm.desktop" "$PKG_ROOT/usr/share/applications/nrm.desktop"

cat > "$PKG_ROOT/usr/share/doc/$PKG_NAME/copyright" <<'EOF'
NRM (Nirvana Reader MD)
Aplikasi pembaca file Markdown untuk Linux.
EOF

INSTALLED_SIZE=$(du -sk "$PKG_ROOT/usr" | cut -f1)

cat > "$PKG_ROOT/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Installed-Size: $INSTALLED_SIZE
Depends: python3 (>= 3.8), python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1 | gir1.2-webkit2-4.0, python3-markdown, python3-pygments
Maintainer: Cymfoni <noreply@example.com>
Description: NRM - Nirvana Reader MD
 Pembaca file Markdown yang ringan untuk Linux (Debian/Ubuntu/Zorin OS),
 dibangun dengan GTK3 dan WebKit2. Mendukung tab, dark mode, tabel isi,
 auto-reload, dan ekspor ke PDF/HTML.
EOF

cat > "$PKG_ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 755 "$PKG_ROOT/DEBIAN/postinst"

cat > "$PKG_ROOT/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 755 "$PKG_ROOT/DEBIAN/postrm"

DEB_FILE="$SCRIPT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"
echo "=== Membangun $DEB_FILE ==="
dpkg-deb --build --root-owner-group "$PKG_ROOT" "$DEB_FILE"

echo ""
echo "Selesai! Install dengan:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt --fix-broken install   # jika ada dependency yang kurang"
