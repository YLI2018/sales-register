"""Which reports exist in the report archive, which broker wrote them, and which are new.

A report is one PDF, or for HSN Weekly Vessel Valuations all screenshots with the same date prefix
(2026-11-04_HSN_VesselValuations_wk_1.png, …_wk_2.png), read in order.

The list of reports already read is extracted_reports.csv in the data folder. A report is new when its fingerprint
(SHA-256 of its file contents) is not on that list, so renaming a file does not make it new and a corrected edition with
the same name does. The first time, reports whose file names already appear in the data (typed by hand in M1) are
listed as "typed in M1" without being read.
"""
import csv
import datetime as dt
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

REGISTER_COLUMNS = ["report_id", "broker", "report_date", "files", "fingerprint", "status", "read_at", "sales_found",
                    "values_found", "check_file", "added_at", "sales_added", "values_added"]


@dataclass
class Report:
    report_id: str
    broker: str                    # advanced / xclusiv / intermodal / hsn
    report_date: dt.date
    files: List[Path] = field(default_factory=list)

    @property
    def fingerprint(self) -> str:
        h = hashlib.sha256()
        for f in self.files:
            h.update(f.read_bytes())
        return h.hexdigest()

    @property
    def file_names(self) -> str:
        return "; ".join(f.name for f in self.files)


def broker_of(name: str) -> Optional[str]:
    low = name.lower()
    if "advanced" in low:
        return "advanced"
    if "xclusiv" in low:
        return "xclusiv"
    if "intermodal" in low:
        return "intermodal"
    if "hsn" in low and low.endswith((".png", ".jpg", ".jpeg")):
        return "hsn"
    return None


def find_reports(sources: Path) -> List[Report]:
    """All broker reports in the archive folder (top level), oldest first. Files that are not reports are ignored."""
    groups: Dict[str, Report] = {}
    for f in sorted(sources.iterdir()):
        if not f.is_file() or f.name.startswith(("~$", ".")):
            continue
        broker = broker_of(f.name)
        m = re.match(r"(20\d{2}-\d{2}-\d{2})_", f.name)
        if not broker or not m:
            continue
        date = dt.date.fromisoformat(m.group(1))
        rid = f"{m.group(1)}_HSN_VesselValuations" if broker == "hsn" else f.name
        groups.setdefault(rid, Report(rid, broker, date)).files.append(f)
    for r in groups.values():
        r.files.sort(key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p.stem)])
    return sorted(groups.values(), key=lambda r: (r.report_date, r.report_id))


def load_register(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def save_register(path: Path, rows: List[Dict[str, str]]) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=REGISTER_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in REGISTER_COLUMNS})
    tmp.replace(path)


def seed_register(reports: List[Report], typed_sources: set) -> List[Dict[str, str]]:
    """First run only: reports whose every file name already appears in the data's source_file column are 'typed in M1'."""
    rows = []
    for r in reports:
        if all(f.name in typed_sources for f in r.files):
            rows.append({"report_id": r.report_id, "broker": r.broker, "report_date": r.report_date.isoformat(),
                         "files": r.file_names, "fingerprint": r.fingerprint, "status": "typed in M1"})
    return rows


def new_reports(reports: List[Report], register: List[Dict[str, str]]) -> List[Report]:
    known = {row["fingerprint"] for row in register}
    return [r for r in reports if r.fingerprint not in known]
