"""Read everything the calculation needs: the clean data files, the parameters and the ships to value.

Data files follow the data contract shared with m1-fill-template (docs/data_dictionary.md): UTF-8 CSV, named columns,
dates YYYY-MM-DD, dot decimals, empty = not reported. The clean folder holds checked data; this module only checks
what the calculation itself depends on and stops on anything it cannot read.
"""
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import openpyxl


class InputError(Exception):
    """An input file is missing, unreadable or breaks the data contract."""


# ---------------------------------------------------------------- value parsing
def _text(v: Optional[str]) -> Optional[str]:
    v = (v or "").strip()
    return v or None


def _number(v: Optional[str], where: str) -> Optional[float]:
    v = _text(v)
    if v is None:
        return None
    if "," in v:
        raise InputError(f"{where}: '{v}' has a comma; the contract uses a dot as decimal mark")
    try:
        return float(v)
    except ValueError:
        raise InputError(f"{where}: '{v}' is not a number")


def _date(v: Optional[str], where: str) -> Optional[dt.date]:
    v = _text(v)
    if v is None:
        return None
    try:
        return dt.datetime.strptime(v, "%Y-%m-%d").date()
    except ValueError:
        hint = " (Excel changes dates when it saves a CSV; edit the file in VS Code or a text editor)" if "/" in v else ""
        raise InputError(f"{where}: '{v}' is not a date YYYY-MM-DD{hint}")


def _read_csv(path: Path, required: List[str]) -> List[Dict[str, str]]:
    if not path.exists():
        raise InputError(f"{path.name}: not found at {path}")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise InputError(f"{path.name}: missing columns: {', '.join(missing)}")
        return [row for row in reader if any((v or "").strip() for v in row.values())]


# ---------------------------------------------------------------- data
@dataclass
class Sale:
    """One row of sales.csv, in file order (the order matters for rule R6: a name already listed earlier)."""
    id: int
    report_date: dt.date
    vessel: str
    segment: str
    dwt: Optional[float]
    built: int
    price_musd: Optional[float]
    features: str
    en_bloc: Optional[str]
    sale_type: str
    notes: str
    reviewed_decision: Optional[str]


@dataclass
class BrokerValue:
    """One row of indicative_prices.csv."""
    report_date: dt.date
    broker: str
    segment: str
    age: str
    value_musd: float


def read_sales(path: Path) -> List[Sale]:
    rows = _read_csv(path, ["id", "report_date", "vessel", "segment", "dwt", "built", "price_musd", "features",
                            "en_bloc", "sale_type", "notes", "reviewed_decision"])
    sales = []
    for i, r in enumerate(rows, start=2):
        w = f"sales.csv line {i}"
        sales.append(Sale(
            id=int(_number(r["id"], w) or 0), report_date=_date(r["report_date"], w), vessel=_text(r["vessel"]) or "",
            segment=_text(r["segment"]) or "", dwt=_number(r["dwt"], w), built=int(_number(r["built"], w) or 0),
            price_musd=_number(r["price_musd"], w), features=_text(r["features"]) or "", en_bloc=_text(r["en_bloc"]),
            sale_type=_text(r["sale_type"]) or "", notes=_text(r["notes"]) or "", reviewed_decision=_text(r["reviewed_decision"])))
        if not sales[-1].report_date or not sales[-1].vessel or not sales[-1].built:
            raise InputError(f"{w}: report_date, vessel and built are required")
    return sales


def read_broker_values(path: Path) -> List[BrokerValue]:
    rows = _read_csv(path, ["report_date", "broker", "segment", "age", "value_musd"])
    out = []
    for i, r in enumerate(rows, start=2):
        w = f"indicative_prices.csv line {i}"
        value = _number(r["value_musd"], w)
        if value is None:
            raise InputError(f"{w}: value_musd is required")
        out.append(BrokerValue(_date(r["report_date"], w), _text(r["broker"]) or "", _text(r["segment"]) or "",
                               _text(r["age"]) or "", value))
    return out


# ---------------------------------------------------------------- parameters
@dataclass
class Parameters:
    """Settings for one segment, read from the Parameters sheet of the M1 template (the single source of settings)."""
    segment: str
    status: str
    dwt_min: float
    dwt_max: float
    dwt_tolerance: float
    age_min: float
    age_max: float
    benchmark_provider: str
    benchmark_segment: str
    benchmark_labels: List[str]
    benchmark_ages: List[float]
    benchmark_max_days: float
    min_comparables: int
    min_r_squared: float
    range_sd: float
    near_age_window: float
    charter_keywords: List[str] = field(default_factory=list)
    review_keywords: List[str] = field(default_factory=list)


def read_parameters(template: Path) -> Dict[str, Parameters]:
    """Read every segment row (rows 6-20) and the global keywords (C25:C28) from the template's Parameters sheet.

    The workbook is opened read-only; only typed settings are read, never calculated cells.
    """
    if not template.exists():
        raise InputError(f"parameters workbook not found at {template}")
    wb = openpyxl.load_workbook(template, data_only=True)
    if "Parameters" not in wb.sheetnames:
        raise InputError(f"{template.name}: no 'Parameters' sheet")
    ws = wb["Parameters"]
    cell = lambda ref: ws[ref].value
    charter = [k for k in (cell("C25"), cell("C26")) if k]
    review = [k for k in (cell("C27"), cell("C28")) if k]
    out = {}
    for r in range(6, 21):
        seg = cell(f"A{r}")
        if not seg:
            continue
        v = {c: cell(f"{c}{r}") for c in "BCDEFGHIJKLMNOPQRSTUVW"}
        try:
            out[seg] = Parameters(
                segment=seg, status=v["B"] or "", dwt_min=float(v["C"]), dwt_max=float(v["D"]), dwt_tolerance=float(v["E"]),
                age_min=float(v["F"]), age_max=float(v["G"]), benchmark_provider=v["H"], benchmark_segment=v["I"],
                benchmark_labels=[v["J"], v["K"], v["L"]], benchmark_ages=[float(v["M"]), float(v["N"]), float(v["O"])],
                benchmark_max_days=float(v["P"]), min_comparables=int(v["Q"]), min_r_squared=float(v["R"]),
                range_sd=float(v["S"]), near_age_window=float(v["T"]), charter_keywords=charter, review_keywords=review)
        except (TypeError, ValueError) as e:
            raise InputError(f"Parameters row {r} ({seg}): a setting is missing or not a number ({e})")
    wb.close()
    return out


# ---------------------------------------------------------------- ships to value
@dataclass
class Ship:
    """One valuation case: the target ship and the valuation date."""
    case_id: str
    target_name: str
    segment: str
    dwt: float
    year_built: int
    valuation_date: dt.date
    known_price_musd: Optional[float] = None
    use_reviewed_decisions: bool = True


SHIP_COLUMNS = ["case_id", "target_name", "segment", "dwt", "year_built", "valuation_date", "known_price_musd",
                "use_reviewed_decisions"]


def _ship(rec: Dict[str, object], where: str) -> Ship:
    s = lambda k: None if rec.get(k) is None else str(rec.get(k))
    for k in ("case_id", "target_name", "segment", "dwt", "year_built", "valuation_date"):
        if _text(s(k)) is None:
            raise InputError(f"{where}: {k} is required")
    use = (_text(s("use_reviewed_decisions")) or "Yes")
    if use not in ("Yes", "No"):
        raise InputError(f"{where}: use_reviewed_decisions must be Yes or No")
    return Ship(case_id=_text(s("case_id")), target_name=_text(s("target_name")), segment=_text(s("segment")),
                dwt=_number(s("dwt"), where), year_built=int(_number(s("year_built"), where)),
                valuation_date=_date(s("valuation_date"), where), known_price_musd=_number(s("known_price_musd"), where),
                use_reviewed_decisions=(use == "Yes"))


def read_ships(path: Path) -> List[Ship]:
    """A list of ships (CSV, one row per ship) or a single case file (JSON, as used by m1-fill-template)."""
    if path.suffix.lower() == ".json":
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise InputError(f"{path.name}: {e}")
        return [_ship(rec, path.name)]
    rows = _read_csv(path, SHIP_COLUMNS[:6])
    ships = [_ship(r, f"{path.name} line {i}") for i, r in enumerate(rows, start=2)]
    ids = [x.case_id for x in ships]
    if len(ids) != len(set(ids)):
        raise InputError(f"{path.name}: case_id must be unique")
    return ships
