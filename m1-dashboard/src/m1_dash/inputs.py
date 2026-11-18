"""Read Calculate's output (a results folder M1_calc_<date_time>) and, optionally, the database for the Database page.

Calculate writes, per run: results.csv (one line per ship), comparables.csv (every sale used, per ship) and run.log.
Nothing here changes any file.
"""
import csv
import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class InputError(Exception):
    """An input is missing or unreadable; the message says which and what to do."""


@dataclass
class Comparable:
    vessel: str
    report_date: dt.date
    age: int
    price_musd: float
    adjusted_price_musd: float
    fitted_price_musd: Optional[float]


@dataclass
class ShipResult:
    case_id: str
    name: str
    segment: str
    valuation_date: dt.date
    target_age: int
    value_musd: Optional[float]
    low_musd: Optional[float]
    high_musd: Optional[float]
    loss_rate: Optional[float]
    a_musd: Optional[float]
    b: Optional[float]
    r_squared: Optional[float]
    n_comparables: int
    known_price_musd: Optional[float]
    status: str
    failed_checks: List[str]
    message: str
    comparables: List[Comparable] = field(default_factory=list)

    @property
    def status_kind(self) -> str:
        """'good', 'warning' or 'critical', for the status label."""
        if self.status == "VALID":
            return "good"
        return "warning" if self.status.startswith("Usable") else "critical"


@dataclass
class RunInfo:
    folder: str
    run_time: str
    version: str
    sales: Optional[int]
    broker_values: Optional[int]


def latest_run(results_root: Path) -> Path:
    """The newest M1_calc_<date_time> folder that holds results.csv."""
    runs = sorted(p for p in results_root.glob("M1_calc_*") if (p / "results.csv").is_file())
    if not runs:
        raise InputError(f"no Calculate results in {results_root}: run project 4 (Calculate) first")
    return runs[-1]


def _num(text: str) -> Optional[float]:
    text = (text or "").strip()
    return float(text) if text else None


def _date(text: str) -> dt.date:
    return dt.date.fromisoformat(text.strip()[:10])


def read_run(run_dir: Path) -> (RunInfo, List[ShipResult]):
    res_path, comp_path = run_dir / "results.csv", run_dir / "comparables.csv"
    if not res_path.is_file():
        raise InputError(f"{res_path} not found: choose a folder written by Calculate")
    ships: List[ShipResult] = []
    with res_path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ships.append(ShipResult(
                case_id=r["case_id"], name=r["target_name"], segment=r["segment"],
                valuation_date=_date(r["valuation_date"]), target_age=int(float(r["target_age"])),
                value_musd=_num(r["value_musd"]), low_musd=_num(r["range_low_musd"]), high_musd=_num(r["range_high_musd"]),
                loss_rate=_num(r["loss_rate"]), a_musd=_num(r["a_musd"]), b=_num(r["b"]), r_squared=_num(r["r_squared"]),
                n_comparables=int(float(r["n_comparables"] or 0)), known_price_musd=_num(r.get("known_price_musd", "")),
                status=r["status"], failed_checks=[c.strip() for c in (r.get("failed_checks") or "").split(";") if c.strip()],
                message=r.get("message", "")))
    by_id = {s.case_id: s for s in ships}
    if comp_path.is_file():
        with comp_path.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                s = by_id.get(r["case_id"])
                if s is not None:
                    s.comparables.append(Comparable(r["vessel"], _date(r["report_date"]), int(float(r["age_at_sale"])),
                                                    float(r["price_musd"]), float(r["adjusted_price_musd"]),
                                                    _num(r.get("fitted_price_musd", ""))))
    info = RunInfo(run_dir.name, "", "", None, None)
    log = run_dir / "run.log"
    if log.is_file():
        text = log.read_text(encoding="utf-8")
        m = re.search(r"^run:\s*(.+)$", text, re.M)
        info.run_time = m.group(1).strip() if m else ""
        m = re.search(r"^(m1_calc \S+)", text, re.M)
        info.version = m.group(1) if m else ""
        m = re.search(r"sales:\s*(\d+);\s*broker values:\s*(\d+)", text)
        if m:
            info.sales, info.broker_values = int(m.group(1)), int(m.group(2))
    if not ships:
        raise InputError(f"{res_path} holds no ships")
    return info, ships


@dataclass
class SaleRow:
    report_date: dt.date
    segment: str


def read_database(clean_dir: Optional[Path]) -> List[SaleRow]:
    """Report date and segment of every sale in clean/sales.csv (for the Database page); empty if not given."""
    if clean_dir is None:
        return []
    path = clean_dir / "sales.csv"
    if not path.is_file():
        raise InputError(f"{path} not found: --data must be the M1_Data/clean folder")
    rows = []
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                rows.append(SaleRow(_date(r["report_date"]), (r.get("segment") or "").strip() or "Not given"))
            except (ValueError, KeyError):
                continue
    return rows
