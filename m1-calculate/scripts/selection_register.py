"""Selection register: one line per MR sale in the database, saying whether M1 used it and why not.

    PYTHONPATH=src python3 scripts/selection_register.py "<M1_Data folder>" 2026-05-22 "<template>.xlsx"

Reads the full clean/sales.csv (all dates), applies the date cut (reported on or before the valuation date),
then the M1 rules R1-R6 and reviewed decisions exactly as m1-calculate does. Writes
<M1_Data>/historical_<date>/selection_register.csv and prints the funnel counts.
"""
import collections
import csv
import datetime as dt
import sys
from pathlib import Path

from m1_calc import engine, inputs

data, cutoff, template = Path(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]), Path(sys.argv[3])
p = inputs.read_parameters(template)["MR"]
ship = inputs.read_ships(data / f"historical_{cutoff}" / "ships.csv")[0]
sales = [s for s in inputs.read_sales(data / "clean" / "sales.csv") if s.segment == "MR"]
raw = {int(r["id"]): r for r in csv.DictReader(open(data / "clean" / "sales.csv", newline="", encoding="utf-8"))}
RULES = {"R1": "size outside MR band", "R2": "resale or newbuilding", "R3": "no exact price",
         "R4": "sold with time charter", "R5": "older than the maximum age", "R6": "same ship listed earlier"}

kept = [s for s in sales if s.report_date <= cutoff]
bt = engine.benchmark_table(inputs.read_broker_values(data / "clean" / "indicative_prices.csv"), p)
sel = engine.select_comparables(kept, ship, p, bt, engine.nearest_ok_date(cutoff, bt))
used = {c.sale.id for c in sel.comparables}

out, funnel = [], collections.Counter()
for s in sales:
    r = raw[s.id]
    if s.report_date > cutoff:
        step, why = "Excluded", f"reported after the valuation date {cutoff:%d %b %Y}"
    else:
        dec, src, fails = sel.decisions[s.id]
        if dec == "Target":
            step, why = "Target", "the ship being valued"
        elif s.id in used:
            step, why = "Used", r["review_reason"] or "passes R1-R6 (automatic screen)"
        else:
            step = "Excluded"
            why = r["review_reason"] if src.startswith("Reviewed") else \
                "; ".join(f"{f} {RULES[f]}" for f in fails) or dec
    funnel[(step, why.split(" ")[0] if step == "Excluded" else step)] += 1
    out.append(dict(id=s.id, report_date=s.report_date, vessel=s.vessel, dwt=r["dwt"], built=s.built,
                    age_at_sale=engine.age_at_sale(s), price_musd=r["price_musd"], source=r["source_file"],
                    m1_status=step, reason=why))
dest = data / f"historical_{cutoff}" / "selection_register.csv"
with open(dest, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(f"MR sales in database: {len(sales)}; reported by {cutoff}: {len(kept)}; used: {len(used)}; undecided: {sel.undecided_reviews}")
for k, v in sorted(funnel.items()):
    print(f"  {k[0]:9} {k[1]:12} {v}")
print("written:", dest)
