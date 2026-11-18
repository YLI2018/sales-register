"""Read the input files and check them against the data contract.

Every problem is reported with file, row and column, so an analyst can fix the source.
Errors stop the run; warnings are listed in the log and the run continues.
"""
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .contract import (CASE_FIELDS, PRICE_FIELDS, PRICES_FIRST_ROW, PRICES_LAST_ROW, SALES_FIELDS, SALES_FIRST_ROW,
                       SALES_LAST_ROW, Field)


@dataclass
class CheckResult:
    """Rows that passed, plus the errors and warnings found."""
    rows: List[Dict[str, object]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def parse_value(raw: str, f: Field):
    """Convert one text value to the field's type. Returns (value, error message or None).

    Empty text gives None. Numbers must use a dot as decimal mark: '28,45' is rejected with a hint,
    because a comma could also be a thousands separator and guessing would risk a wrong price.
    """
    text = (raw or "").strip()
    if text == "":
        return None, None
    try:
        if f.kind == "int":
            if "," in text:
                return None, f"'{text}' has a comma; write whole numbers without separators"
            num = float(text)
            if num != int(num):
                return None, f"'{text}' is not a whole number"
            value = int(num)
        elif f.kind == "float":
            if "," in text:
                return None, f"'{text}' has a comma; use a dot as decimal mark (28.45, not 28,45)"
            value = float(text)
        elif f.kind == "date":
            value = dt.datetime.strptime(text, "%Y-%m-%d")
        elif f.kind == "choice":
            if text not in f.choices:
                return None, f"'{text}' is not allowed; allowed: {', '.join(f.choices)}"
            value = text
        else:
            value = text
    except ValueError:
        expected = {"int": "a whole number", "float": "a number", "date": "a date YYYY-MM-DD"}[f.kind]
        return None, f"'{text}' is not {expected}"
    if f.limits and isinstance(value, (int, float)) and not (f.limits[0] <= value <= f.limits[1]):
        return None, f"{value} is outside {f.limits[0]:g} to {f.limits[1]:g}"
    return value, None


def read_table(path: Path, fields: Sequence[Field], capacity: int) -> CheckResult:
    """Read one CSV file and check every row against the given fields.

    Checks: required columns present, required values filled, types, allowed values, limits, capacity.
    Unknown columns are ignored with a warning.
    """
    res = CheckResult()
    name = path.name
    if not path.exists():
        res.errors.append(f"{name}: file not found at {path}")
        return res
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        missing = [f.name for f in fields if f.name not in header]
        if missing:
            res.errors.append(f"{name}: missing columns: {', '.join(missing)}")
            return res
        extra = [h for h in header if h not in {f.name for f in fields}]
        if extra:
            res.warnings.append(f"{name}: columns not in the contract are ignored: {', '.join(extra)}")
        for line_no, raw in enumerate(reader, start=2):
            if not any((v or "").strip() for v in raw.values()):
                continue  # completely empty line
            row, row_ok = {}, True
            for f in fields:
                value, err = parse_value(raw.get(f.name, ""), f)
                if err:
                    res.errors.append(f"{name} line {line_no}, {f.name}: {err}")
                    row_ok = False
                elif value is None and f.required:
                    res.errors.append(f"{name} line {line_no}, {f.name}: required value is empty")
                    row_ok = False
                elif value is None and f.warn_if_blank:
                    res.warnings.append(f"{name} line {line_no}, {f.name}: empty")
                row[f.name] = value
            row["_line"] = line_no
            if row_ok:
                res.rows.append(row)
    if len(res.rows) > capacity:
        res.errors.append(f"{name}: {len(res.rows)} rows, but the template holds {capacity}; extend the template first")
    return res


def read_sales(path: Path) -> CheckResult:
    """Read sales.csv and add the checks that need the whole table (unique id, duplicates, review reasons)."""
    res = read_table(path, SALES_FIELDS, SALES_LAST_ROW - SALES_FIRST_ROW + 1)
    seen_ids, seen_sales = {}, {}
    for r in res.rows:
        if r["id"] in seen_ids:
            res.errors.append(f"sales.csv line {r['_line']}, id: {r['id']} already used on line {seen_ids[r['id']]}")
        seen_ids.setdefault(r["id"], r["_line"])
        key = (r["vessel"].lower(), r["report_date"])
        if key in seen_sales:
            res.warnings.append(f"sales.csv line {r['_line']}: {r['vessel']} on {r['report_date']:%Y-%m-%d} also on line "
                                f"{seen_sales[key]} (same sale twice?)")
        seen_sales.setdefault(key, r["_line"])
        if r["reviewed_decision"] and not r["review_reason"]:
            res.warnings.append(f"sales.csv line {r['_line']}: reviewed decision without a reason")
    return res


def read_prices(path: Path) -> CheckResult:
    """Read indicative_prices.csv and flag the same value given twice (same date, broker, segment, age)."""
    res = read_table(path, PRICE_FIELDS, PRICES_LAST_ROW - PRICES_FIRST_ROW + 1)
    seen = {}
    for r in res.rows:
        key = (r["report_date"], r["broker"], r["segment"], r["age"])
        if key in seen:
            res.warnings.append(f"indicative_prices.csv line {r['_line']}: same date, broker, segment and age as line "
                                f"{seen[key]}; the Benchmarks sheet will show 'Duplicate'")
        seen.setdefault(key, r["_line"])
    return res


def read_case(path: Path) -> CheckResult:
    """Read the case JSON file (one object with the CASE_FIELDS names) and check it."""
    res = CheckResult()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        res.errors.append(f"case file not found at {path}")
        return res
    except json.JSONDecodeError as e:
        res.errors.append(f"{path.name}: not valid JSON ({e})")
        return res
    row = {}
    for f in CASE_FIELDS:
        raw = data.get(f.name)
        value, err = parse_value("" if raw is None else str(raw), f)
        if err:
            res.errors.append(f"{path.name}, {f.name}: {err}")
        elif value is None and f.required:
            res.errors.append(f"{path.name}, {f.name}: required value is empty")
        row[f.name] = value
    unknown = [k for k in data if k not in {f.name for f in CASE_FIELDS}]
    if unknown:
        res.warnings.append(f"{path.name}: fields not in the contract are ignored: {', '.join(unknown)}")
    if not res.errors:
        res.rows.append(row)
    return res
