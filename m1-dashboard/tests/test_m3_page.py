"""M3 Acquisition and finance page, on a small made-up M3 results file (no real data needed)."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from m1_dash import m3
from m1_dash.inputs import InputError
from test_dashboard import write_run
from m1_dash.__main__ import main


def write_m3(folder: Path, name="M3_results_2026-05-22_v3.json", **over):
    folder.mkdir(parents=True, exist_ok=True)
    res = lambda v: {"value": v, "meaning": "", "where": ""}  # noqa: E731
    j = {"schema": "m3-results/1", "made": "2026-11-18 16:00",
         "model": {"file": "M3_Model_v3.xlsx", "version": "v3", "sha256": "ab" * 32, "file_saved": "2026-11-18 15:34",
                   "spec": "Spec.docx"},
         "case": {"description": "Test <ship>", "base_date": "2026-05-22", "price_tested_musd": 28.45,
                  "employment": "Time charter", "hold_years": 2},
         "data_used": [{"what": "Curve", "source": "Made-up"}],
         "inputs": {"I_Hurdle": res(0.11), "I_Min_DSCR": res(1.2), "I_MVC": res(1.3), "I_LTV": res(0.6)},
         "results": {"R_Eq_IRR": res(-0.08), "R_Max_Bid": res(22.22), "R_Bid_Binding": res("Return (required return)"),
                     "R_Min_DSCR": res(1.14), "R_Cov_Headroom": res(0.337), "R_Max_Fall": res(0.252),
                     "R_Bid_IRR": res(22.22), "R_Bid_Cov": res(38), "R_Bid_DSCR": res(27),
                     "R_Model_OK": res("PASS"), "R_Bank_OK": res("FAIL – 1 rule(s) broken at this price"),
                     "R_Data_OK": res("2 placeholder(s)"), "R_Deal_OK": res("NO – equity IRR -8.0% vs 11.0%")},
         "by_year": {"years": [0, 1, 2], "Operating cash after carbon": [0, 5.456, 4.1],
                     "Cash to / from our equity": [-12.693, 2.836, 9.0], "Debt service cover": [None, 2.08, 1.14]},
         "sensitivities": {"A_equity_irr_hire_x_sale": {"columns": [-0.2, 0, 0.2], "rows": [-2000, 0, 2000],
                                                         "values": [["n/a", -0.18, -0.1], [-0.17, -0.08, 0.12],
                                                                    [-0.05, 0.01, 0.06]]}}}
    j.update(over)
    (folder / name).write_text(json.dumps(j), encoding="utf-8")
    return folder / name


class M3Page(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_reads_newest_file(self):
        write_m3(self.tmp / "m3", "M3_results_2026-05-22_v2.json")
        newest = write_m3(self.tmp / "m3")
        self.assertEqual(m3.read_m3(self.tmp / "m3")["_file"], newest.name)
        self.assertIsNone(m3.read_m3(None))

    def test_bad_inputs_give_clear_errors(self):
        (self.tmp / "empty").mkdir()
        with self.assertRaises(InputError):
            m3.read_m3(self.tmp / "empty")
        with self.assertRaises(InputError):
            m3.read_m3(write_m3(self.tmp / "m3", schema="other/9"))

    def test_page_content(self):
        html = m3.page(m3.read_m3(write_m3(self.tmp / "m3")))
        for text in ("-8.0%", "$22.22m", "1.14×", "33.7%", "Return (required return)", "abababababababab",
                     "Owners&#x27; cash", "n/a", "Test &lt;ship&gt;"):
            self.assertIn(text, html)
        self.assertNotIn("<ship>", html)
        self.assertIn('style="font-weight:700" data-tip="Hire +0 $/day, sale +20%', html)   # 12% meets 11%

    def test_warning_verdict_shown_as_warning(self):
        f = write_m3(self.tmp / "m3")
        import json as _j
        j = _j.loads(f.read_text()); j["results"]["R_Model_OK"]["value"] = "PASS with 1 warning(s) – see the checks marked WARN"
        f.write_text(_j.dumps(j))
        html = m3.page(m3.read_m3(f))
        self.assertIn('status warning"><b>!</b>Warning</span><span>Model works', html)

    def test_dashboard_with_m3_page(self):
        write_run(self.tmp / "results" / "M1_calc_2026-11-05_235135")
        write_m3(self.tmp / "m3")
        out = self.tmp / "out"
        self.assertEqual(main(["--results", str(self.tmp / "results"), "--m3", str(self.tmp / "m3"), "--out", str(out)]), 0)
        html = next(out.glob("M1_Dashboard_*.html")).read_text(encoding="utf-8")
        self.assertIn('id="p-m3"', html)
        self.assertIn('href="#m3"', html)
        self.assertIn("$22.22m", html)
        self.assertNotRegex(html, r"https?://")

    def test_dashboard_without_m3_still_works(self):
        write_run(self.tmp / "results" / "M1_calc_2026-11-05_235135")
        out = self.tmp / "out"
        self.assertEqual(main(["--results", str(self.tmp / "results"), "--out", str(out)]), 0)
        self.assertIn("Run with --m3", next(out.glob("M1_Dashboard_*.html")).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
