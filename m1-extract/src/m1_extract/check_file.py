"""The check file: an Excel workbook in which a person approves or rejects each row read from the reports.

Sheets: 'How to check' (instructions), 'Sales' and 'Broker values'. Each row shows what was read, where it came from
(report and page), what to check (warnings), whether it is already in the data, and a Decision cell (OK or Reject,
chosen from a list). Cells can be corrected before writing OK. It is an .xlsx file, so Excel keeps dates intact.
House style: black and grey only.
"""
import datetime as dt
from pathlib import Path
from typing import Dict, List, Tuple

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from .data_files import SALES_COLUMNS, VALUE_COLUMNS

HEAD_FILL, HEAD_FONT = PatternFill("solid", fgColor="404040"), Font(bold=True, color="FFFFFF")
GREY = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
INFO = ["Decision", "Suggestion", "What to check", "Already in data", "Report", "Page"]
SALE_FIELDS = [c for c in SALES_COLUMNS if c != "id"]


def _suggest(warnings: List[str], dup: str) -> str:
    if dup.startswith("in this file"):
        return "Reject (repeat of a row above)"
    if dup:
        return "Reject (already in data)"
    serious = [w for w in warnings if "worked out from DWT" not in w and "read from an image" not in w and w != "no exact price"]
    return "Check" if serious or any("image" in w for w in warnings) else "OK"


def write(path: Path, sales: List[Dict], values: List[Dict], summary: List[str]) -> Path:
    wb = openpyxl.Workbook()
    h = wb.active
    h.title = "How to check"
    lines = ["How to check this file",
             "1. Go through the 'Sales' and 'Broker values' sheets. Each row was read from a broker report.",
             "2. Clear rows are decided already: 'Decision' says OK, or Reject for rows already in the data or repeated.",
             "   Change any of them if you disagree. Approximate prices stay without a price (as in M1).",
             "3. Rows with an empty 'Decision' need you: read 'What to check' (open the report at the page shown),",
             "   correct cells if needed, and choose OK (add to the data) or Reject (leave out).",
             "   Sister ships sold together (en bloc): the package price is already split equally; check it in the report.",
             "4. Save the file (keep it .xlsx, keep the file name), close it, then run 'Add checked rows'.",
             "Every row needs a decision; nothing is added until all rows are decided.",
             ""] + summary
    for i, t in enumerate(lines, start=1):
        h.cell(i, 1, t).font = Font(bold=(i == 1), size=14 if i == 1 else 11)
    h.column_dimensions["A"].width = 120
    for title, rows, fields in (("Sales", sales, SALE_FIELDS), ("Broker values", values, VALUE_COLUMNS)):
        ws = wb.create_sheet(title)
        cols = INFO + fields
        for j, c in enumerate(cols, start=1):
            cell = ws.cell(1, j, c)
            cell.fill, cell.font, cell.border = HEAD_FILL, HEAD_FONT, BOX
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        for i, r in enumerate(rows, start=2):
            hint = _suggest(r["_warnings"], r.get("_dup", ""))
            # Clear cases are decided already (OK, or Reject for repeats); only 'Check' rows are left for a person.
            decision = "OK" if hint == "OK" else ("Reject" if hint.startswith("Reject") else "")
            info = [decision, hint, "; ".join(r["_warnings"]), r.get("_dup", ""),
                    r.get("source_file"), r.get("_page")]
            for j, v in enumerate(info + [r.get(f) for f in fields], start=1):
                cell = ws.cell(i, j, v)
                cell.border = BOX
                if 2 <= j <= 6:
                    cell.fill = GREY
                if isinstance(v, (dt.date, dt.datetime)):
                    cell.number_format = "yyyy-mm-dd"
        dv = DataValidation(type="list", formula1='"OK,Reject"', allow_blank=True)
        ws.add_data_validation(dv)
        if rows:
            dv.add(f"A2:A{len(rows) + 1}")
        widths = {"Decision": 9, "Suggestion": 22, "What to check": 40, "Already in data": 34, "Report": 30, "Page": 6,
                  "vessel": 22, "notes": 50, "features": 28, "shipyard": 20, "buyer": 20, "basis": 40, "source_file": 30}
        for j, c in enumerate(cols, start=1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = widths.get(c, 12)
        ws.freeze_panes = "B2"
        ws.auto_filter.ref = f"A1:{openpyxl.utils.get_column_letter(len(cols))}{max(len(rows) + 1, 1)}"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def read(path: Path) -> Tuple[List[Dict], List[Dict], List[str]]:
    """Rows marked OK in a checked file, and problems: rows without a decision, or a decision other than OK / Reject."""
    wb = openpyxl.load_workbook(path)
    out, problems = {}, []
    for title, fields in (("Sales", SALE_FIELDS), ("Broker values", VALUE_COLUMNS)):
        ws = wb[title]
        head = [c.value for c in ws[1]]
        rows = []
        for i, values in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            rec = dict(zip(head, values))
            if all(v in (None, "") for v in values):
                continue
            decision = (rec.get("Decision") or "").strip()
            if decision not in ("OK", "Reject"):
                problems.append(f"{title} row {i} ({rec.get('vessel') or rec.get('segment') or ''}): Decision is "
                                f"'{decision or 'empty'}'; choose OK or Reject")
                continue
            if decision == "OK":
                r = {f: rec.get(f) for f in fields}
                for f, v in r.items():
                    if isinstance(v, str):
                        r[f] = v.strip() or None
                if isinstance(r.get("report_date"), dt.datetime):
                    r["report_date"] = r["report_date"].date()
                if isinstance(r.get("next_survey"), dt.datetime):
                    r["next_survey"] = r["next_survey"].date()
                r["_row"] = i
                rows.append(r)
        out[title] = rows
    return out["Sales"], out["Broker values"], problems
