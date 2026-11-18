"""One reader per broker. Each returns (sales, broker_values): lists of dictionaries in the data-contract fields
(see docs/data_dictionary.md), plus '_page' (where the row was found) and '_warnings' (what to check).

Conventions follow the rows typed by hand in M1: sale date = report date; approximate prices are not prices (the text
goes to features); survey dates go to notes and next_survey; container size in TEU goes to notes, DWT left empty.
"""
import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Tuple

from . import normalise as N
from .pdf_columns import find_header, looks_like_size, page_words, read_table

Row = Dict[str, object]


def _sale(source_file: str, report_date: dt.date, page: int) -> Row:
    return {"report_date": report_date, "vessel": None, "segment": None, "dwt": None, "built": None, "shipyard": None,
            "yard_country": None, "price_musd": None, "buyer": None, "seller": None, "features": None, "en_bloc": "N",
            "sale_type": "Secondhand", "source_file": source_file, "source_url": None, "notes": None,
            "reviewed_decision": None, "review_reason": None, "next_survey": None, "_page": page, "_warnings": []}


def _finish(r: Row, comments: str, ss: str = "", extra_notes: List[str] = ()) -> Row:
    """Common last steps: sale type, en bloc flag, survey date, notes, and the warnings a checker needs."""
    low = (comments or "").lower()
    if "auction" in low or "bidding" in low:
        r["sale_type"] = "Auction"
    if "resale" in low or (r["built"] and r["built"] > r["report_date"].year):
        r["sale_type"] = "Resale"
    if re.search(r"en ?bloc", low):
        r["en_bloc"] = "Y"
    dates = [d for d in (N.survey_date(ss), *(N.survey_date(m) for m in re.findall(r"(?:SS|DD)[^,;]*", comments or "")))
             if d]
    r["next_survey"] = dt.date.fromisoformat(min(dates)) if dates else None
    parts = [f"p{r['_page']}"] + ([f"SS {ss}"] if ss else []) + list(extra_notes) + ([comments] if comments else [])
    r["notes"] = "; ".join(p for p in parts if p)
    w = r["_warnings"]
    if re.search(r"en ?bloc", f"{r.get('features') or ''} {low}", re.I):
        r["en_bloc"] = "Y"
    if not r["segment"] and r["dwt"]:
        table = r.pop("_table", None)
        guess = N.segment_from_size(r["dwt"], table) if table else None
        if guess:
            r["segment"] = guess
            w.append("segment worked out from DWT: check")
    r.pop("_table", None)
    if not r["vessel"]:
        w.append("name missing")
    if not r["segment"]:
        w.append("segment not recognised: fill in")
    if r["dwt"] is None and r["segment"] != "Container":
        w.append("DWT missing")
    if not r["built"]:
        w.append("year built missing")
    if r["price_musd"] is None:
        w.append("no exact price")
    if r["en_bloc"] == "Y":
        w.append("en bloc: check the price split")
    if r["sale_type"] != "Secondhand":
        w.append(f"sale type {r['sale_type']}: check")
    return r


# ------------------------------------------------------------------ en bloc (sister ships sold together)
def link_en_bloc(sales: List[Row]) -> List[Row]:
    """Join sister ships sold together (en bloc) and split the package price equally between them.

    Broker tables print one package price ('$ 40m enbloc') for two or more ships. The price lands on one row and
    the sister ship next to it has no price (and may not say en bloc at all). Rows are in table order, so:

    1. a ship marked en bloc WITH a price is joined to the ship just above (or else just below) that has no price;
    2. a ship marked en bloc WITHOUT a price is joined to the ship just above (or else just below) that has one;
    3. the same price printed on both ships of an en bloc pair is one package price;
    4. a package grows to a further neighbour without a price that looks like a sister: same segment, DWT within 2%,
       built within a year (three or more ships sold together).

    Each ship then gets total / number of ships, the buyer printed across the rows is joined, and the row says so.
    A price marked 'each' is a price per ship and is not split.
    """
    def is_bloc(r):
        return r["en_bloc"] == "Y" or "package (en bloc)" in (r.get("features") or "")

    def each(r):
        return bool(re.search(r"\beach\b", f"{r.get('notes') or ''} {r.get('features') or ''}", re.I))

    def no_price(r):
        return r["price_musd"] is None and "Approximate price" not in (r.get("features") or "")

    def near(i, j):
        return 0 <= j < len(sales) and sales[j]["_page"] == sales[i]["_page"] \
            and sales[j]["source_file"] == sales[i]["source_file"]

    def sister(a, b):
        return a["segment"] == b["segment"] and a["dwt"] and b["dwt"] and abs(a["dwt"] - b["dwt"]) <= 0.02 * a["dwt"] \
            and a["built"] and b["built"] and abs(a["built"] - b["built"]) <= 1

    group_of: Dict[int, List[int]] = {}
    groups: List[List[int]] = []

    def join(i, j):
        g = group_of.get(i) or group_of.get(j)
        if g is None:
            g = []
            groups.append(g)
        for k in (i, j):
            if k not in g:
                g.append(k)
            group_of[k] = g

    for i, r in enumerate(sales):
        if not is_bloc(r) or i in group_of or each(r):
            continue
        want_price = r["price_musd"] is None
        for j in (i - 1, i + 1):
            if near(i, j) and j not in group_of and not each(sales[j]) and \
                    ((want_price and sales[j]["price_musd"] is not None) or (not want_price and no_price(sales[j]))):
                join(i, j)
                break
        else:
            j = i + 1
            if near(i, j) and is_bloc(sales[j]) and sales[j]["price_musd"] == r["price_musd"] and not each(sales[j]) \
                    and r["price_musd"] is not None:
                join(i, j)
    for g in groups:
        g.sort()
        for step, edge in ((-1, lambda: g[0]), (1, lambda: g[-1])):
            k = edge() + step
            while near(edge(), k) and k not in group_of and no_price(sales[k]) and sister(sales[k], sales[g[0]]):
                g.append(k)
                group_of[k] = g
                g.sort()
                k = edge() + step
    for g in groups:
        rows = [sales[k] for k in sorted(g)]
        total = next(r["price_musd"] for r in rows if r["price_musd"] is not None)
        buyers = [r["buyer"] for r in rows if r["buyer"]]
        if any(b.count("(") != b.count(")") for b in buyers):
            buyer = " ".join(buyers)                       # one buyer name printed across the rows
        else:
            buyer = next((b for b in buyers if b.lower() != "undisclosed"), buyers[0] if buyers else None)
        names = " and ".join(r["vessel"] or "?" for r in rows)
        share = round(total / len(rows), 4)
        for r in rows:
            r["en_bloc"] = "Y"
            r["price_musd"] = share
            r["buyer"] = buyer
            feats = [f for f in (r.get("features") or "").split("; ")
                     if f and "package (en bloc)" not in f and not f.startswith("Price as reported")]
            r["features"] = "; ".join(feats) or None
            r["notes"] = f"{r['notes']}; package ${total:g}m for {names}; split equally"
            r["_warnings"] = [w for w in r["_warnings"] if w not in ("no exact price", "en bloc: check the price split")]
            r["_warnings"].append(f"en bloc: package ${total:g}m split equally between {len(rows)} ships: check")
    return sales


# ------------------------------------------------------------------ Advanced Shipping & Trading
ADV_SEGMENTS = r"(Capesize|Kamsarmax|Ultramax|Supramax|Handysize|Panamax|VLCC|Suezmax|Aframax|LR1|LR2|MR)"
ADV_VALUE = re.compile(ADV_SEGMENTS + r"\s+(\d+k)\s+(Resale|\d+ years)\s+(\d+(?:,\d+)?)\s+(\d+(?:,\d+)?)\s+(-?\d+(?:,\d+)?%)")


def read_advanced(pdf, source_file: str, report_date: dt.date) -> Tuple[List[Row], List[Row]]:
    sales, values = [], []
    for pno, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        week = re.search(r"Week (\d+)", text)
        if text.startswith("REPORTED SALES") or ("Type" in text and "YoB" in text and "Buyer" in text):
            words, after = page_words(page), -1
            headers = []
            while True:
                lines = {}
                for w in words:
                    if w.top > after:
                        lines.setdefault(round(w.top), []).append(w)
                hdr = None
                for y in sorted(lines):
                    line = [w for yy in (y - 1, y, y + 1) for w in lines.get(yy, [])]
                    names = {w.text for w in line}
                    if {"Type", "Name", "YoB", "Price"} <= names:
                        hdr = {w.text: w for w in sorted(line, key=lambda w: w.x0)}
                        break
                if not hdr:
                    break
                headers.append(hdr)
                after = max(w.bottom for w in hdr.values()) + 1
            for i, hdr in enumerate(headers):
                stop = min(w.top for w in headers[i + 1].values()) - 25 if i + 1 < len(headers) else None
                anchor = "Dwt" if "Dwt" in hdr else ("Teu" if "Teu" in hdr else "Cbm")
                table = "container" if anchor == "Teu" else ("gas" if anchor == "Cbm" else ("bulk" if "Gear" in hdr else "tanker"))
                for c in read_table(words, hdr, anchor, looks_like_size, stop_y=stop):
                    r = _sale(source_file, report_date, pno)
                    r["vessel"] = N.ship_name(c.get("Name", ""))
                    r["segment"] = N.segment_from_type(c.get("Type", ""), table) or ("Gas" if table == "gas" else None)
                    r["_table"] = table
                    size = N.size_number(c.get(anchor, ""))
                    extra = []
                    if table == "container":
                        extra.append(f"{size:,} TEU (DWT not reported)" if size else "TEU not read")
                    elif table == "gas":
                        extra.append(f"{size:,} cbm (DWT not reported)" if size else "cbm not read")
                    else:
                        r["dwt"] = size
                    yob = re.search(r"(19|20)\d{2}", c.get("YoB", ""))
                    r["built"] = int(yob.group(0)) if yob else None
                    r["shipyard"], r["yard_country"] = N.yard_and_country(c.get("Yard", ""))
                    r["price_musd"], remark = N.price(c.get("Price", ""))
                    r["buyer"] = c.get("Buyer") or None
                    comments = c.get("Comments", "")
                    feats = [f for f in (comments if re.search(r"scrubber|ice|bwts|eco|dpp|t/c|charter", comments, re.I) else "", remark) if f]
                    r["features"] = "; ".join(feats) or None
                    sales.append(_finish(r, comments, c.get("SS", ""), extra))
        if text.startswith("INDICATIVE PRICES") and week:
            wk = int(week.group(1))
            for line in text.splitlines():
                for m in ADV_VALUE.finditer(line):
                    seg, size, age, now, before, _ = m.groups()
                    values.append({"report_date": report_date, "broker": "Advanced Shipping", "segment": seg,
                                   "size": size, "age": age, "value_musd": float(now.replace(",", ".")),
                                   "compared_with": f"Week {wk - 1}", "earlier_value_musd": float(before.replace(",", ".")),
                                   "basis": f"Week {wk}; p{pno}; as reported (table 'Indicative Prices')",
                                   "source_file": source_file, "_page": pno, "_warnings": []})
    return link_en_bloc(sales), values


# ------------------------------------------------------------------ Xclusiv
def read_xclusiv(pdf, source_file: str, report_date: dt.date) -> Tuple[List[Row], List[Row]]:
    sales = []
    for pno, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        for heading, table in (("TANKER SALES", "tanker"), ("BULK CARRIER SALES", "bulk")):
            if heading not in text:
                continue
            words = page_words(page)
            top = min((w.top for w in words if w.text == heading.split()[0]), default=-1)
            hdr = find_header(words, ["NAME", "DWT", "YEAR", "COUNTRY", "YARD", "BUYERS", "COMMENTS"], after_y=top)
            if not hdr:
                continue
            price_word = [w for w in words if w.text == "PRICE" and abs(w.top - hdr["NAME"].top) < 20]
            if price_word:
                hdr["PRICE"] = price_word[0]
            for c in read_table(words, hdr, "DWT", looks_like_size, max_gap=6):
                r = _sale(source_file, report_date, pno)
                r["vessel"] = N.ship_name(c.get("NAME", ""))
                r["dwt"] = N.size_number(c.get("DWT", ""))
                r["segment"] = N.segment_from_size(r["dwt"], table)
                if r["segment"]:
                    r["_warnings"].append("segment worked out from DWT: check")
                yob = re.search(r"(19|20)\d{2}", c.get("YEAR", ""))
                r["built"] = int(yob.group(0)) if yob else None
                r["shipyard"] = N.title_case(c.get("YARD", ""))
                r["yard_country"] = N.COUNTRIES.get(c.get("COUNTRY", "").strip().lower(), N.title_case(c.get("COUNTRY", "")))
                price_text, comments = c.get("PRICE", ""), c.get("COMMENTS", "")
                m = re.match(r"^\s*((?:RGN|HIGH|LOW|XS|EXCESS|MID)\s*)?(\d+(?:\.\d+)?)\s*(.*)$", price_text, re.I)
                if m:
                    price_text, comments = (m.group(1) or "") + m.group(2), (m.group(3) + " " + comments).strip()
                r["price_musd"], remark = N.price(price_text)
                r["buyer"] = N.title_case(c.get("BUYERS", "")) or None
                feats = [f for f in (comments.capitalize() if re.search(r"scrubber|ice|bwts|eco|dpp|t/c|charter", comments, re.I) else "", remark) if f]
                r["features"] = "; ".join(feats) or None
                sales.append(_finish(r, comments.capitalize()))
    return link_en_bloc(sales), []


# ------------------------------------------------------------------ Intermodal
def read_intermodal(pdf, source_file: str, report_date: dt.date) -> Tuple[List[Row], List[Row]]:
    sales = []
    for pno, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        if "Secondhand Sales" not in text:
            continue
        words = page_words(page, x_tolerance=3)
        bulk_top = min((w.top for w in words if w.text == "Bulk"), default=None)
        for table, after, stop in (("tanker", -1, bulk_top), ("bulk", bulk_top or 1e9, None)):
            hdr = find_header(words, ["Size", "Name", "Dwt", "Built", "Yard", "SS", "Price", "Buyers", "Comments"], after_y=after)
            if not hdr or (stop is not None and hdr["Name"].top > stop):
                continue
            # Use every title on the header line (M/E, Hull, Gear …) so those columns are not merged into a neighbour.
            line = [w for w in words if abs(w.top - hdr["Name"].top) < 3 and w.text not in ("due",)]
            hdr = {**{w.text: w for w in line}, **hdr}
            for c in read_table(words, hdr, "Dwt", looks_like_size, stop_y=stop, max_gap=6):
                r = _sale(source_file, report_date, pno)
                r["vessel"] = N.ship_name(c.get("Name", "").replace("  ", " "))
                r["segment"] = N.segment_from_type(c.get("Size", ""), table)
                r["_table"] = table
                r["dwt"] = N.size_number(c.get("Dwt", ""))
                yob = re.search(r"(19|20)\d{2}", c.get("Built", ""))
                r["built"] = int(yob.group(0)) if yob else None
                r["shipyard"], r["yard_country"] = N.yard_and_country(c.get("Yard", ""))
                r["price_musd"], remark = N.price(c.get("Price", ""))
                r["buyer"] = c.get("Buyers") or None
                comments = c.get("Comments", "")
                feats = [f for f in (comments if re.search(r"scrubber|ice|bwts|eco|dpp|stst|t/c|charter", comments, re.I) else "", remark) if f]
                r["features"] = "; ".join(feats) or None
                sales.append(_finish(r, comments, c.get("SS", "")))
    return link_en_bloc(sales), []


# ------------------------------------------------------------------ HSN Weekly Vessel Valuations (screenshots)
HSN_PREFIXES = ["Sub Panamax", "Post Panamax", "Newcastlemax", "Capesize", "Kamsarmax", "Ultramax", "Supramax",
                "Handysize", "Panamax", "VLCC", "Suezmax", "Aframax", "LR2", "LR1", "MR2", "MR1", "MR", "Handy",
                "Feeder", "Small", "Chemical", "VLGC", "LPG", "LNG"]
HSN_SALE = re.compile(
    r"(?P<lead>(?:" + "|".join(HSN_PREFIXES) + r")\s+[^()]+?)\s*\(\s*(?P<size>[\d.,]+)\s*(?P<unit>DWT|TEU|CBM)\s*[,.]?\s*"
    r"(?P<year>(?:19|20)\d{2})\s*[,.]\s*(?P<yard>[^)]+)\)\s*sold\s+(?P<who>.*?)\s*for\s+USD\s+(?P<price>[\d.,]+)\s*mil"
    r"[,.]?\s*(?:[VW]{1,2}\s*V?alue\s+USD\s+(?P<vv>[\d.,]+)\s*mil)?", re.I)
HSN_SECTION = {"bulkers": "bulk", "tankers": "tanker", "containers": "container", "gas": "gas"}


def ocr_lines(image_path: Path) -> List[str]:
    """Text lines of an image, top to bottom, with Apple's text recognition (macOS Vision)."""
    import Vision
    from Foundation import NSURL
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    req.setUsesLanguageCorrection_(False)
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(image_path)), None)
    ok, err = handler.performRequests_error_([req], None)
    if not ok:
        raise RuntimeError(f"text recognition failed for {image_path.name}: {err}")
    found = [(1 - o.boundingBox().origin.y, o.boundingBox().origin.x, o.topCandidates_(1)[0].string()) for o in req.results()]
    return [t for _, _, t in sorted(found)]


def read_hsn(images: List[Path], report_date: dt.date) -> Tuple[List[Row], List[Row]]:
    """Read one HSN valuations report from its screenshots (in order _1, _2 …). Sales split across two images are joined."""
    text_parts, page_of = [], []
    for i, img in enumerate(images, start=1):
        for line in ocr_lines(img):
            text_parts.append(line)
            page_of.append(i)
    return parse_hsn(text_parts, page_of, "; ".join(p.name for p in images), report_date)


def parse_hsn(text_parts: List[str], page_of: List[int], names: str, report_date: dt.date) -> Tuple[List[Row], List[Row]]:
    """Turn the recognised text lines of an HSN valuations report into sale rows (testable without images)."""
    title = re.search(r"Report,?\s+([A-Z][a-z]+)\s+(\d{1,2}),?\s*(20\d{2})", " ".join(text_parts[:4]))
    if title:
        try:
            report_date = dt.datetime.strptime(f"{title.group(1)} {title.group(2)} {title.group(3)}", "%B %d %Y").date()
        except ValueError:
            pass
    sales, section = [], "bulk"
    joined, offsets, pos = "", [], 0
    for line, pg in zip(text_parts, page_of):
        key = line.strip().lower()
        if key in HSN_SECTION:
            joined += f" §{HSN_SECTION[key]}§ "
        offsets.append((len(joined), pg))
        joined += " " + line.strip()
    for m in HSN_SALE.finditer(joined):
        before = joined[:m.start()]
        sec = re.findall(r"§(\w+)§", before)
        section = sec[-1] if sec else "bulk"
        page = max((pg for off, pg in offsets if off <= m.start()), default=1)
        r = _sale(names, report_date, page)
        lead = " ".join(m.group("lead").split())
        # The match may start inside the comment paragraph above the sale: keep the text after the LAST segment word.
        starts = [mm for mm in re.finditer(r"(?:(?<=^)|(?<=[\s.]))(" + "|".join(sorted(HSN_PREFIXES, key=len, reverse=True))
                                             + r")\s+(?=[A-Z0-9])", lead)]
        prefix, rest = (starts[-1].group(1), lead[starts[-1].end():]) if starts else ("", lead)
        r["vessel"] = rest.strip()
        ships = [x.strip() for x in re.split(r"\s*&\s*|\s+and\s+", r["vessel"]) if x.strip()]
        code = prefix.upper().replace(" ", "")
        r["segment"] = ("Container" if section == "container" else
                        N.segment_from_type(code, section) or N.segment_from_type(prefix.split()[0], section)
                        or N.segment_from_type(code, "tanker") or N.segment_from_type(code, "bulk"))
        size = N.size_number(m.group("size"))
        extra = []
        if m.group("unit").upper() == "DWT":
            r["dwt"] = size
        else:
            extra.append(f"{size:,} {m.group('unit').upper()} (DWT not reported)")
        r["built"] = int(m.group("year"))
        r["shipyard"] = " ".join(m.group("yard").split())
        r["price_musd"] = float(m.group("price").replace(",", "."))
        who = " ".join(m.group("who").split())
        by = re.search(r"\bby\s+(.+?)(?:\s+to\s+|$)", who)
        to = re.search(r"\bto\s+(.+)$", who)
        r["seller"] = by.group(1).strip() if by else None
        r["buyer"] = to.group(1).strip() if to else "Undisclosed"
        if m.group("vv"):
            extra.append(f"VesselsValue value USD {float(m.group('vv').replace(',', '.')):.2f}m")
        r["_warnings"].append("read from an image: check the figures")
        if len(ships) > 1:
            # Sister ships in one sentence: one row per ship, the package price split equally.
            total = r["price_musd"]
            for name in ships:
                twin = {**r, "vessel": name, "en_bloc": "Y", "price_musd": round(total / len(ships), 4),
                        "_warnings": list(r["_warnings"])}
                _finish(twin, "", "", extra + [f"package ${total:g}m for {' and '.join(ships)}; split equally"])
                twin["_warnings"] = [w for w in twin["_warnings"] if w != "en bloc: check the price split"] + [
                    f"en bloc: package ${total:g}m split equally between {len(ships)} ships; size and year given once: check"]
                sales.append(twin)
            continue
        sales.append(_finish(r, "", "", extra))
    if not sales:
        raise RuntimeError(f"no sale sentences recognised in {names}")
    return sales, []
