#!/bin/bash
# Double-click: read new reports in Sources into a check file (M1_Data/staging).
# Paths go in scripts/local_settings.sh (not in Git):  export M1_SOURCES="..."  export M1_DATA="..."
[ -f "$(dirname "$0")/local_settings.sh" ] && . "$(dirname "$0")/local_settings.sh"
cd "$(dirname "$0")/.." || exit 1
PYTHONPATH=src .venv/bin/python -m m1_extract extract --sources "$M1_SOURCES" --data "$M1_DATA"
echo; read -r -p "Press Return to close."
