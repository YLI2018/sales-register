"""Historical valuation data cut: keep only what was published on or before the valuation date.

Writes <M1_Data>/historical_<date>/clean/sales.csv and indicative_prices.csv with report_date <= the cut-off,
so a valuation dated 22 May 2026 uses no sale or broker value reported after that day (no hindsight).

    python3 scripts/historical_cut.py "<M1_Data folder>" 2026-05-22
"""
import csv
import sys
from pathlib import Path

data, cutoff = Path(sys.argv[1]), sys.argv[2]
out = data / f"historical_{cutoff}" / "clean"
out.mkdir(parents=True, exist_ok=True)
for name in ("sales.csv", "indicative_prices.csv"):
    with open(data / "clean" / name, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    kept = [r for r in rows if r["report_date"] <= cutoff]
    with open(out / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(kept)
    print(f"{name}: kept {len(kept)} of {len(rows)} rows reported on or before {cutoff}")
