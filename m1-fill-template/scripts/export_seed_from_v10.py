"""One-off: write the data typed into M1 v10 as the two contract files (sales.csv, indicative_prices.csv).

usage: python3 scripts/export_seed_from_v10.py M1_Market_Database_v10.xlsx OUTPUT_FOLDER

This stands in for the Extract sub-project until it exists: it gives Fill template real, already-checked data.
v10 is opened read-only (values only) and is not changed. Refuses to overwrite existing CSV files.

Showcase rule: private research remarks in the notes ("... check whether linked to ...") are dropped, so the
exported data carries no remarks about specific companies. Market facts (ships, prices, buyers, sellers) are kept.
"""
import re
import csv
import datetime as dt
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from m1_fill.contract import (PRICE_FIELDS, PRICES_FIRST_ROW, PRICES_LAST_ROW, SALES_FIELDS,  # noqa: E402
                              SALES_FIRST_ROW, SALES_LAST_ROW)


PRIVATE_REMARK = re.compile(r"[^.;]*check whether linked to[^.;]*[.;]?", re.IGNORECASE)


def clean_note(text):
    """Drop private research remarks from a note; return None if nothing is left."""
    if not isinstance(text, str):
        return text
    out = PRIVATE_REMARK.sub("", text).strip()
    return out or None


def fmt(v):
    """Contract format: dates YYYY-MM-DD, numbers as plain text with a dot, None as empty."""
    if v is None:
        return ""
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def export(ws, fields, first, last, key_col, path: Path) -> int:
    n = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([f.name for f in fields])
        for r in range(first, last + 1):
            if ws[f"{key_col}{r}"].value in (None, ""):
                continue
            w.writerow([fmt(clean_note(ws[f"{f.column}{r}"].value) if f.name == "notes" else ws[f"{f.column}{r}"].value)
                        for f in fields])
            n += 1
    return n


def main(v10: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    targets = [out / "sales.csv", out / "indicative_prices.csv"]
    if any(t.exists() for t in targets):
        raise SystemExit(f"{out} already holds sales.csv or indicative_prices.csv; not overwritten")
    wb = openpyxl.load_workbook(v10, data_only=True, read_only=False)
    ns = export(wb["Sales Register"], SALES_FIELDS, SALES_FIRST_ROW, SALES_LAST_ROW, "C", targets[0])
    npr = export(wb["Indicative Prices"], PRICE_FIELDS, PRICES_FIRST_ROW, PRICES_LAST_ROW, "A", targets[1])
    print(f"sales.csv: {ns} rows; indicative_prices.csv: {npr} rows; written to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
