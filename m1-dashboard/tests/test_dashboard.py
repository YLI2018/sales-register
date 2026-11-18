"""Tests on a small made-up Calculate output (no real data needed)."""
import csv
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from m1_dash import charts, page, roadmap
from m1_dash.__main__ import main
from m1_dash.inputs import InputError, latest_run, read_database, read_run

RESULT_COLS = ["case_id", "target_name", "segment", "valuation_date", "target_age", "value_musd", "range_low_musd",
               "range_high_musd", "loss_rate", "a_musd", "b", "r_squared", "n_comparables", "sd_residuals_musd",
               "near_age_average_musd", "near_age_count", "known_price_musd", "known_gap_pct", "valuation_benchmark_date",
               "parameters_status", "status", "failed_checks", "message"]
COMP_COLS = ["case_id", "sale_id", "vessel", "report_date", "age_at_sale", "price_musd", "benchmark_date",
             "days_to_benchmark", "benchmark_age", "index_factor", "adjusted_price_musd", "log_price", "age_gap",
             "log_price_gap", "fitted_price_musd", "residual_musd", "decision_source"]


def write_run(folder: Path):
    folder.mkdir(parents=True)
    with (folder / "results.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(RESULT_COLS)
        w.writerow(["VAL-001", "Test Ship", "MR", "2026-05-22", "14", "29.62", "26.67", "32.57", "0.0809", "96.44", "-0.0843",
                    "0.94", "3", "2.95", "29.5", "2", "28.45", "-0.04", "2026-05-22", "Validated", "VALID", "", ""])
        w.writerow(["VAL-002", "Other <Ship>", "MR", "2026-05-22", "14", "29.49", "26.45", "32.52", "0.0808", "95.96",
                    "-0.0843", "0.94", "3", "3.0", "29.5", "2", "", "", "2026-05-22", "Validated",
                    "NOT VALID: see failed checks", "Review rows decided", "5 sales need a reviewed decision"])
    with (folder / "comparables.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COMP_COLS)
        for case in ("VAL-001", "VAL-002"):
            for i, (age, price) in enumerate(((10, 41.0), (15, 27.5), (18, 21.0)), start=1):
                w.writerow([case, i, f"Comp {i}", "2026-05-22", age, price, "2026-05-22", 0, "15 years", 1.0, price,
                            "", "", "", "", "", "Reviewed"])
    (folder / "run.log").write_text("m1_calc 0.2.1\nrun: 2026-11-05 23:51:35\nsales: 308; broker values: 427; ships: 2\n")


class Dashboard(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.results = self.tmp / "results"
        write_run(self.results / "M1_calc_2026-11-01_100000")
        write_run(self.results / "M1_calc_2026-11-05_235135")
        self.clean = self.tmp / "clean"
        self.clean.mkdir()
        (self.clean / "sales.csv").write_text("id,report_date,vessel,segment\n1,2026-02-09,A,MR\n2,2026-02-09,B,MR\n"
                                              "3,2026-10-31,C,Handysize\n4,bad-date,D,MR\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_newest_run_and_reading(self):
        run = latest_run(self.results)
        self.assertEqual(run.name, "M1_calc_2026-11-05_235135")
        info, ships = read_run(run)
        self.assertEqual((info.sales, info.broker_values, info.version), (308, 427, "m1_calc 0.2.1"))
        self.assertEqual([s.status_kind for s in ships], ["good", "critical"])
        self.assertEqual(ships[1].failed_checks, ["Review rows decided"])
        self.assertEqual(len(ships[0].comparables), 3)

    def test_database_skips_unreadable_rows(self):
        rows = read_database(self.clean)
        self.assertEqual(len(rows), 3)
        self.assertIsNone(read_database(None) or None)

    def test_missing_inputs_give_clear_errors(self):
        with self.assertRaises(InputError):
            latest_run(self.tmp / "nowhere")
        self.assertEqual(main(["--results", str(self.tmp / "nowhere"), "--out", str(self.tmp / "out")]), 2)
        self.assertFalse((self.tmp / "out").exists())

    def test_dashboard_written_with_four_pages(self):
        out = self.tmp / "out"
        self.assertEqual(main(["--results", str(self.results), "--data", str(self.clean), "--out", str(out)]), 0)
        files = list(out.glob("M1_Dashboard_*.html"))
        self.assertEqual(len(files), 1)
        html = files[0].read_text(encoding="utf-8")
        for pid in ("p-overview", "p-ship", "p-database", "p-roadmap"):
            self.assertIn(f'id="{pid}"', html)
        self.assertIn("$29.62m", html)
        self.assertIn("Other &lt;Ship&gt;", html)                     # names are escaped
        self.assertNotIn("<Ship>", html)
        self.assertIn("5 sales need a reviewed decision", html)
        self.assertNotRegex(html, r"https?://")                       # works offline: no outside links or scripts

    def test_failed_check_is_marked(self):
        _, ships = read_run(latest_run(self.results))
        panel = page.ship_panel(ships[1])
        self.assertRegex(panel, r'class="status critical"><b>✕</b>Fail</span>Review rows decided')
        self.assertEqual(panel.count('class="status good"'), len(page.CHECKS) - 1)

    def test_age_curve_points_and_target(self):
        _, ships = read_run(latest_run(self.results))
        svg = charts.age_curve(ships[0])
        self.assertEqual(svg.count('class="dot"'), 3)
        self.assertEqual(svg.count('class="target"'), 1)
        self.assertIn("Test Ship: $29.62m", svg)

    def test_round_axis_steps(self):
        self.assertEqual(charts.nice_max(323), 400)
        self.assertEqual(charts.ticks(400), [0, 100, 200, 300, 400])
        self.assertEqual(charts.ticks(40), [0, 10, 20, 30, 40])

    def test_roadmap_links_point_to_known_models(self):
        for a, b, *_ in roadmap.LINKS:
            self.assertIn(a, roadmap.MODELS)
            self.assertIn(b, roadmap.MODELS)
        self.assertEqual(len(re.findall(r'class="rm-node', roadmap.diagram())), len(roadmap.MODELS))

    def test_automation_page(self):
        out = self.tmp / "out"
        self.assertEqual(main(["--results", str(self.results), "--data", str(self.clean), "--out", str(out)]), 0)
        html = next(out.glob("M1_Dashboard_*.html")).read_text(encoding="utf-8")
        self.assertIn('id="p-automation"', html)
        self.assertIn('href="#automation"', html)
        for project in ("m1-report-download", "m1-extract", "m1-fill-template", "m1-calculate", "m1-dashboard"):
            self.assertIn(project, html)

    def test_unused_model_is_dashed(self):
        svg = roadmap.diagram()
        self.assertIn('class="rm-node unused"', svg)          # VE: built, not used in this case
        self.assertIn('class="rm-edge dashed"', svg)
        self.assertTrue(roadmap.MODELS["M5"][2].startswith("Built"))   # M5 = this dashboard, built
        self.assertNotIn("not used", roadmap.MODELS["M5"][2])           # and not drawn like VE


if __name__ == "__main__":
    unittest.main()
