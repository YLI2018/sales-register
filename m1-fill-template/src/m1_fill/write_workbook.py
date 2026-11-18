"""Write checked data and the case into a copy of the blank template.

Rules (docs/adr/0002-write-input-columns-only.md):
- the blank template is opened read-only and never saved;
- only the input columns listed in the contract are written; formula columns are never touched;
- an existing output file is never overwritten;
- the saved workbook is set to recalculate fully when Excel opens it.
"""
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional

import openpyxl

from .charts import restore_charts
from .contract import (CASE_FIELDS, CASE_SHEET, PRICE_FIELDS, PRICES_FIRST_ROW, PRICES_LAST_ROW, PRICES_SHEET,
                       SALES_FIELDS, SALES_FIRST_ROW, SALES_LAST_ROW, SALES_SHEET)


class TemplateError(Exception):
    """The file given as template is not a blank M1 template."""


def check_blank_template(wb) -> None:
    """Make sure the workbook is the blank template: expected sheets present and no data in the input areas."""
    needed = {"Start Here", "Inputs", "Outputs", "Parameters", SALES_SHEET, PRICES_SHEET, "Benchmarks", "Age Curve"}
    missing = needed - set(wb.sheetnames)
    if missing:
        raise TemplateError(f"template is missing sheets: {', '.join(sorted(missing))}")
    sr, ip = wb[SALES_SHEET], wb[PRICES_SHEET]
    if any(sr[f"C{r}"].value not in (None, "") for r in range(SALES_FIRST_ROW, SALES_LAST_ROW + 1)):
        raise TemplateError("template already holds sales data; use the blank template")
    if any(ip[f"A{r}"].value not in (None, "") for r in range(PRICES_FIRST_ROW, PRICES_LAST_ROW + 1)):
        raise TemplateError("template already holds broker values; use the blank template")
    for f in SALES_FIELDS:   # the input columns must not contain formulas in the blank template
        v = sr[f"{f.column}{SALES_FIRST_ROW}"].value
        if isinstance(v, str) and v.startswith("="):
            raise TemplateError(f"{SALES_SHEET} column {f.column} holds formulas; contract and template do not match")


def write_rows(ws, fields, rows: List[Dict[str, object]], first_row: int) -> None:
    """Write rows into the input columns, one row per record, starting at first_row. Styles stay as in the template."""
    for i, rec in enumerate(rows):
        r = first_row + i
        for f in fields:
            ws[f"{f.column}{r}"].value = rec.get(f.name)


def fill(template: Path, sales: List[Dict], prices: List[Dict], case: Optional[Dict], out_path: Path) -> Path:
    """Create out_path: a copy of the blank template with the data and the case written in. Returns out_path."""
    if out_path.exists():
        raise FileExistsError(f"{out_path} already exists; outputs are never overwritten")
    wb = openpyxl.load_workbook(template)
    check_blank_template(wb)
    write_rows(wb[SALES_SHEET], SALES_FIELDS, sales, SALES_FIRST_ROW)
    write_rows(wb[PRICES_SHEET], PRICE_FIELDS, prices, PRICES_FIRST_ROW)
    if case:
        ws = wb[CASE_SHEET]
        for f in CASE_FIELDS:
            ws[f.column].value = case.get(f.name)
    wb.calculation.fullCalcOnLoad = True
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    restore_charts(template, out_path)
    return out_path


def output_name(case: Optional[Dict], now: Optional[dt.datetime] = None) -> str:
    """File name for a filled workbook: M1_<case id>_<YYYY-MM-DD_HHMMSS>.xlsx."""
    now = now or dt.datetime.now()
    cid = (case or {}).get("case_id") or "nocase"
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(cid))
    return f"M1_{safe}_{now:%Y-%m-%d_%H%M%S}.xlsx"
