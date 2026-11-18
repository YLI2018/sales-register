"""Command line: python3 -m m1_fill --data DATA_FOLDER --out OUTPUT_FOLDER [--case CASE.json] [--template FILE]

Exit codes: 0 = workbook written; 1 = errors in the data (nothing written); 2 = template or file problem.
A log file with the same name as the workbook (.log) lists every check, warning and count.
"""
import argparse
import sys
from pathlib import Path

from . import __version__
from .read_data import read_case, read_prices, read_sales
from .write_workbook import TemplateError, fill, output_name

DEFAULT_TEMPLATE = Path(__file__).resolve().parents[2] / "templates" / "M1_Comparable_Sales_Template_v1_blank.xlsx"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="m1_fill", description="Fill the blank M1 template with checked data and a case.")
    p.add_argument("--data", required=True, type=Path, help="folder holding sales.csv and indicative_prices.csv")
    p.add_argument("--out", required=True, type=Path, help="folder for the filled workbook and its log")
    p.add_argument("--case", type=Path, help="case JSON file (optional; without it Inputs is left blank)")
    p.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="blank template (default: templates/ in this repository)")
    p.add_argument("--check-only", action="store_true", help="run the checks and print the result; write nothing")
    a = p.parse_args(argv)

    sales = read_sales(a.data / "sales.csv")
    prices = read_prices(a.data / "indicative_prices.csv")
    case = read_case(a.case) if a.case else None
    errors = sales.errors + prices.errors + (case.errors if case else [])
    warnings = sales.warnings + prices.warnings + (case.warnings if case else [])

    lines = [f"m1_fill {__version__}",
             f"template: {a.template}",
             f"data: {a.data}",
             f"case: {a.case or 'none'}",
             f"sales rows: {len(sales.rows)}; broker value rows: {len(prices.rows)}",
             f"errors: {len(errors)}; warnings: {len(warnings)}"]
    lines += [f"ERROR   {e}" for e in errors] + [f"WARNING {w}" for w in warnings]

    if errors or a.check_only:
        print("\n".join(lines))
        print("Nothing written." if errors else "Check only: nothing written.")
        return 1 if errors else 0
    try:
        case_row = case.rows[0] if case else None
        out = fill(a.template, sales.rows, prices.rows, case_row, a.out / output_name(case_row))
    except (TemplateError, FileExistsError, FileNotFoundError, ValueError) as e:
        print("\n".join(lines)); print(f"STOPPED: {e}")
        return 2
    lines.append(f"written: {out}")
    out.with_suffix(".log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:6] + [lines[-1]]))
    if warnings:
        print(f"{len(warnings)} warnings: see {out.with_suffix('.log').name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
