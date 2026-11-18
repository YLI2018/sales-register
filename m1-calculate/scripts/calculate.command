#!/bin/bash
# Double-click to value the ships in SHIPS with the clean data and the template's Parameters.
# Personal paths go in scripts/local_settings.sh (not in Git), e.g.
#   M1_DATA="/path/to/M1_Data"
#   M1_PARAMETERS="/path/to/M1_Comparable_Sales_Template_v1.xlsx"
#   SHIPPING_VALUATION_SRC="/path/to/shipping-vessel-valuation/src"   (the one M1 fit)
[ -f "$(dirname "$0")/local_settings.sh" ] && . "$(dirname "$0")/local_settings.sh"
DATA="${M1_DATA:-$HOME/M1_Data}"
PARAMETERS="${M1_PARAMETERS:-$HOME/M1_Comparable_Sales_Template_v1.xlsx}"
SHIPS="${M1_SHIPS:-$(dirname "$0")/../examples/ships_example.csv}"   # your own list: set M1_SHIPS in local_settings.sh
OUT="$DATA/results"
export SHIPPING_VALUATION_SRC

cd "$(dirname "$0")/.." || exit 1
PYTHONPATH=src python3 -m m1_calc --data "$DATA/clean" --parameters "$PARAMETERS" --ships "$SHIPS" --out "$OUT"
echo
read -r -p "Press Return to close."
