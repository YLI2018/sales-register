#!/bin/bash
# Double-click: add the rows marked OK in the newest check file to the clean data (after a backup).
[ -f "$(dirname "$0")/local_settings.sh" ] && . "$(dirname "$0")/local_settings.sh"
cd "$(dirname "$0")/.." || exit 1
PYTHONPATH=src .venv/bin/python -m m1_extract add --data "$M1_DATA"
echo; read -r -p "Press Return to close."
