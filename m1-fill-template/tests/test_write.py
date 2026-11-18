"""Checks of writing into the blank template (no data folder needed)."""
import datetime as dt
import tempfile
import unittest
from pathlib import Path

import openpyxl

from m1_fill.charts import chart_parts
from m1_fill.contract import SALES_FIELDS
from m1_fill.write_workbook import TemplateError, fill, output_name

ROOT = Path(__file__).resolve().parents[1]
BLANK = ROOT / "templates" / "M1_Comparable_Sales_Template_v1_blank.xlsx"

SALE = {f.name: None for f in SALES_FIELDS}
SALE.update(id=1, report_date=dt.datetime(2026, 5, 22), vessel="Test Ship", segment="MR", dwt=50000, built=2012,
            price_musd=28.45, sale_type="Secondhand", source_file="x.pdf")
PRICE = {"report_date": dt.datetime(2026, 5, 22), "broker": "Advanced Shipping", "segment": "MR", "age": "15 years",
         "value_musd": 28.5, "source_file": "x.pdf"}
CASE = {"case_id": "T-1", "purpose": "Back-test", "target_name": "Test Ship", "segment": "MR", "dwt": 50000,
        "year_built": 2012, "valuation_date": dt.datetime(2026, 5, 22), "use_reviewed_decisions": "Yes"}


class Fill(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp()) / "out.xlsx"

    def test_blank_template_is_blank(self):
        wb = openpyxl.load_workbook(BLANK)
        self.assertIsNone(wb["Sales Register"]["C5"].value)
        self.assertIsNone(wb["Indicative Prices"]["A5"].value)

    def test_values_written_and_formulas_untouched(self):
        before = openpyxl.load_workbook(BLANK)["Sales Register"]
        fill(BLANK, [SALE], [PRICE], CASE, self.out)
        wb = openpyxl.load_workbook(self.out)
        sr = wb["Sales Register"]
        self.assertEqual(sr["C5"].value, "Test Ship")
        self.assertEqual(sr["I5"].value, 28.45)
        for col in ("M", "S", "V", "W", "AB", "AC", "AD", "AG", "AH"):     # formula columns identical to the template
            self.assertEqual(sr[f"{col}5"].value, before[f"{col}5"].value, col)
        self.assertEqual(wb["Inputs"]["C7"].value, "Test Ship")
        self.assertEqual(wb["Indicative Prices"]["F5"].value, 28.5)

    def test_charts_kept(self):
        fill(BLANK, [SALE], [PRICE], CASE, self.out)
        self.assertEqual(chart_parts(self.out), chart_parts(BLANK))
        self.assertEqual(len(chart_parts(self.out)), 2)

    def test_never_overwrites(self):
        fill(BLANK, [SALE], [PRICE], CASE, self.out)
        with self.assertRaises(FileExistsError):
            fill(BLANK, [SALE], [PRICE], CASE, self.out)

    def test_refuses_filled_workbook_as_template(self):
        fill(BLANK, [SALE], [PRICE], CASE, self.out)
        with self.assertRaises(TemplateError):
            fill(self.out, [SALE], [PRICE], CASE, self.out.with_name("again.xlsx"))

    def test_output_name(self):
        self.assertEqual(output_name({"case_id": "UM/1"}, dt.datetime(2026, 11, 5, 9, 30, 0)), "M1_UM_1_2026-11-05_093000.xlsx")


if __name__ == "__main__":
    unittest.main()
