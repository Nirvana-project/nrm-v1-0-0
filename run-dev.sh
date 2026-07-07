#!/usr/bin/env bash
# Jalankan NRM langsung dari source Python tanpa kompilasi.
# Cocok untuk testing cepat sebelum build .deb yang sebenarnya.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MISSING=()
python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" 2>/dev/null \
    || MISSING+=(python3-gi gir1.2-gtk-3.0)
python3 -c "
import gi
ok = False
for v in ('4.1','4.0'):
    try:
        gi.require_version('WebKit2', v)
        from gi.repository import WebKit2
        ok = True
        break
    except Exception:
        pass
import sys
sys.exit(0 if ok else 1)
" 2>/dev/null || MISSING+=(gir1.2-webkit2-4.1)
python3 -c "import markdown" 2>/dev/null || MISSING+=(python3-markdown)
python3 -c "import pygments" 2>/dev/null || MISSING+=(python3-pygments)

if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "Paket berikut belum terpasang: ${MISSING[*]}"
    echo "Install dulu dengan:"
    echo "  sudo apt update && sudo apt install -y ${MISSING[*]}"
    exit 1
fi

python3 nrm_main.py "$@"
