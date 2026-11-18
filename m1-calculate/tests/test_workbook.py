"""Checks of results.xlsx (no data folder needed): sheets, numbers, Excel check formulas and chart."""
import datetime as dt
import math
import tempfile
import unittest
from pathlib import Path

import openpyxl

from m1_calc.engine import value_ship
from m1_calc.inputs import BrokerValue, Ship
from m1_calc.workbook import FIRST_ROW, write_workbook
from test_engine import P, sale

D = dt.date


class Workbook(unittest.TestCase):
    def setUp(self):
        day = D(2026, 5, 22)
        values = [BrokerValue(day, "Broker A", "MR", a, v) for a, v in (("5 years", 50), ("10 years", 40), ("15 years", 30))]
        sales = [sale(id=i, vessel=f"S{i}", built=2026 - age, price_musd=round(90 * math.exp(-0.08 * age) * f, 2))
                 for i, (age, f) in enumerate(((6, 1.02), (9, 0.97), (12, 1.01), (15, 0.99), (18, 1.03), (20, 0.98)), start=1)]
        self.results = [value_ship(Ship("T1", "Target ship", "MR", 50000, 2012, day, 30.0), sales, values, {"MR": P}),
                        value_ship(Ship("T2", "S3", "MR", 50000, 2014, day), sales, values, {"MR": P})]
        self.path = write_workbook(self.results, Path(tempfile.mkdtemp()) / "results.xlsx")

    def test_sheets(self):
        wb = openpyxl.load_workbook(self.path)
        self.assertEqual(wb.sheetnames, ["Results", "Curve T1", "Curve T2"])

    def test_numbers_and_checks(self):
        ws = openpyxl.load_workbook(self.path)["Curve T1"]
        r = self.results[0]
        self.assertAlmostEqual(ws["B7"].value, r.curve.a_musd)
        self.assertAlmostEqual(ws["B8"].value, r.curve.b)
        self.assertAlmostEqual(ws["B12"].value, r.value_musd)
        self.assertTrue(ws["C8"].value.startswith("=SLOPE("))
        self.assertEqual(ws.cell(FIRST_ROW, 9).value, f"=LN(H{FIRST_ROW})")
        self.assertEqual(sum(1 for row in range(FIRST_ROW, FIRST_ROW + 10) if ws.cell(row, 1).value), r.n_comparables)

    def test_chart_present(self):
        ws = openpyxl.load_workbook(self.path)["Curve T1"]
        self.assertEqual(len(ws._charts), 1)


if __name__ == "__main__":
    unittest.main()
