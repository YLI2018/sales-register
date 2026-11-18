"""Build the blank template (formulas, no data) from the full M1 template.

usage: python3 scripts/make_blank_template.py FULL_TEMPLATE.xlsx templates/M1_Comparable_Sales_Template_v1_blank.xlsx

Keeps the 8 M1 sheets only (docs/adr/0003-blank-template-holds-m1-sheets-only.md), clears every input column
listed in the data contract, clears the case on Inputs and the case log, and restores the original charts.
The full template is opened read-only and is not changed.
"""
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from m1_fill.charts import restore_charts  # noqa: E402
from m1_fill.contract import (CASE_FIELDS, PRICE_FIELDS, PRICES_FIRST_ROW, PRICES_LAST_ROW, SALES_FIELDS,  # noqa: E402
                              SALES_FIRST_ROW, SALES_LAST_ROW)

M1_SHEETS = ["Start Here", "Inputs", "Outputs", "Parameters", "Sales Register", "Indicative Prices", "Benchmarks", "Age Curve"]


def main(src: Path, out: Path) -> None:
    if out.exists():
        raise SystemExit(f"{out} exists; delete it first if you really want to rebuild it")
    wb = openpyxl.load_workbook(src)
    for name in [n for n in wb.sheetnames if n not in M1_SHEETS]:
        del wb[name]
    sr, ip = wb["Sales Register"], wb["Indicative Prices"]
    for r in range(SALES_FIRST_ROW, SALES_LAST_ROW + 1):
        for f in SALES_FIELDS:
            sr[f"{f.column}{r}"].value = None
    for r in range(PRICES_FIRST_ROW, PRICES_LAST_ROW + 1):
        for f in PRICE_FIELDS:
            ip[f"{f.column}{r}"].value = None
    for f in CASE_FIELDS:
        wb["Inputs"][f.column].value = None
    for c in range(2, 18):          # case log: keep the header and the 'current case' row, clear logged cases
        wb["Outputs"].cell(46, c).value = None
    h = wb["Start Here"]
    h["B2"] = "Ship valuation model – personal portfolio project. Blank template v1 (formulas, no data). Filled by m1-fill-template."
    h["C8"] = "Owner: model owner. Changes to formulas or Parameters are recorded in the Parameters change log."
    wb["Parameters"]["G44"] = "Model owner"
    sr["R4"] = "Notes"
    for r in range(21, 31):
        if h.cell(r, 2).value == "Other sheets":
            h.cell(r, 2).value = None; h.cell(r, 3).value = None
    wb.calculation.fullCalcOnLoad = True
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    n = restore_charts(src, out)
    print(f"blank template written: {out} ({len(wb.sheetnames)} sheets, {n} charts restored)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
