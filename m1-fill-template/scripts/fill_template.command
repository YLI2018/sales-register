#!/bin/bash
# Double-click to fill the blank M1 template with the data in DATA and the case in CASE.
# The data folder comes from the M1_DATA setting (or ~/M1_Data); change CASE and OUT below if needed.
# Personal paths go in scripts/local_settings.sh (not in Git), e.g.  M1_DATA="/path/to/M1_Data"
[ -f "$(dirname "$0")/local_settings.sh" ] && . "$(dirname "$0")/local_settings.sh"
DATA="${M1_DATA:-$HOME/M1_Data}"
CASE="$(dirname "$0")/../examples/case_target_ship_1.json"
OUT="$DATA/output"

cd "$(dirname "$0")/.." || exit 1
PYTHONPATH=src python3 -m m1_fill --data "$DATA/clean" --case "$CASE" --out "$OUT"
echo
read -r -p "Press Return to close."
