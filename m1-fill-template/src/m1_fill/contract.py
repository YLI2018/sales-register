"""The data contract: what the input files must contain and where each field goes in the template.

This module is the single source of truth for the file formats. docs/data_dictionary.md describes the same
contract in words; tests/test_contract.py checks that the two agree on column names.

Files (UTF-8, comma-separated, first row = column names exactly as below):
    sales.csv              one row per sale        -> sheet 'Sales Register', rows 5-304
    indicative_prices.csv  one row per broker value -> sheet 'Indicative Prices', rows 5-1000
    case JSON              one valuation case       -> sheet 'Inputs', cells C5-C16

Value formats: dates YYYY-MM-DD; numbers with a dot as decimal mark and no thousands separator; empty = blank.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

TEMPLATE_VERSION = "M1_Comparable_Sales_Template_v1_blank"

SEGMENTS = ("Capesize", "Post Panamax", "Kamsarmax", "Panamax", "Ultramax", "Supramax", "Handysize", "VLCC", "Suezmax",
            "Aframax", "LR2", "LR1", "MR", "Handy tanker", "Chemical tanker", "Panamax tanker", "Container", "Gas", "Other")
YARD_COUNTRIES = ("Japan", "Korea", "China", "Taiwan", "Vietnam", "Philippines", "Other")
EN_BLOC = ("Y", "N", "Unknown")
SALE_TYPES = ("Secondhand", "Resale", "Auction")
DECISIONS = ("Yes", "No", "Target")
PURPOSES = ("Sale price guide", "Purchase bid", "Loan collateral", "Portfolio value", "Back-test")


@dataclass(frozen=True)
class Field:
    """One column of an input file.

    name:      column name in the CSV file
    column:    Excel column it is written to
    kind:      'int', 'float', 'date', 'text' or 'choice'
    required:  True = an empty value is an error
    choices:   allowed values for kind 'choice'
    limits:    (min, max) for numbers; outside = error
    warn_if_blank: True = an empty value is reported as a warning
    meaning:   one-line description (also in docs/data_dictionary.md)
    """
    name: str
    column: str
    kind: str
    required: bool = False
    choices: Tuple[str, ...] = ()
    limits: Optional[Tuple[float, float]] = None
    warn_if_blank: bool = False
    meaning: str = ""


SALES_SHEET, SALES_FIRST_ROW, SALES_LAST_ROW = "Sales Register", 5, 304
SALES_FIELDS = (
    Field("id", "A", "int", True, limits=(1, 1_000_000), meaning="Row identifier, unique"),
    Field("report_date", "B", "date", True, meaning="Date of the report that gave the sale"),
    Field("vessel", "C", "text", True, meaning="Ship name as reported"),
    Field("segment", "D", "choice", True, choices=SEGMENTS, meaning="Ship type and size class"),
    Field("dwt", "E", "int", limits=(1_000, 600_000), warn_if_blank=True, meaning="Deadweight tonnes"),
    Field("built", "F", "int", True, limits=(1950, 2035), meaning="Year built (or due for delivery)"),
    Field("shipyard", "G", "text", meaning="Shipyard"),
    Field("yard_country", "H", "text", meaning="Country of the shipyard (free text: yards exist outside the usual list, e.g. Denmark)"),
    Field("price_musd", "I", "float", limits=(0.01, 1_000), warn_if_blank=True,
          meaning="Exact reported price, $m. Blank if only an approximate price was reported (write it in notes)"),
    Field("buyer", "J", "text", meaning="Buyer as reported"),
    Field("seller", "K", "text", meaning="Seller as reported"),
    Field("features", "L", "text", meaning="Special features: scrubber, DPP, time charter attached ..."),
    Field("en_bloc", "N", "choice", choices=EN_BLOC, meaning="Y if sold as part of a package"),
    Field("sale_type", "O", "choice", True, choices=SALE_TYPES, meaning="Secondhand, Resale or Auction"),
    Field("source_file", "P", "text", True, meaning="Source report file name"),
    Field("source_url", "Q", "text", meaning="Link to the source"),
    Field("notes", "R", "text", meaning="Remarks from every report: survey dates, package details, approximate prices, conflicts"),
    Field("reviewed_decision", "Z", "choice", choices=DECISIONS, meaning="A person's decision: Yes, No or Target (optional)"),
    Field("review_reason", "AA", "text", meaning="Reason for the reviewed decision; required when a decision is given"),
    Field("next_survey", "AE", "date", meaning="Next special survey or drydock date from the notes (first of the month)"),
)

PRICES_SHEET, PRICES_FIRST_ROW, PRICES_LAST_ROW = "Indicative Prices", 5, 1000
PRICE_FIELDS = (
    Field("report_date", "A", "date", True, meaning="Report date"),
    Field("broker", "B", "text", True, meaning="Broker publishing the value, e.g. Advanced Shipping"),
    Field("segment", "C", "text", True, meaning="Segment label as the broker writes it, e.g. MR, MR2"),
    Field("size", "D", "text", meaning="Reference size, e.g. 51k"),
    Field("age", "E", "text", True, meaning="Age label exactly as used on Parameters, e.g. '5 years', 'Resale'"),
    Field("value_musd", "F", "float", True, limits=(0.01, 1_000), meaning="Published value, $m"),
    Field("compared_with", "G", "text", meaning="Earlier period the broker compares with"),
    Field("earlier_value_musd", "H", "float", limits=(0.01, 1_000), meaning="Earlier value, $m"),
    Field("basis", "I", "text", meaning="Basis of the value (e.g. monthly average)"),
    Field("source_file", "J", "text", True, meaning="Source report file name"),
)

# The case goes to sheet 'Inputs', column C.
CASE_SHEET = "Inputs"
CASE_FIELDS = (
    Field("case_id", "C5", "text", True, meaning="Case reference"),
    Field("purpose", "C6", "choice", True, choices=PURPOSES, meaning="Why the value is needed"),
    Field("target_name", "C7", "text", True, meaning="Ship to value; as in Sales Register if it has a row there"),
    Field("segment", "C8", "choice", True, choices=SEGMENTS, meaning="Must have a row on Parameters"),
    Field("dwt", "C9", "int", True, limits=(1_000, 600_000), meaning="Deadweight tonnes"),
    Field("year_built", "C10", "int", True, limits=(1950, 2035), meaning="Year built"),
    Field("shipyard", "C11", "text", meaning="Shipyard and country"),
    Field("valuation_date", "C12", "date", True, meaning="Date the value is for"),
    Field("known_price_musd", "C13", "float", limits=(0.01, 1_000), meaning="Known or offered price to test against (optional)"),
    Field("use_reviewed_decisions", "C14", "choice", True, choices=("Yes", "No"), meaning="Use Sales Register Z where filled"),
    Field("prepared_by", "C15", "text", meaning="Preparer"),
    Field("date_prepared", "C16", "date", meaning="Date prepared"),
)

# Columns written by this program; every other column of these sheets holds formulas and is never touched.
SALES_INPUT_COLUMNS = tuple(f.column for f in SALES_FIELDS)
PRICE_INPUT_COLUMNS = tuple(f.column for f in PRICE_FIELDS)
