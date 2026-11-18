"""Turn broker text into contract values: numbers, prices, yards, segments, survey dates and names."""
import re
from typing import Optional, Tuple

COUNTRIES = {"korea": "Korea", "s. korea": "Korea", "south korea": "Korea", "japan": "Japan", "china": "China",
             "taiwan": "Taiwan", "vietnam": "Vietnam", "philippines": "Philippines", "croatia": "Croatia",
             "denmark": "Denmark", "germany": "Germany", "romania": "Romania", "turkey": "Turkey", "india": "India",
             "poland": "Poland", "italy": "Italy", "spain": "Spain", "norway": "Norway", "netherlands": "Netherlands",
             "singapore": "Singapore", "indonesia": "Indonesia", "bulgaria": "Bulgaria"}


def size_number(text: str) -> Optional[int]:
    """'81.504', '158,517', '63.500' or '2797' as a whole number of tonnes (or TEU)."""
    t = re.sub(r"[^\d.,]", "", text or "")
    if not t:
        return None
    digits = re.sub(r"[.,]", "", t)
    return int(digits) if digits.isdigit() else None


def price(text: str) -> Tuple[Optional[float], str]:
    """Parse a price cell. Returns (exact $m or None, remark).
    Exact: '$ 20,5m', '$ 9,294m', '110', '24.4', '$ 110.0m'. Approximate ('rgn', 'high', 'low', 'xs', 'excess',
    'region', 'mid', 'about'): no exact price; the text goes to the remark, as in the M1 typing convention."""
    raw = (text or "").strip()
    if not raw:
        return None, ""
    low = raw.lower()
    if re.search(r"\b(rgn|region|high|low|xs|excess|mid|about|abt|approx|undisclosed|n/?a)\b", low):
        return None, f"Approximate price: {raw}"
    m = re.search(r"(\d+(?:[.,]\d+)?)", raw)
    if not m:
        if re.search(r"en ?bloc", low):
            return None, "Price given for the package (en bloc): see the partner row"
        return None, f"Price not read: {raw}"
    value = float(m.group(1).replace(",", "."))
    note = ""
    if re.search(r"\beach\b|\ben ?bloc\b", low):
        note = f"Price as reported: {raw}"
    return value, note


def yard_and_country(text: str) -> Tuple[str, str]:
    """'Hyundai Samho, Korea' -> ('Hyundai Samho', 'Korea'); 'HYUNDAI, S. Korea' -> ('Hyundai', 'Korea')."""
    t = " ".join((text or "").split())
    if "," in t:
        yard, country = t.rsplit(",", 1)
        c = COUNTRIES.get(country.strip().lower())
        if c:
            return title_case(yard.strip()), c
    return title_case(t), ""


CODES = {"STI", "SPP", "STX", "GSI", "HHI", "SWS", "MSC", "CSC", "BW", "NYK", "MOL", "COSCO", "CMB", "IMC", "MAN"}
SMALL = {"of", "and", "the", "for", "to", "de"}


def word_case(w: str, first: bool) -> str:
    """One word of an all-capitals name: codes stay in capitals (LS, CS, HV, STI), small words lower case, others capitalised."""
    if not first and w.lower() in SMALL:
        return w.lower()
    if w in CODES or (len(w) <= 2 and w.isalpha()) or (w.isalpha() and not any(v in w for v in "AEIOUY")):
        return w
    return w.capitalize()


def title_case(text: str) -> str:
    """'HYUNDAI MIPO' -> 'Hyundai Mipo'; 'CLIENTS OF ACME' -> 'Clients of Acme'; mixed-case text is left as it is."""
    t = " ".join((text or "").split())
    if t.isupper():
        return " ".join(word_case(w, i == 0) for i, w in enumerate(t.split()))
    return t


def ship_name(text: str) -> str:
    """Ship names in title case as typed in M1 ('LS EXAMPLE' -> 'LS Example', 'DEMO NENG 16' -> 'Demo Neng 16')."""
    t = " ".join((text or "").replace("\u201c", "").replace("\u201d", "").replace('"', "").split())
    return title_case(t)


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def survey_date(text: str) -> Optional[str]:
    """'02/2027' or 'Feb-27' or 'Feb 2027' -> '2027-02-01' (first of the month, the M1 convention)."""
    t = (text or "").strip()
    m = re.search(r"\b(\d{1,2})/(20\d{2})\b", t)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{m.group(2)}-{int(m.group(1)):02d}-01"
    m = re.search(r"\b([A-Za-z]{3})[a-z]*[-\s'’]*(\d{2,4})\b", t)
    if m and m.group(1).lower() in MONTHS:
        y = int(m.group(2))
        y = y + 2000 if y < 100 else y
        return f"{y}-{MONTHS[m.group(1).lower()]:02d}-01"
    return None


TANKER_CODES = {"VLCC": "VLCC", "SUEZ": "Suezmax", "SUEZMAX": "Suezmax", "AFRA": "Aframax", "AFRAMAX": "Aframax",
                "LR2": "LR2", "LR1": "LR1", "MR": "MR", "MR2": "MR", "MR1": "MR", "PANAMAX": "Panamax tanker",
                "HANDY": "Handy tanker", "SMALL": "Chemical tanker"}
BULK_CODES = {"CAPE": "Capesize", "CAPESIZE": "Capesize", "NEWCASTLEMAX": "Capesize", "POST": "Post Panamax",
              "KMAX": "Kamsarmax", "KAMSARMAX": "Kamsarmax", "PMAX": "Panamax", "PANAMAX": "Panamax", "UMAX": "Ultramax",
              "ULTRAMAX": "Ultramax", "SUPRA": "Supramax", "SUPRAMAX": "Supramax", "HANDY": "Handysize", "HANDYSIZE": "Handysize"}


def segment_from_type(type_text: str, table: str) -> Optional[str]:
    """Segment from a broker's type or size code, using the table (tanker / bulk / container) to settle 'Panamax'."""
    t = re.sub(r"[^A-Za-z0-9 /]", "", type_text or "").upper().replace(" ", "")
    if table == "container":
        return "Container"
    if table == "tanker":
        if t.startswith("CHEM") or "CHEMOIL" in t:
            return "Chemical tanker"
        if t == "PRODUCTS":
            return "Handy tanker"
        return TANKER_CODES.get(t)
    return BULK_CODES.get(t) or ({"POSTPANAMAX": "Post Panamax"}.get(t))


def segment_from_size(dwt: Optional[int], table: str) -> Optional[str]:
    """Segment from DWT when the report gives no type (Xclusiv). Border cases are flagged by the caller."""
    if dwt is None:
        return None
    if table == "tanker":
        for low, seg in ((200_000, "VLCC"), (120_000, "Suezmax"), (85_000, "Aframax"), (60_000, "LR1"),
                         (42_000, "MR"), (25_000, "Handy tanker"), (0, "Chemical tanker")):
            if dwt >= low:
                return seg
    if table == "bulk":
        for low, seg in ((150_000, "Capesize"), (85_000, "Post Panamax"), (78_000, "Kamsarmax"), (68_000, "Panamax"),
                         (60_000, "Ultramax"), (50_000, "Supramax"), (0, "Handysize")):
            if dwt >= low:
                return seg
    return None


def norm_key(name: str) -> str:
    """A ship name reduced for matching: lower case, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())
