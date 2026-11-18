"""Checks that need no reports: value parsing, HSN sentences, report grouping, the check file and adding rows."""
import csv
import datetime as dt
import shutil
import tempfile
import unittest
from pathlib import Path

from m1_extract import check_file, data_files
from m1_extract import normalise as N
from m1_extract.readers import _sale, link_en_bloc, parse_hsn
from m1_extract.reports import find_reports, new_reports, seed_register

D = dt.date


class Values(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual([N.size_number(x) for x in ("81.504", "158,517", "63.500", "2797", "")], [81504, 158517, 63500, 2797, None])

    def test_prices(self):
        self.assertEqual(N.price("$ 20,5m")[0], 20.5)
        self.assertEqual(N.price("$ 9,294m")[0], 9.294)
        self.assertEqual(N.price("110")[0], 110)
        for approx in ("rgn $ 40m", "high $ 24,0m", "xs $20m", "RGN 49", "low $14m"):
            value, remark = N.price(approx)
            self.assertIsNone(value, approx)
            self.assertTrue(remark.startswith("Approximate price"), approx)
        self.assertIsNone(N.price("enbloc")[0])

    def test_survey_dates(self):
        self.assertEqual(N.survey_date("02/2027"), "2027-02-01")
        self.assertEqual(N.survey_date("Feb-27"), "2027-02-01")
        self.assertIsNone(N.survey_date("MAN B&W"))

    def test_yard_and_names(self):
        self.assertEqual(N.yard_and_country("Hyundai Samho, Korea"), ("Hyundai Samho", "Korea"))
        self.assertEqual(N.yard_and_country("HYUNDAI, S. Korea"), ("Hyundai", "Korea"))
        self.assertEqual([N.ship_name(x) for x in ("DEMO NENG 16", "LS EXAMPLE", "SPP DEMO", "OM SAMPLE")],
                         ["Demo Neng 16", "LS Example", "SPP Demo", "OM Sample"])
        self.assertEqual(N.title_case("CLIENTS OF ACME"), "Clients of Acme")

    def test_segments(self):
        self.assertEqual(N.segment_from_type("MR2", "tanker"), "MR")
        self.assertEqual(N.segment_from_type("KMAX", "bulk"), "Kamsarmax")
        self.assertEqual(N.segment_from_type("Panamax", "tanker"), "Panamax tanker")
        self.assertEqual(N.segment_from_size(51319, "tanker"), "MR")
        self.assertEqual(N.segment_from_size(56141, "bulk"), "Supramax")


class HsnSentences(unittest.TestCase):
    LINES = ["Weekly Vessel Valuations Report, October 27", "2026", "Bulkers",
             "Handysize values firmed as buyers paid firm prices for modern tonnage.",
             "Ultramax Sample Queen (61.400 DWT, 2013. Northport Dock) sold by Demo Kaiun Kaisha for",
             "USD 24.0 mil, VV Value USD 23.89 mil.", "Tankers",
             "MR2 Demo Angel (50,800 DWT, 2008, Eastbay Offshore) sold by Demo Overseas Marine for USD 22.5",
             "mil, WV Value USD 21.75 mil.", "Containers",
             "Sub Panamax Example G (2,556 TEU, 2001, Hyundai Heavy Industries Ulsan) sold by Samplesea",
             "Shipping to Democo for USD 26.0 mil, VV Value USD 24.21 mil.",
             "VLCC Alpha & Beta (314,000 DWT, 2012, Hyundai) sold to Testcorp for USD 178.0 mil."]

    def test_parse(self):
        sales, _ = parse_hsn(self.LINES, [1] * len(self.LINES), "x.png", D(2026, 10, 28))
        by = {s["vessel"]: s for s in sales}
        self.assertEqual(set(by), {"Sample Queen", "Demo Angel", "Example G", "Alpha", "Beta"})
        pa = by["Demo Angel"]
        self.assertEqual((pa["segment"], pa["dwt"], pa["built"], pa["price_musd"], pa["seller"]), ("MR", 50800, 2008, 22.5, "Demo Overseas Marine"))
        self.assertEqual(pa["report_date"], D(2026, 10, 27))                  # date from the title, not the file
        self.assertIn("VesselsValue value USD 21.75m", pa["notes"])
        self.assertEqual(by["Sample Queen"]["dwt"], 61400)                   # '61.400' read as thousands
        self.assertEqual(by["Example G"]["segment"], "Container")
        self.assertIsNone(by["Example G"]["dwt"])
        self.assertEqual(by["Example G"]["buyer"], "Democo")
        for ship in ("Alpha", "Beta"):                                       # one row per sister ship, price split
            self.assertEqual((by[ship]["en_bloc"], by[ship]["price_musd"], by[ship]["buyer"]), ("Y", 89.0, "Testcorp"))


class EnBloc(unittest.TestCase):
    @staticmethod
    def row(name, dwt, price, buyer=None, bloc="N", features=None):
        r = _sale("r.pdf", D(2026, 10, 31), 3)
        r.update(vessel=name, segment="Handysize", dwt=dwt, built=2010, price_musd=price, buyer=buyer, en_bloc=bloc,
                 features=features, notes="p3")
        r["_warnings"] = [] if price is not None else ["no exact price"]
        return r

    def test_price_on_one_ship_enbloc_on_the_other(self):
        rows = link_en_bloc([self.row("Bao Shine", 32203, 13.0, "Undisclosed"),
                             self.row("Alpha Sample", 31967, 23.5, "USA based"),
                             self.row("Beta Sample", 31833, None, None, "Y", "Price given for the package (en bloc): see the partner row")])
        self.assertEqual(rows[0]["price_musd"], 13.0)                         # the ship above is not part of it
        for r in rows[1:]:
            self.assertEqual((r["price_musd"], r["buyer"], r["en_bloc"], r["features"]), (11.75, "USA based", "Y", None))
            self.assertIn("package $23.5m for Alpha Sample and Beta Sample", r["notes"])
            self.assertNotIn("no exact price", r["_warnings"])

    def test_enbloc_price_with_sister_above_and_buyer_over_two_rows(self):
        rows = link_en_bloc([self.row("Demo One", 156848, None, "Greek (Northport"),
                             self.row("Demo Two", 156657, 140.0, "Maritime)", "Y", "Price as reported: $ 140m enbloc")])
        self.assertEqual([(r["price_musd"], r["buyer"]) for r in rows], [(70.0, "Greek (Northport Maritime)")] * 2)

    def test_three_sisters_and_each(self):
        rows = link_en_bloc([self.row("A One", 50000, None), self.row("A Two", 50100, 90.0, None, "Y"),
                             self.row("A Three", 49900, None), self.row("Other", 30000, None)])
        self.assertEqual([r["price_musd"] for r in rows], [30.0, 30.0, 30.0, None])
        each = link_en_bloc([self.row("B One", 50000, 17.0, None, "Y", "Price as reported: $17m each"), self.row("B Two", 50000, None)])
        self.assertEqual([r["price_musd"] for r in each], [17.0, None])


class ReportsAndFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "Sources"
        self.src.mkdir()
        for name in ("2026-11-04_HSN_VesselValuations_wk_2.png", "2026-11-04_HSN_VesselValuations_wk_1.png",
                     "2026-10-31_AdvancedShipping_Market_wk44.pdf", "notes.txt"):
            (self.src / name).write_bytes(name.encode())

    def test_grouping_and_new(self):
        reps = find_reports(self.src)
        self.assertEqual([r.broker for r in reps], ["advanced", "hsn"])
        self.assertEqual([f.name for f in reps[1].files][0], "2026-11-04_HSN_VesselValuations_wk_1.png")
        reg = seed_register(reps, {"2026-10-31_AdvancedShipping_Market_wk44.pdf"})
        self.assertEqual([r.report_id for r in new_reports(reps, reg)], ["2026-11-04_HSN_VesselValuations"])
        (self.src / "renamed.pdf").write_bytes(b"x")                          # renaming does not make a report new
        shutil.move(self.src / "2026-10-31_AdvancedShipping_Market_wk44.pdf", self.src / "2026-10-31_AdvancedShipping_Market_wk44_copy.pdf")
        self.assertEqual([r.report_id for r in new_reports(find_reports(self.src), reg)], ["2026-11-04_HSN_VesselValuations"])

    def test_check_file_and_add(self):
        clean = self.tmp / "clean"
        clean.mkdir()
        with (clean / "sales.csv").open("w", newline="") as fh:
            csv.writer(fh).writerows([data_files.SALES_COLUMNS, ["7", "2026-05-22", "Sample Tide", "MR", "50000", "2012"] + [""] * 14])
        with (clean / "indicative_prices.csv").open("w", newline="") as fh:
            csv.writer(fh).writerow(data_files.VALUE_COLUMNS)
        sale = {"report_date": D(2026, 11, 2), "vessel": "Test", "segment": "MR", "dwt": 50000, "built": 2010, "shipyard": "X",
                "yard_country": "Korea", "price_musd": 20.0, "buyer": "Greek", "seller": None, "features": None, "en_bloc": "N",
                "sale_type": "Secondhand", "source_file": "r.pdf", "source_url": None, "notes": "p1", "reviewed_decision": None,
                "review_reason": None, "next_survey": None, "_page": 1, "_warnings": []}
        path = check_file.write(self.tmp / "staging" / "check_x.xlsx", [sale], [], ["read r.pdf"])
        import openpyxl
        wb = openpyxl.load_workbook(path)
        self.assertEqual(wb["Sales"]["A2"].value, "OK")                       # a clear row is decided already
        wb["Sales"]["A2"] = None
        wb.save(path)
        rows, values, problems = check_file.read(path)
        self.assertEqual((rows, len(problems)), ([], 1))                       # undecided: nothing returned
        wb["Sales"]["A2"] = "OK"
        wb.save(path)
        rows, values, problems = check_file.read(path)
        self.assertEqual((len(rows), problems, data_files.check_rows(rows, values)), (1, [], []))
        data_files.backup(clean, "t")
        data_files.append(clean, rows, values)
        lines = (clean / "sales.csv").read_text().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[2].startswith("8,2026-11-02,Test,MR,50000,2010"))
        self.assertTrue((clean / "backup" / "t_sales.csv").exists())

    def test_deleted_check_file_reads_again(self):
        from m1_extract.__main__ import cmd_extract
        from m1_extract.reports import load_register
        data = self.tmp / "M1_Data"
        (data / "clean").mkdir(parents=True)
        (data / "clean" / "sales.csv").write_text(",".join(data_files.SALES_COLUMNS) + "\n")
        (data / "clean" / "indicative_prices.csv").write_text(",".join(data_files.VALUE_COLUMNS) + "\n")
        (self.src / "2026-11-04_HSN_VesselValuations_wk_1.png").unlink()
        (self.src / "2026-11-04_HSN_VesselValuations_wk_2.png").unlink()
        rep = find_reports(self.src)[0]
        from m1_extract.reports import save_register
        save_register(data / "extracted_reports.csv", [{"report_id": rep.report_id, "broker": rep.broker, "report_date": "2026-10-31",
                       "files": rep.file_names, "fingerprint": rep.fingerprint, "status": "read, waiting for check", "check_file": "check_x.xlsx"}])
        cmd_extract(self.src, data)                                           # the PDF is not real: it fails to read, but is tried again
        self.assertTrue((data / "staging").exists())
        self.assertEqual([r["status"] for r in load_register(data / "extracted_reports.csv")], [])

    def test_already_in_data(self):
        existing = [{"id": "53", "vessel": "Saltwind Explorer", "built": "2011", "report_date": "2026-10-27", "price_musd": "16.5", "source_file": "h.png"}]
        self.assertTrue(data_files.already_in_data({"vessel": "SALTWIND EXPLORER", "built": 2011, "report_date": D(2026, 10, 31)}, existing).startswith("yes"))
        self.assertEqual(data_files.already_in_data({"vessel": "Saltwind Explorer", "built": 2011, "report_date": D(2027, 10, 31)}, existing), "")


if __name__ == "__main__":
    unittest.main()
