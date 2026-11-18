"""Unit checks of each calculation step on small, made-up data (no data folder needed)."""
import datetime as dt
import math
import unittest

from m1_calc.engine import (BenchmarkTable, Comparable, adjusted_price, age_at_sale, automatic_screen, benchmark_age,
                            benchmark_table, decision_used, failed_rules, fit_curve, nearest_ok_date, value_ship)
from m1_calc.inputs import BrokerValue, Parameters, Sale, Ship

D = dt.date
P = Parameters(segment="MR", status="Validated", dwt_min=45000, dwt_max=55000, dwt_tolerance=0.01, age_min=2, age_max=20,
               benchmark_provider="Broker A", benchmark_segment="MR", benchmark_labels=["5 years", "10 years", "15 years"],
               benchmark_ages=[5, 10, 15], benchmark_max_days=7, min_comparables=3, min_r_squared=0.7, range_sd=1,
               near_age_window=1, charter_keywords=["charter", "T/C"], review_keywords=["DPP", "confirm delivered"])


def sale(**kw):
    base = dict(id=1, report_date=D(2026, 5, 22), vessel="A", segment="MR", dwt=50000, built=2012, price_musd=28.0,
                features="", en_bloc="N", sale_type="Secondhand", notes="", reviewed_decision=None)
    base.update(kw)
    return Sale(**base)


def bv(day, age, value, broker="Broker A"):
    return BrokerValue(day, broker, "MR", age, value)


class Benchmarks(unittest.TestCase):
    def test_ok_only_with_one_value_per_age(self):
        rows = [bv(D(2026, 1, 2), a, v) for a, v in (("5 years", 50), ("10 years", 40), ("15 years", 30))]
        rows += [bv(D(2026, 1, 9), "5 years", 51), bv(D(2026, 1, 9), "10 years", 41)]                   # 15 years missing
        rows += [bv(D(2026, 1, 16), a, v) for a, v in (("5 years", 52), ("10 years", 42), ("15 years", 32), ("15 years", 33))]
        rows += [bv(D(2026, 1, 2), "5 years", 99, broker="Broker B")]                                    # other provider
        self.assertEqual(benchmark_table(rows, P).ok_dates, [D(2026, 1, 2)])

    def test_nearest_date_earlier_wins_tie(self):
        bt = BenchmarkTable({D(2026, 1, 1): [1, 1, 1], D(2026, 1, 9): [1, 1, 1]})
        self.assertEqual(nearest_ok_date(D(2026, 1, 5), bt), D(2026, 1, 1))
        self.assertEqual(nearest_ok_date(D(2026, 1, 6), bt), D(2026, 1, 9))
        self.assertIsNone(nearest_ok_date(D(2026, 1, 5), BenchmarkTable({})))

    def test_benchmark_age_cut_offs(self):
        self.assertEqual([benchmark_age(a, P) for a in (5, 7.4, 7.5, 12.4, 12.5, 20)], [0, 0, 1, 1, 2, 2])

    def test_index_factor(self):
        bt = BenchmarkTable({D(2026, 3, 27): [46.5, 36.5, 25.5], D(2026, 5, 22): [50.5, 40.5, 28.5]})
        ab, k, factor, adj = adjusted_price(sale(report_date=D(2026, 3, 30), price_musd=27.6), bt, D(2026, 5, 22), P)
        self.assertEqual((ab, k), (D(2026, 3, 27), 2))
        self.assertAlmostEqual(adj, 27.6 * 28.5 / 25.5)          # the Target Ship 2 example: $30.85m
        self.assertAlmostEqual(round(adj, 2), 30.85)


class Rules(unittest.TestCase):
    def test_each_rule(self):
        self.assertEqual(failed_rules(sale(dwt=44000), P, False), ["R1"])
        self.assertEqual(failed_rules(sale(dwt=44995), P, False), [])            # within the 1% tolerance
        self.assertEqual(failed_rules(sale(sale_type="Resale"), P, False), ["R2"])
        self.assertEqual(failed_rules(sale(built=2025), P, False), ["R2"])
        self.assertEqual(failed_rules(sale(price_musd=None), P, False), ["R3"])
        self.assertEqual(failed_rules(sale(notes="sold incl. T/C"), P, False), ["R4"])
        self.assertEqual(failed_rules(sale(built=2005), P, False), ["R5"])
        self.assertEqual(failed_rules(sale(), P, True), ["R6"])
        self.assertEqual(age_at_sale(sale()), 14)

    def test_screen_and_decision(self):
        self.assertEqual(automatic_screen(sale(en_bloc="Y"), P, []), "Review")
        self.assertEqual(automatic_screen(sale(features="DPP"), P, []), "Review")
        self.assertEqual(automatic_screen(sale(), P, ["R3"]), "No")
        self.assertEqual(decision_used(sale(reviewed_decision="No"), "Yes", True), ("No", "Reviewed (Z)"))
        self.assertEqual(decision_used(sale(reviewed_decision="No"), "Yes", False), ("Yes", "Automatic (W)"))
        self.assertEqual(decision_used(sale(reviewed_decision="Target"), "Yes", True), ("Yes", "Automatic (W)"))
        self.assertEqual(decision_used(sale(), "Review", True)[0], "Review: decide in Z")


class Curve(unittest.TestCase):
    def test_exact_exponential_is_recovered(self):
        comps = [Comparable(sale(id=i), age, D(2026, 5, 22), "15 years", 1.0, 100 * math.exp(-0.08 * age), 0, "x")
                 for i, age in enumerate((5, 9, 12, 16, 20))]
        c = fit_curve(comps)
        self.assertAlmostEqual(c.a_musd, 100)
        self.assertAlmostEqual(c.b, -0.08)
        self.assertAlmostEqual(c.r_squared, 1.0)
        self.assertAlmostEqual(c.loss_rate, 1 - math.exp(-0.08))
        self.assertAlmostEqual(max(abs(x.residual_musd) for x in comps), 0.0)


class Valuation(unittest.TestCase):
    def setUp(self):
        day = D(2026, 5, 22)
        self.values = [bv(day, a, v) for a, v in (("5 years", 50), ("10 years", 40), ("15 years", 30))]
        self.sales = [sale(id=i, vessel=f"S{i}", built=2026 - age, price_musd=round(90 * math.exp(-0.08 * age) * f, 2))
                      for i, (age, f) in enumerate(((6, 1.02), (9, 0.97), (12, 1.01), (15, 0.99), (18, 1.03), (20, 0.98)), start=1)]
        self.params = {"MR": P}

    def test_valid_case(self):
        r = value_ship(Ship("T1", "Target ship", "MR", 50000, 2012, D(2026, 5, 22)), self.sales, self.values, self.params)
        self.assertEqual(r.status, "VALID")
        self.assertEqual(r.n_comparables, 6)
        self.assertLess(r.range_low_musd, r.value_musd)

    def test_nothing_after_the_valuation_date_is_used(self):
        ship = Ship("T6", "Target ship", "MR", 50000, 2012, D(2026, 5, 22))
        base = value_ship(ship, self.sales, self.values, self.params)
        later_sale = sale(id=99, vessel="Late", built=2014, price_musd=60.0, report_date=D(2026, 6, 1))
        later_values = [bv(D(2026, 5, 23), a, v) for a, v in (("5 years", 80), ("10 years", 70), ("15 years", 60))]
        r = value_ship(ship, self.sales + [later_sale], self.values + later_values, self.params)
        self.assertAlmostEqual(r.value_musd, base.value_musd)
        self.assertEqual(r.n_comparables, base.n_comparables)
        self.assertEqual(r.valuation_benchmark_date, D(2026, 5, 22))
        self.assertEqual((r.information_cutoff, r.sales_after_cutoff, r.broker_values_after_cutoff), (D(2026, 5, 22), 1, 3))

    def test_same_age_gives_no_curve_not_a_crash(self):
        same = [sale(id=i, vessel=f"A{i}", built=2014, price_musd=p) for i, p in enumerate((30.0, 31.0, 29.5), start=1)]
        r = value_ship(Ship("T5", "X", "MR", 50000, 2012, D(2026, 5, 22)), same, self.values, self.params)
        self.assertIsNone(r.value_musd)
        self.assertEqual(r.status, "NOT VALID: see failed checks")
        self.assertIn("no age curve", r.message)

    def test_target_excluded_from_its_own_comparables(self):
        r = value_ship(Ship("T2", "S3", "MR", 50000, 2014, D(2026, 5, 22)), self.sales, self.values, self.params)
        self.assertEqual(r.n_comparables, 5)

    def test_too_few_comparables_is_not_valid(self):
        r = value_ship(Ship("T3", "X", "MR", 50000, 2012, D(2026, 5, 22)), self.sales[:2], self.values, self.params)
        self.assertTrue(r.status.startswith("NOT VALID"))

    def test_unknown_segment(self):
        r = value_ship(Ship("T4", "X", "LR2", 110000, 2012, D(2026, 5, 22)), self.sales, self.values, self.params)
        self.assertTrue(r.status.startswith("NOT VALID"))


if __name__ == "__main__":
    unittest.main()
