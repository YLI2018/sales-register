"""The M1 valuation, step by step. Each function matches a column or cell of the Excel template, named in its docstring,
so every Python number can be checked against Excel (docs/adr/0003-names-follow-excel.md).

Order of the steps:
    benchmark_table      -> Benchmarks table 1 (OK dates and values)
    nearest_ok_date      -> Sales Register AB; Benchmarks B72 (valuation-date benchmark)
    age_at_sale          -> Sales Register S
    failed_rules         -> Sales Register AG (rules R1-R6)
    automatic_screen     -> Sales Register W
    decision_used        -> Sales Register AH
    benchmark_age        -> Sales Register AD
    adjusted_price       -> Sales Register AC (index_factor inside)
    fit_curve            -> Age Curve O5 (a), O6 (b), O8 (R squared), O12 (SD); the fit itself is the shared M1 code
    value_ship           -> Age Curve O11-O20 and Outputs C29-C38 (validity checks, status)

Information cutoff: a valuation uses only sales and broker values reported on or before its valuation date. Later rows
are left out before any step (no comparable and no benchmark from after the date), and the counts left out are recorded.
"""
import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .inputs import BrokerValue, Parameters, Sale, Ship
from .shared_m1 import fit_age_curve


# ---------------------------------------------------------------- benchmarks
@dataclass
class BenchmarkTable:
    """The active benchmark series: for each OK report date, the values at the three benchmark ages (in label order)."""
    values: Dict[dt.date, List[float]]

    @property
    def ok_dates(self) -> List[dt.date]:
        return sorted(self.values)


def benchmark_table(broker_values: List[BrokerValue], p: Parameters) -> BenchmarkTable:
    """Benchmarks table 1: every report date of the provider and segment on Parameters. A date is OK only when each of the
    three age labels has exactly one value (none = Missing, more than one = Duplicate, both excluded)."""
    rows = [b for b in broker_values if b.broker == p.benchmark_provider and b.segment == p.benchmark_segment]
    table = {}
    for d in sorted({b.report_date for b in rows}):
        per_age = [[b.value_musd for b in rows if b.report_date == d and b.age == lab] for lab in p.benchmark_labels]
        if all(len(v) == 1 for v in per_age):
            table[d] = [v[0] for v in per_age]
    return BenchmarkTable(table)


def nearest_ok_date(day: dt.date, bt: BenchmarkTable) -> Optional[dt.date]:
    """Sales Register AB: the OK benchmark date nearest to `day`; on a tie the earlier date. None if there is no OK date."""
    before = [d for d in bt.ok_dates if d <= day]
    after = [d for d in bt.ok_dates if d >= day]
    if not before and not after:
        return None
    if not before:
        return after[0]
    if not after:
        return before[-1]
    return before[-1] if (day - before[-1]) <= (after[0] - day) else after[0]


# ---------------------------------------------------------------- rules and decisions
def age_at_sale(s: Sale) -> int:
    """Sales Register S: report year minus year built."""
    return s.report_date.year - s.built


def _in_notes(s: Sale, keyword: str) -> bool:
    return keyword.lower() in f"{s.features} {s.notes}".lower()


def failed_rules(s: Sale, p: Parameters, name_seen_before: bool) -> List[str]:
    """Sales Register AG: the rules R1-R6 this sale fails under the segment's parameters (empty list = passes all).

    R1 size band with tolerance; R2 resale or younger than the minimum age; R3 no exact price; R4 a charter keyword in
    features or notes; R5 older than the maximum age; R6 the same name already listed earlier in the same segment.
    """
    age = age_at_sale(s)
    fails = []
    if s.dwt is None or s.dwt < p.dwt_min * (1 - p.dwt_tolerance) or s.dwt > p.dwt_max * (1 + p.dwt_tolerance):
        fails.append("R1")
    if s.sale_type == "Resale" or age < p.age_min:
        fails.append("R2")
    if s.price_musd is None:
        fails.append("R3")
    if any(_in_notes(s, k) for k in p.charter_keywords):
        fails.append("R4")
    if age > p.age_max:
        fails.append("R5")
    if name_seen_before:
        fails.append("R6")
    return fails


def automatic_screen(s: Sale, p: Parameters, fails: List[str]) -> str:
    """Sales Register W (for a row of the target's segment that is not the target): No if any rule fails; Review if en
    bloc or a review keyword is in the notes; otherwise Yes."""
    if fails:
        return "No"
    if s.en_bloc == "Y" or any(_in_notes(s, k) for k in p.review_keywords):
        return "Review"
    return "Yes"


def decision_used(s: Sale, screen: str, use_reviewed: bool) -> Tuple[str, str]:
    """Sales Register AH and AI: (decision, source). A reviewed decision in Z overrides the screen when the case says so
    (except 'Target', which belongs to the ship it was written for). An undecided Review stays 'Review: decide in Z'."""
    if use_reviewed and s.reviewed_decision and s.reviewed_decision != "Target":
        return s.reviewed_decision, "Reviewed (Z)"
    if screen == "Review":
        return "Review: decide in Z", "Automatic (W)"
    return screen, "Automatic (W)"


def benchmark_age(age: float, p: Parameters) -> int:
    """Sales Register AD, as an index 0/1/2 into the benchmark labels: cut-offs halfway between the three benchmark ages."""
    a1, a2, a3 = p.benchmark_ages
    if age < (a1 + a2) / 2:
        return 0
    if age < (a2 + a3) / 2:
        return 1
    return 2


# ---------------------------------------------------------------- comparables
@dataclass
class Comparable:
    """One comparable sale as used in the fit (Age Curve row)."""
    sale: Sale
    age_at_sale: int
    benchmark_date: dt.date
    benchmark_age_label: str
    index_factor: float
    adjusted_price_musd: float
    days_to_benchmark: int
    decision_source: str
    log_price: float = 0.0
    age_gap: float = 0.0
    log_price_gap: float = 0.0
    fitted_price_musd: float = 0.0
    residual_musd: float = 0.0


def adjusted_price(s: Sale, bt: BenchmarkTable, valuation_benchmark: dt.date, p: Parameters):
    """Sales Register AB, AD, AC: (benchmark date, age index, index factor, adjusted price). The index factor is the
    benchmark on the valuation-date benchmark date divided by the benchmark on the sale's benchmark date, same age."""
    ab = nearest_ok_date(s.report_date, bt)
    k = benchmark_age(age_at_sale(s), p)
    factor = bt.values[valuation_benchmark][k] / bt.values[ab][k]
    return ab, k, factor, s.price_musd * factor


@dataclass
class Selection:
    """The outcome of the screening for one case."""
    comparables: List[Comparable]
    undecided_reviews: int
    decisions: Dict[int, Tuple[str, str, List[str]]]   # sale id -> (decision used, source, failed rules)


def select_comparables(sales: List[Sale], ship: Ship, p: Parameters, bt: BenchmarkTable,
                       valuation_benchmark: dt.date) -> Selection:
    """Apply rules and decisions to every sale of the segment, in file order, and index the Yes rows."""
    seen, comps, undecided, decisions = set(), [], 0, {}
    for s in sales:
        if s.segment != ship.segment:
            continue
        seen_before = s.vessel in seen
        seen.add(s.vessel)
        if s.vessel == ship.target_name:
            decisions[s.id] = ("Target", "Inputs", [])
            continue
        fails = failed_rules(s, p, seen_before)
        decision, source = decision_used(s, automatic_screen(s, p, fails), ship.use_reviewed_decisions)
        decisions[s.id] = (decision, source, fails)
        if decision == "Review: decide in Z":
            undecided += 1
        if decision != "Yes" or s.price_musd is None:
            continue
        ab, k, factor, adj = adjusted_price(s, bt, valuation_benchmark, p)
        comps.append(Comparable(s, age_at_sale(s), ab, p.benchmark_labels[k], factor, adj,
                                abs((s.report_date - ab).days), source))
    return Selection(comps, undecided, decisions)


# ---------------------------------------------------------------- curve and value
@dataclass
class Curve:
    """Age Curve O5 (a_musd), O6 (b), O8 (r_squared), O12 (sd_musd), with the averages used by the hand calculation
    (AB10-AB13). a, b, R squared and SD come from the shared M1 fit."""
    a_musd: float
    b: float
    r_squared: float
    mean_age: float
    mean_log_price: float
    sum_age_gap_x_log_price_gap: float
    sum_age_gap_squared: float
    sd_musd: float = 0.0

    @property
    def loss_rate(self) -> float:
        """Age Curve O7: value lost per year = 1 - e^b."""
        return 1 - math.exp(self.b)

    def fitted_price(self, age: float) -> float:
        """Age Curve F: a x e^(b x age)."""
        return self.a_musd * math.exp(self.b * age)


def fit_curve(comps: List[Comparable]) -> Curve:
    """Ordinary least squares of LN(adjusted price) on age, done by the shared M1 fit (fit_age_curve):
    b = sum(age gap x log price gap) / sum(age gap squared); intercept = mean log price - b x mean age; a = e^intercept.
    Raises ValueError when no curve can be fitted (fewer than 3 sales, all the same age, a price not above 0).
    The gap columns below are only for the Age Curve sheet's hand calculation."""
    m1 = fit_age_curve([c.age_at_sale for c in comps], [c.adjusted_price_musd for c in comps])
    for c in comps:
        c.log_price = math.log(c.adjusted_price_musd)
    n = len(comps)
    mean_age = sum(c.age_at_sale for c in comps) / n
    mean_lp = sum(c.log_price for c in comps) / n
    for c in comps:
        c.age_gap, c.log_price_gap = c.age_at_sale - mean_age, c.log_price - mean_lp
    sxy = sum(c.age_gap * c.log_price_gap for c in comps)
    sxx = sum(c.age_gap ** 2 for c in comps)
    curve = Curve(m1.a, m1.b, m1.r_squared, mean_age, mean_lp, sxy, sxx, m1.sd)
    for c in comps:
        c.fitted_price_musd = curve.fitted_price(c.age_at_sale)
        c.residual_musd = c.adjusted_price_musd - c.fitted_price_musd
    return curve


@dataclass
class Result:
    """One valuation: the numbers on the Outputs sheet, the validity checks and the comparables behind them."""
    ship: Ship
    target_age: int
    status: str
    checks: Dict[str, str] = field(default_factory=dict)
    value_musd: Optional[float] = None
    range_low_musd: Optional[float] = None
    range_high_musd: Optional[float] = None
    sd_residuals_musd: Optional[float] = None
    curve: Optional[Curve] = None
    n_comparables: int = 0
    near_age_average_musd: Optional[float] = None
    near_age_count: int = 0
    known_gap_pct: Optional[float] = None
    valuation_benchmark_date: Optional[dt.date] = None
    parameters_status: str = ""
    information_cutoff: Optional[dt.date] = None
    sales_after_cutoff: int = 0
    broker_values_after_cutoff: int = 0
    comparables: List[Comparable] = field(default_factory=list)
    message: str = ""


def value_ship(ship: Ship, sales: List[Sale], broker_values: List[BrokerValue], params: Dict[str, Parameters]) -> Result:
    """Value one ship: Age Curve O11-O20 and the validity checks of Outputs C29-C38 with the overall status (C32)."""
    target_age = ship.valuation_date.year - ship.year_built
    p = params.get(ship.segment)
    if p is None:
        return Result(ship, target_age, "NOT VALID: see failed checks", message=f"segment {ship.segment} has no Parameters row")
    cutoff = ship.valuation_date
    seg_sales = [s for s in sales if s.segment == ship.segment]
    seg_values = [b for b in broker_values if b.broker == p.benchmark_provider and b.segment == p.benchmark_segment]
    sales = [s for s in sales if s.report_date <= cutoff]
    broker_values = [b for b in broker_values if b.report_date <= cutoff]
    bt = benchmark_table(broker_values, p)
    vb = nearest_ok_date(ship.valuation_date, bt)
    res = Result(ship, target_age, "", valuation_benchmark_date=vb, parameters_status=p.status, information_cutoff=cutoff,
                 sales_after_cutoff=sum(1 for s in seg_sales if s.report_date > cutoff),
                 broker_values_after_cutoff=sum(1 for b in seg_values if b.report_date > cutoff))
    vb_ok = vb is not None and abs((ship.valuation_date - vb).days) <= p.benchmark_max_days
    if vb is None:
        res.status, res.message = "NOT VALID: see failed checks", "no OK benchmark date for this segment"
        res.checks["Valuation-date benchmark within max days"] = "Fail"
        return res
    sel = select_comparables(sales, ship, p, bt, vb)
    comps = sel.comparables
    res.comparables, res.n_comparables = comps, len(comps)
    try:
        curve = fit_curve(comps)
    except ValueError as e:
        curve = None
        res.message = f"no age curve: {e}"
    if curve is not None:
        res.curve = curve
        res.value_musd = curve.fitted_price(target_age)
        res.sd_residuals_musd = curve.sd_musd
        res.range_low_musd = res.value_musd - p.range_sd * res.sd_residuals_musd
        res.range_high_musd = res.value_musd + p.range_sd * res.sd_residuals_musd
        near = [c.adjusted_price_musd for c in comps if abs(c.age_at_sale - target_age) <= p.near_age_window]
        res.near_age_count = len(near)
        res.near_age_average_musd = sum(near) / len(near) if near else None
        if ship.known_price_musd is not None:
            res.known_gap_pct = ship.known_price_musd / res.value_musd - 1
    ages = [c.age_at_sale for c in comps]
    far = sum(1 for c in comps if c.days_to_benchmark > p.benchmark_max_days)
    pf = lambda ok: "Pass" if ok else "Fail"
    res.checks = {
        "Comparables at least the minimum": pf(len(comps) >= p.min_comparables),
        "Target age inside the comparables' age range": pf(bool(ages) and min(ages) <= target_age <= max(ages)),
        "R squared at least the minimum": pf(res.curve is not None and res.curve.r_squared >= p.min_r_squared),
        "Valuation-date benchmark within max days": pf(vb_ok),
        "Comparables' benchmark dates within max days": pf(far == 0),
        "Review rows decided": pf(sel.undecided_reviews == 0),
        "Target DWT inside the segment band": pf(p.dwt_min * (1 - p.dwt_tolerance) <= ship.dwt <= p.dwt_max * (1 + p.dwt_tolerance)),
        "Value falls with age (b below 0)": pf(res.curve is not None and res.curve.b < 0),
        "Segment parameters validated": "Pass" if p.status.startswith("Validated") else "Warning",
    }
    if "Fail" in res.checks.values():
        res.status = "NOT VALID: see failed checks"
    elif "Warning" in res.checks.values():
        res.status = "Usable with warning (draft parameters)"
    else:
        res.status = "VALID"
    if sel.undecided_reviews:
        res.message = "; ".join(m for m in (res.message, f"{sel.undecided_reviews} sales need a reviewed decision") if m)
    return res
