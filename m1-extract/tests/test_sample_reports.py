"""Checks on the three SYNTHETIC sample reports in data/sample (made-up ships; layouts copied from the real reports).

These run anywhere, with no private data. The real reports are checked by a private test that is not in this repository.
To remake the samples: .venv/bin/python data/sample/make_sample_reports.py
"""
import csv
import datetime as dt
import unittest
from pathlib import Path

import pdfplumber

from m1_extract import readers

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample"


def expected(name):
    with open(SAMPLE / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def as_text(v):
    """Compare as the CSV writes it: empty for None, plain numbers, ISO dates."""
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


class SampleReports(unittest.TestCase):
    def read(self, name, reader):
        with pdfplumber.open(SAMPLE / name) as pdf:
            return reader(pdf, name, dt.date.fromisoformat(name[:10]))

    def same_rows(self, got, want_file):
        want = expected(want_file)
        self.assertEqual([g["vessel"] for g in got], [w["vessel"] for w in want], "ships found, in table order")
        for g, w in zip(got, want):
            for field, value in w.items():
                if field == "price_musd" and value:
                    self.assertAlmostEqual(g[field], float(value), places=4, msg=f"{w['vessel']}: {field}")
                else:
                    self.assertEqual(as_text(g[field]), value, f"{w['vessel']}: {field}")

    def test_advanced_layout(self):
        sales, values = self.read("2026-01-09_AdvancedShipping_Market_wk02_SYNTHETIC.pdf", readers.read_advanced)
        self.same_rows(sales, "expected_advanced_sales.csv")
        want = expected("expected_advanced_values.csv")
        self.assertEqual([{k: as_text(v[k]) for k in want[0]} for v in values],
                         [{k: f"{float(w[k]):g}" if k.endswith("musd") else w[k] for k in w} for w in want])

    def test_xclusiv_layout(self):
        sales, _ = self.read("2026-01-12_Xclusive_SalesPurchase_wk03_SYNTHETIC.pdf", readers.read_xclusiv)
        self.same_rows(sales, "expected_xclusiv_sales.csv")

    def test_intermodal_layout(self):
        sales, _ = self.read("2026-01-14_intermodal-report-wk02_SYNTHETIC.pdf", readers.read_intermodal)
        self.same_rows(sales, "expected_intermodal_sales.csv")


if __name__ == "__main__":
    unittest.main()
