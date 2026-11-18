#!/bin/zsh
# Double-click: make the dashboard from the newest Calculate results and open it.
cd "$(dirname "$0")/.." || exit 2
source scripts/local_settings.sh || { echo "Set your folder in scripts/local_settings.sh"; read; exit 2; }
out=$(PYTHONPATH=src python3 -m m1_dash --results "$M1_DATA/results" --data "$M1_DATA/clean" ${M3_RESULTS:+--m3 "$M3_RESULTS"} --out "$M1_DATA/dashboard")
echo "$out"
file=$(echo "$out" | sed -n 's/^Dashboard: //p')
[ -n "$file" ] && open "$file"
echo; echo "Press Return to close."; read
