"""The clean data files (sales.csv, indicative_prices.csv): read them, check rows before adding, back them up, append.

The columns and rules are the data contract shared with m1-fill-template and m1-calculate (docs/data_dictionary.md).
Existing rows are never rewritten: approved rows are appended at the end, after a dated backup copy is made.
"""
import csv
import datetime as dt
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from .normalise import norm_key

SALES_COLUMNS = ["id", "report_date", "vessel", "segment", "dwt", "built", "shipyard", "yard_country", "price_musd",
                 "buyer", "seller", "features", "en_bloc", "sale_type", "source_file", "source_url", "notes",
                 "reviewed_decision", "review_reason", "next_survey"]
VALUE_COLUMNS = ["report_date", "broker", "segment", "size", "age", "value_musd", "compared_with", "earlier_value_musd",
                 "basis", "source_file"]
SEGMENTS = ("Capesize", "Post Panamax", "Kamsarmax", "Panamax", "Ultramax", "Supramax", "Handysize", "VLCC", "Suezmax",
            "Aframax", "LR2", "LR1", "MR", "Handy tanker", "Chemical tanker", "Panamax tanker", "Container", "Gas", "Other")


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def typed_source_files(sales: List[Dict[str, str]], values: List[Dict[str, str]]) -> set:
    """Every file name mentioned in the data's source_file column (it can hold several, separated by '; ')."""
    names = set()
    for row in sales + values:
        for part in (row.get("source_file") or "").split(";"):
            if part.strip():
                names.add(part.strip())
    return names


def already_in_data(sale: Dict, existing: List[Dict[str, str]], days: int = 150) -> str:
    """Describe an existing row for the same ship (same name and year built, report dates within `days`), or ''."""
    key, built = norm_key(sale.get("vessel")), sale.get("built")
    for row in existing:
        if norm_key(row.get("vessel")) == key and str(row.get("built")) == str(built):
            try:
                gap = abs((dt.date.fromisoformat(row["report_date"]) - sale["report_date"]).days)
            except (ValueError, TypeError):
                gap = 0
            if gap <= days:
                return f"yes: id {row.get('id')}, {row.get('report_date')}, ${row.get('price_musd') or '–'}m ({row.get('source_file')})"
    return ""


def value_already_in_data(v: Dict, existing: List[Dict[str, str]]) -> str:
    for row in existing:
        if (row.get("report_date") == v["report_date"].isoformat() and row.get("broker") == v["broker"]
                and row.get("segment") == v["segment"] and row.get("age") == v["age"]):
            return f"yes: {row.get('value_musd')} ({row.get('source_file')})"
    return ""


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(round(v, 6))
    return str(v).strip()


def check_rows(sales: List[Dict], values: List[Dict]) -> List[str]:
    """Contract checks on rows about to be added (they were edited by hand in the check file). Returns problems."""
    problems = []
    for i, r in enumerate(sales, start=1):
        where = f"Sales row {r.get('_row', i)} ({r.get('vessel') or 'no name'})"
        for f in ("report_date", "vessel", "segment", "built", "sale_type", "source_file"):
            if r.get(f) in (None, ""):
                problems.append(f"{where}: {f} is empty")
        if r.get("segment") and r["segment"] not in SEGMENTS:
            problems.append(f"{where}: segment '{r['segment']}' is not allowed ({', '.join(SEGMENTS)})")
        if r.get("sale_type") and r["sale_type"] not in ("Secondhand", "Resale", "Auction"):
            problems.append(f"{where}: sale_type must be Secondhand, Resale or Auction")
        if r.get("en_bloc") not in (None, "", "Y", "N", "Unknown"):
            problems.append(f"{where}: en_bloc must be Y, N or Unknown")
        for f, lo, hi in (("dwt", 1000, 600000), ("built", 1950, 2035), ("price_musd", 0.01, 1000)):
            v = r.get(f)
            if v in (None, ""):
                continue
            try:
                x = float(v)
                if not lo <= x <= hi:
                    problems.append(f"{where}: {f} {v} is outside {lo}–{hi}")
            except (TypeError, ValueError):
                problems.append(f"{where}: {f} '{v}' is not a number")
        if not isinstance(r.get("report_date"), (dt.date, dt.datetime)):
            problems.append(f"{where}: report_date is not a date")
    for i, v in enumerate(values, start=1):
        where = f"Broker values row {v.get('_row', i)}"
        for f in ("report_date", "broker", "segment", "age", "value_musd", "source_file"):
            if v.get(f) in (None, ""):
                problems.append(f"{where}: {f} is empty")
    return problems


def backup(clean: Path, stamp: str) -> Path:
    folder = clean / "backup"
    folder.mkdir(exist_ok=True)
    for name in ("sales.csv", "indicative_prices.csv"):
        shutil.copy2(clean / name, folder / f"{stamp}_{name}")
    return folder


def append(clean: Path, sales: List[Dict], values: List[Dict]) -> Tuple[int, int]:
    """Append approved rows; new sales get the next free ids. Existing lines are not touched."""
    existing = read_csv(clean / "sales.csv")
    next_id = max((int(r["id"]) for r in existing if (r.get("id") or "").isdigit()), default=0) + 1
    for name, rows, cols in (("sales.csv", sales, SALES_COLUMNS), ("indicative_prices.csv", values, VALUE_COLUMNS)):
        path = clean / name
        text = path.read_bytes()
        with path.open(newline="", encoding="utf-8-sig") as fh:
            header = next(csv.reader(fh))
        if set(header) != set(cols):
            raise ValueError(f"{name} columns differ from the data contract: {header}")
        cols = header                                   # keep the file's own column order
        with path.open("a", newline="", encoding="utf-8") as fh:
            if text and not text.endswith(b"\n"):
                fh.write("\n")
            w = csv.writer(fh)
            for r in rows:
                if name == "sales.csv":
                    r["id"] = next_id
                    next_id += 1
                w.writerow([_fmt(r.get(c)) for c in cols])
    return len(sales), len(values)
