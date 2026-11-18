"""Make the three SYNTHETIC sample reports and their expected rows.

Run from the project folder:   .venv/bin/python data/sample/make_sample_reports.py

Each PDF copies only the table LAYOUT of a report the extractor reads (column order and positions). Every ship,
price, buyer and date is made up, every page says SYNTHETIC, and there are no broker logos or report text.

The expected rows (expected_*.csv) are written here by hand from the same made-up data, so the test checks the
extractor against what the report says, not against the extractor's own output.

No extra library is needed: the PDFs are written directly (Helvetica, text only).
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 595.32, 841.92                      # A4, as the real reports

FIELDS = ["vessel", "segment", "dwt", "built", "shipyard", "yard_country", "price_musd", "buyer", "en_bloc",
          "sale_type", "next_survey", "features"]
VALUE_FIELDS = ["segment", "size", "age", "value_musd", "compared_with", "earlier_value_musd"]


# ------------------------------------------------------------------ a minimal PDF writer
def _esc(t: str) -> str:
    return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(path: Path, pages):
    """pages: list of [(x, top, size, text)], top measured from the top of the page (as pdfplumber reports it)."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    kids = []
    for items in pages:
        ops = ["BT"]
        for x, top, size, text in items:
            baseline = H - top - 0.72 * size
            ops.append(f"/F1 {size} Tf 1 0 0 1 {x:.2f} {baseline:.2f} Tm ({_esc(text)}) Tj")
        ops.append("ET")
        stream = "\n".join(ops)
        objs.append(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")
        content = len(objs)
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content} 0 R >>")
        kids.append(len(objs))
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>"
    out, offsets = b"%PDF-1.4\n", []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(out)


def footer(layout: str):
    return [(30, 800, 8, "SYNTHETIC SAMPLE - made-up ships, prices and dates. Not a broker report."),
            (30, 812, 8, f"Only the table layout is modelled on the {layout}.")]


def write_csv(path: Path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def row(vessel, segment, dwt, built, yard, country, price, buyer, en_bloc="N", sale_type="Secondhand",
        survey="", features=""):
    return dict(zip(FIELDS, [vessel, segment, dwt, built, yard, country, price, buyer, en_bloc, sale_type, survey,
                             features]))


# ------------------------------------------------------------------ 1. Advanced Shipping & Trading layout
def advanced():
    s = 6.5
    p1 = [(227, 39, 16, "REPORTED SALES"), (423, 94, 9, "Week 2 (2nd Jan to 9th Jan 2026)"),
          (248, 127, 11, "Bulk Carriers")]
    cols = [("Type", 30), ("Name", 89), ("Dwt", 146), ("YoB", 186), ("Yard", 234), ("SS", 293), ("M/E", 334),
            ("Gear", 379), ("Price", 421), ("Buyer", 472), ("Comments", 526)]
    p1 += [(x, 153, s, t) for t, x in cols]
    #        top  type         name             dwt       yob     yard (one or two lines)          ss         gear     price        buyer          comments
    bulk = [(174, "Kamsarmax", "Sample Horizon", "81.600", "2014", ["Northport Heavy,", "Korea"], "03/2029", "-", "$ 21,5m", "Greek", ""),
            (197, "Supramax", "Demo Trader", "56.100", "2012", ["Eastbay, Japan"], "07/2027", "4x30T", "$ 15,2m", "Undisclosed", "Scrubber fitted"),
            (214, "Handysize", "Test Pioneer", "37.200", "2015", ["Seaview, Japan"], "05/2030", "4x30T", "High $ 19m", "Greek", ""),
            (231, "Handysize", "Mock Spirit", "32.000", "2011", ["Harbourside, Japan"], "04/2028", "4x30T", "$ 24m", "Chinese", "enbloc"),
            (248, "Handysize", "Mock Venture", "32.010", "2011", ["Harbourside, Japan"], "04/2028", "4x30T", "", "", "")]
    for top, typ, name, dwt, yob, yard, ss, gear, price, buyer, com in bulk:
        p1 += [(21, top, s, typ), (84, top, s, name), (143, top, s, dwt), (186, top, s, yob), (282, top, s, ss),
               (323, top, s, "MAN-B&W"), (388, top, s, gear), (418, top, s, price), (464, top, s, buyer), (526, top, s, com)]
        if len(yard) == 1:
            p1.append((218, top, s, yard[0]))
        else:
            p1 += [(215, top - 6, s, yard[0]), (234, top + 5, s, yard[1])]
    p1.append((248, 300, 11, "Tankers"))
    tcols = [("Type", 32), ("Name", 92), ("Dwt", 150), ("YoB", 188), ("Yard", 245), ("SS", 314), ("M/E", 357),
             ("Price", 411), ("Buyer", 471), ("Comments", 525)]
    p1 += [(x, 325, s, t) for t, x in tcols]
    tank = [(346, "MR", "Sample Coast", "49.990", "2016", "Hyundai Mipo, Korea", "09/2026", "$ 34,5m", "Undisclosed", "Online bidding"),
            (363, "LR2", "Demo Crest", "115.000", "2027", "Riverside, China", "", "$ 72m", "Greek", "Resale")]
    for top, typ, name, dwt, yob, yard, ss, price, buyer, com in tank:
        p1 += [(26, top, s, typ), (84, top, s, name), (143, top, s, dwt), (186, top, s, yob), (225, top, s, yard),
               (303, top, s, ss), (345, top, s, "MAN-B&W"), (408, top, s, price), (464, top, s, buyer), (525, top, s, com)]
    p1 += footer("Advanced Shipping & Trading weekly market report")

    p2 = [(200, 39, 16, "INDICATIVE PRICES"), (423, 94, 9, "Week 2 (2nd Jan to 9th Jan 2026)"),
          (60, 130, 9, "Tankers"), (60, 145, 8, "Size Age Week 2 Week 1 change")]
    vals = [("MR", "50k", "Resale", "48,5", "48", "1,04%"), ("MR", "50k", "5 years", "41", "41", "0,00%"),
            ("MR", "50k", "10 years", "32,5", "33", "-1,52%"), ("LR2", "115k", "5 years", "68", "67,5", "0,74%")]
    for i, v in enumerate(vals):
        p2.append((60, 165 + 15 * i, 8, " ".join(v)))
    p2 += footer("Advanced Shipping & Trading weekly market report")
    write_pdf(HERE / "2026-01-09_AdvancedShipping_Market_wk02_SYNTHETIC.pdf", [p1, p2])

    sales = [row("Sample Horizon", "Kamsarmax", 81600, 2014, "Northport Heavy", "Korea", 21.5, "Greek", survey="2029-03-01"),
             row("Demo Trader", "Supramax", 56100, 2012, "Eastbay", "Japan", 15.2, "Undisclosed", survey="2027-07-01",
                 features="Scrubber fitted"),
             row("Test Pioneer", "Handysize", 37200, 2015, "Seaview", "Japan", "", "Greek", survey="2030-05-01",
                 features="Approximate price: High $ 19m"),
             row("Mock Spirit", "Handysize", 32000, 2011, "Harbourside", "Japan", 12.0, "Chinese", "Y", survey="2028-04-01"),
             row("Mock Venture", "Handysize", 32010, 2011, "Harbourside", "Japan", 12.0, "Chinese", "Y", survey="2028-04-01"),
             row("Sample Coast", "MR", 49990, 2016, "Hyundai Mipo", "Korea", 34.5, "Undisclosed", sale_type="Auction",
                 survey="2026-09-01"),
             row("Demo Crest", "LR2", 115000, 2027, "Riverside", "China", 72.0, "Greek", sale_type="Resale")]
    write_csv(HERE / "expected_advanced_sales.csv", FIELDS, sales)
    write_csv(HERE / "expected_advanced_values.csv", VALUE_FIELDS,
              [dict(zip(VALUE_FIELDS, [seg, size, age, now.replace(",", "."), "Week 1", before.replace(",", ".")]))
               for seg, size, age, now, before, _ in vals])


# ------------------------------------------------------------------ 2. Xclusiv layout
def xclusiv():
    s = 7
    p = [(240, 60, 16, "Sale & Purchase"), (267, 100, 10, "TANKER SALES"), (437, 112, s, "PRICE")]
    p += [(x, 120, s, t) for t, x in (("NAME", 68), ("DWT", 142), ("YEAR", 172), ("COUNTRY", 197), ("YARD", 277),
                                       ("BUYERS", 365), ("COMMENTS", 495))]
    p.append((433, 127, s, "($ mills)"))
    #        name            dwt        year    country    x_c  yard              x_y  buyers                x_b  price    x_p  comments
    rows = [("SAMPLE STAR", "158,000", "2013", "S. KOREA", 199, "NORTHPORT", 266, "UNDISCLOSED", 353, "72", 444, ""),
            ("DEMO RIVER", "74,500", "2009", "CROATIA", 199, "EASTBAY", 268, "GREEK", 368, "18.5", 440, ""),
            ("TEST HARBOUR", "49,900", "2021", "CHINA", 204, "NEW TIMES", 265, "UNDISCLOSED", 353, "RGN 47", 434, "DELY MAR 26"),
            ("MOCK LAKE", "50,200", "2010", "S. KOREA", 199, "HYUNDAI MIPO", 257, "CLIENTS OF EXAMPLE", 336, "24.8", 440, "SCRUBBER FITTED"),
            ("SAMPLE BAY", "45,800", "2007", "JAPAN", 204, "SHIN KURUSHIMA", 252, "UNDISCLOSED", 353, "16", 444, "ICE CLASSED")]
    for i, (name, dwt, year, country, xc, yard, xy, buyer, xb, price, xp, com) in enumerate(rows):
        top = 139 + 12.7 * i
        p += [(28, top, s, name), (138 if len(dwt) < 7 else 136, top, s, dwt), (172, top, s, year),
              (xc, top, s, country), (xy, top, s, yard), (xb, top, s, buyer), (xp, top, s, price), (483, top, s, com)]
    p += footer("Xclusiv weekly sale & purchase report")
    write_pdf(HERE / "2026-01-12_Xclusive_SalesPurchase_wk03_SYNTHETIC.pdf", [p])

    sales = [row("Sample Star", "Suezmax", 158000, 2013, "Northport", "Korea", 72.0, "Undisclosed"),
             row("Demo River", "LR1", 74500, 2009, "Eastbay", "Croatia", 18.5, "Greek"),
             row("Test Harbour", "MR", 49900, 2021, "New Times", "China", "", "Undisclosed",
                 features="Approximate price: RGN 47"),
             row("Mock Lake", "MR", 50200, 2010, "Hyundai Mipo", "Korea", 24.8, "Clients of Example",
                 features="Scrubber fitted"),
             row("Sample Bay", "MR", 45800, 2007, "Shin Kurushima", "Japan", 16.0, "Undisclosed", features="Ice classed")]
    write_csv(HERE / "expected_xclusiv_sales.csv", FIELDS, sales)


# ------------------------------------------------------------------ 3. Intermodal layout
def intermodal():
    s = 5.5
    p = [(469, 36, 15, "Secondhand Sales"), (15, 115, 9, "Tankers")]
    head = [("Size", 13), ("Name", 87), ("Dwt", 141), ("Built", 183), ("Yard", 241), ("M/E", 292), ("SS due", 331), ("Hull", 370), ("Price", 406), ("Buyers", 455), ("Comments", 517)]
    p += [(x, 141, s, t) for t, x in head]
    tank = [("LR2", "SAMPLE GLORY", "109,000", "2012", "ACME, S. Korea", "Apr-28", "$ 52.0m", "Greek", ""),
            ("MR2", "DEMO PEARL", "50,100", "2011", "STX, S. Korea", "Oct-26", "$ 26.5m", "undisclosed", ""),
            ("MR2", "TEST VOYAGER", "47,000", "2008", "EASTBAY, China", "Jul-27", "high $ 18.0m", "undisclosed", "")]
    for i, (size, name, dwt, built, yard, ss, price, buyer, com) in enumerate(tank):
        top = 157 + 13 * i
        p += [(13, top, s, size), (85, top, s, name), (135, top, s, dwt), (183, top, s, built), (224, top, s, yard),
              (285, top, s, "MAN B&W"), (331, top, s, ss), (372, top, s, "DH"), (401, top, s, price),
              (455, top, s, buyer), (517, top, s, com)]
    p.append((15, 240, 9, "Bulk Carriers"))
    bhead = [("Size", 13), ("Name", 87), ("Dwt", 141), ("Built", 183), ("Yard", 241), ("M/E", 292), ("SS due", 331), ("Gear", 370), ("Price", 430), ("Buyers", 470), ("Comments", 525)]
    p += [(x, 266, s, t) for t, x in bhead]
    bulk = [("KMAX", "MOCK EMPIRE", "82,000", "2015", "SEAVIEW, Japan", "Sep-29", "-", "$ 24.0m", "Chinese", "via auction"),
            ("SUPRA", "SAMPLE WAVE", "56,500", "2010", "RIVERSIDE, China", "Mar-27", "4 X 30t CRANES", "$ 14,5m", "undisclosed", "")]
    for i, (size, name, dwt, built, yard, ss, gear, price, buyer, com) in enumerate(bulk):
        top = 282 + 13 * i
        p += [(13, top, s, size), (85, top, s, name), (135, top, s, dwt), (183, top, s, built), (224, top, s, yard),
              (285, top, s, "MAN B&W"), (331, top, s, ss), (370, top, s, gear), (428, top, s, price),
              (470, top, s, buyer), (525, top, s, com)]
    p += footer("Intermodal weekly report")
    write_pdf(HERE / "2026-01-14_intermodal-report-wk02_SYNTHETIC.pdf", [p])

    sales = [row("Sample Glory", "LR2", 109000, 2012, "Acme", "Korea", 52.0, "Greek", survey="2028-04-01"),
             row("Demo Pearl", "MR", 50100, 2011, "STX", "Korea", 26.5, "undisclosed", survey="2026-10-01"),
             row("Test Voyager", "MR", 47000, 2008, "Eastbay", "China", "", "undisclosed", survey="2027-07-01",
                 features="Approximate price: high $ 18.0m"),
             row("Mock Empire", "Kamsarmax", 82000, 2015, "Seaview", "Japan", 24.0, "Chinese", sale_type="Auction",
                 survey="2029-09-01"),
             row("Sample Wave", "Supramax", 56500, 2010, "Riverside", "China", 14.5, "undisclosed", survey="2027-03-01")]
    write_csv(HERE / "expected_intermodal_sales.csv", FIELDS, sales)


if __name__ == "__main__":
    advanced()
    xclusiv()
    intermodal()
    print(f"written to {HERE}")
