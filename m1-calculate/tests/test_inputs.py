"""Checks of the input readers (no data folder needed)."""
import tempfile
import unittest
from pathlib import Path

from m1_calc.inputs import InputError, read_broker_values, read_sales, read_ships

ROOT = Path(__file__).resolve().parents[1]
SALES_HEADER = "id,report_date,vessel,segment,dwt,built,price_musd,features,en_bloc,sale_type,notes,reviewed_decision\n"


class Readers(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def write(self, name, text):
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_sales_good(self):
        s = read_sales(self.write("sales.csv", SALES_HEADER + "1,2026-05-22,A,MR,50000,2012,28.45,,N,Secondhand,,\n"))
        self.assertEqual((s[0].price_musd, s[0].built), (28.45, 2012))

    def test_comma_decimal_rejected(self):
        with self.assertRaises(InputError):
            read_sales(self.write("sales.csv", SALES_HEADER + '1,2026-05-22,A,MR,50000,2012,"28,45",,N,Secondhand,,\n'))

    def test_missing_column(self):
        with self.assertRaises(InputError):
            read_broker_values(self.write("indicative_prices.csv", "report_date,broker\n2026-05-22,X\n"))

    def test_example_ships(self):
        ships = read_ships(ROOT / "examples" / "ships_example.csv")
        self.assertEqual([s.case_id for s in ships], ["VAL-001", "VAL-002", "VAL-003", "VAL-004"])
        self.assertFalse(ships[3].use_reviewed_decisions)
        self.assertIsNone(ships[1].known_price_musd)

    def test_case_json(self):
        ships = read_ships(ROOT / "examples" / "case_target_ship_1.json")
        self.assertEqual((ships[0].target_name, ships[0].known_price_musd), ("Target Ship 1", 28.45))

    def test_duplicate_case_id(self):
        p = self.write("ships.csv", "case_id,target_name,segment,dwt,year_built,valuation_date\n"
                                    "A,X,MR,50000,2012,2026-05-22\nA,Y,MR,50000,2012,2026-05-22\n")
        with self.assertRaises(InputError):
            read_ships(p)


if __name__ == "__main__":
    unittest.main()
