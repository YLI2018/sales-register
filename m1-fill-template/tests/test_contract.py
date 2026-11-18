"""Checks of the data contract and of reading the input files (no data folder needed)."""
import csv
import json
import re
import tempfile
import unittest
from pathlib import Path

from m1_fill.contract import PRICE_FIELDS, SALES_FIELDS, CASE_FIELDS, Field
from m1_fill.read_data import parse_value, read_case, read_prices, read_sales

ROOT = Path(__file__).resolve().parents[1]

GOOD_SALE = {"id": "1", "report_date": "2026-05-22", "vessel": "Test Ship", "segment": "MR", "dwt": "50000",
             "built": "2012", "price_musd": "28.45", "sale_type": "Secondhand", "source_file": "x.pdf"}
GOOD_PRICE = {"report_date": "2026-05-22", "broker": "Advanced Shipping", "segment": "MR", "age": "15 years",
              "value_musd": "28.5", "source_file": "x.pdf"}


def write_csv(folder: Path, name: str, fields, rows):
    path = folder / name
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[f.name for f in fields])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


class ParseValue(unittest.TestCase):
    def test_decimal_dot(self):
        self.assertEqual(parse_value("28.45", Field("p", "I", "float"))[0], 28.45)

    def test_decimal_comma_rejected_with_hint(self):
        value, err = parse_value("28,45", Field("p", "I", "float"))
        self.assertIsNone(value)
        self.assertIn("dot as decimal mark", err)

    def test_date_format(self):
        self.assertIsNone(parse_value("22/05/2026", Field("d", "B", "date"))[0])
        self.assertEqual(parse_value("2026-05-22", Field("d", "B", "date"))[0].year, 2026)

    def test_choice(self):
        f = Field("s", "D", "choice", choices=("MR", "LR2"))
        self.assertEqual(parse_value("MR", f)[0], "MR")
        self.assertIn("not allowed", parse_value("mr", f)[1])

    def test_limits(self):
        self.assertIn("outside", parse_value("2045", Field("b", "F", "int", limits=(1950, 2035)))[1])

    def test_blank_is_none(self):
        self.assertEqual(parse_value("  ", Field("x", "A", "int")), (None, None))


class ReadFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_good_files(self):
        s = read_sales(write_csv(self.tmp, "sales.csv", SALES_FIELDS, [GOOD_SALE]))
        p = read_prices(write_csv(self.tmp, "indicative_prices.csv", PRICE_FIELDS, [GOOD_PRICE]))
        self.assertEqual((s.errors, p.errors), ([], []))
        self.assertEqual(s.rows[0]["price_musd"], 28.45)

    def test_missing_column(self):
        path = self.tmp / "sales.csv"
        path.write_text("id,vessel\n1,A\n", encoding="utf-8")
        self.assertIn("missing columns", read_sales(path).errors[0])

    def test_required_value(self):
        bad = dict(GOOD_SALE, vessel="")
        errs = read_sales(write_csv(self.tmp, "sales.csv", SALES_FIELDS, [bad])).errors
        self.assertTrue(any("vessel: required" in e for e in errs))

    def test_duplicate_id(self):
        errs = read_sales(write_csv(self.tmp, "sales.csv", SALES_FIELDS, [GOOD_SALE, dict(GOOD_SALE, vessel="B")])).errors
        self.assertTrue(any("already used" in e for e in errs))

    def test_approximate_price_is_warning_not_error(self):
        res = read_sales(write_csv(self.tmp, "sales.csv", SALES_FIELDS, [dict(GOOD_SALE, price_musd="")]))
        self.assertEqual(res.errors, [])
        self.assertTrue(any("price_musd: empty" in w for w in res.warnings))

    def test_decision_without_reason_warns(self):
        res = read_sales(write_csv(self.tmp, "sales.csv", SALES_FIELDS, [dict(GOOD_SALE, reviewed_decision="Yes")]))
        self.assertTrue(any("without a reason" in w for w in res.warnings))

    def test_duplicate_broker_value_warns(self):
        res = read_prices(write_csv(self.tmp, "indicative_prices.csv", PRICE_FIELDS, [GOOD_PRICE, GOOD_PRICE]))
        self.assertTrue(any("Duplicate" in w for w in res.warnings))

    def test_capacity(self):
        rows = [dict(GOOD_SALE, id=str(i), vessel=f"S{i}") for i in range(1, 302)]
        errs = read_sales(write_csv(self.tmp, "sales.csv", SALES_FIELDS, rows)).errors
        self.assertTrue(any("template holds 300" in e for e in errs))

    def test_example_case_is_valid(self):
        res = read_case(ROOT / "examples" / "case_target_ship_1.json")
        self.assertEqual(res.errors, [])
        self.assertEqual(res.rows[0]["target_name"], "Target Ship 1")

    def test_case_bad_segment(self):
        path = self.tmp / "case.json"
        data = json.loads((ROOT / "examples" / "case_target_ship_1.json").read_text())
        data["segment"] = "Tanker"
        path.write_text(json.dumps(data))
        self.assertTrue(any("segment" in e for e in read_case(path).errors))


class DocsMatchContract(unittest.TestCase):
    def test_every_field_is_documented(self):
        doc = (ROOT / "docs" / "data_dictionary.md").read_text(encoding="utf-8")
        for f in SALES_FIELDS + PRICE_FIELDS + CASE_FIELDS:
            self.assertRegex(doc, r"`" + re.escape(f.name) + r"`", f"{f.name} missing from data_dictionary.md")


if __name__ == "__main__":
    unittest.main()
