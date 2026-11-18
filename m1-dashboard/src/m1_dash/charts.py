"""Charts as inline SVG (no add-ons, works offline). Colours come from CSS variables set in page.py, so light and
dark themes use the same drawing. Every data mark carries a data-tip attribute that the page shows on hover."""
import datetime as dt
import math
from collections import Counter
from html import escape
from typing import List, Sequence, Tuple

from .inputs import SaleRow, ShipResult


def nice_max(v: float) -> float:
    """A round axis maximum just above v (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8 × 10^n)."""
    if v <= 0:
        return 1.0
    e = 10 ** math.floor(math.log10(v))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * e:
            return m * e
    return 10 * e


def ticks(top: float) -> List[float]:
    """Gridline values from 0 to top in round steps (1, 2, 2.5 or 5 × 10^n), four to six intervals."""
    e = 10 ** math.floor(math.log10(top))
    for k in (e / 10, e / 4, e / 5, e / 2, e, 2 * e):
        for m in (1, 2, 2.5, 5):
            step = m * k
            n = top / step
            if 4 <= n <= 6 and abs(n - round(n)) < 1e-9:
                return [round(step * i, 6) for i in range(int(round(n)) + 1)]
    return [round(top / 5 * i, 6) for i in range(6)]


def _tip(text: str) -> str:
    return f' data-tip="{escape(text, quote=True)}" tabindex="0"'


def fmt_m(v) -> str:
    return "–" if v is None else f"${v:,.2f}m"


# ---------------------------------------------------------------- age curve
def age_curve(ship: ShipResult) -> str:
    """Comparable sales (adjusted price against age at sale), the fitted curve value = a·e^(b·age), and the ship
    being valued with its value range."""
    W, H, L, R, T, B = 760, 380, 58, 24, 18, 48
    comps = ship.comparables
    if not comps or ship.a_musd is None or ship.b is None:
        return '<p class="empty">No age curve: this valuation has no fitted curve.</p>'
    ages = [c.age for c in comps] + [ship.target_age]
    x0, x1 = 0, max(ages) + 2
    ytop = nice_max(max([c.adjusted_price_musd for c in comps] + [ship.high_musd or 0]) * 1.08)
    sx = lambda a: L + (a - x0) / (x1 - x0) * (W - L - R)
    sy = lambda p: T + (1 - p / ytop) * (H - T - B)
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Age curve for {escape(ship.name)}">']
    for t in ticks(ytop):
        out.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{sy(t):.1f}" y2="{sy(t):.1f}"/>'
                   f'<text class="tick" x="{L - 8}" y="{sy(t) + 4:.1f}" text-anchor="end">{t:g}</text>')
    step = 2 if x1 <= 24 else 5
    for a in range(0, x1 + 1, step):
        out.append(f'<text class="tick" x="{sx(a):.1f}" y="{H - B + 18}" text-anchor="middle">{a}</text>')
    out.append(f'<line class="axis" x1="{L}" x2="{W - R}" y1="{H - B}" y2="{H - B}"/>')
    out.append(f'<text class="axis-title" x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle">Age at sale (years)</text>'
               f'<text class="axis-title" x="14" y="{(T + H - B) / 2}" text-anchor="middle" '
               f'transform="rotate(-90 14 {(T + H - B) / 2})">Price brought to the valuation date ($m)</text>')
    lo, hi = max(0, min(ages) - 1), max(ages) + 1
    pts = " ".join(f"{sx(lo + i * (hi - lo) / 60):.1f},{sy(ship.a_musd * math.exp(ship.b * (lo + i * (hi - lo) / 60))):.1f}"
                   for i in range(61))
    out.append(f'<polyline class="curve" points="{pts}"/>')
    for c in sorted(comps, key=lambda c: c.age):
        tip = (f"{c.vessel} · age {c.age} · reported {c.report_date:%d %b %Y} · sold ${c.price_musd:g}m"
               f" · brought to valuation date ${c.adjusted_price_musd:.2f}m")
        out.append(f'<circle class="dot"{_tip(tip)} cx="{sx(c.age):.1f}" cy="{sy(c.adjusted_price_musd):.1f}" r="5"/>')
    if ship.value_musd is not None:
        x = sx(ship.target_age)
        if ship.low_musd is not None and ship.high_musd is not None:
            out.append(f'<line class="whisker" x1="{x:.1f}" x2="{x:.1f}" y1="{sy(ship.high_musd):.1f}" y2="{sy(ship.low_musd):.1f}"/>'
                       f'<line class="whisker" x1="{x - 7:.1f}" x2="{x + 7:.1f}" y1="{sy(ship.high_musd):.1f}" y2="{sy(ship.high_musd):.1f}"/>'
                       f'<line class="whisker" x1="{x - 7:.1f}" x2="{x + 7:.1f}" y1="{sy(ship.low_musd):.1f}" y2="{sy(ship.low_musd):.1f}"/>')
        y = sy(ship.value_musd)
        tip = (f"{ship.name} · age {ship.target_age} · value {fmt_m(ship.value_musd)}"
               f" (range {fmt_m(ship.low_musd)} to {fmt_m(ship.high_musd)})")
        out.append(f'<path class="target"{_tip(tip)} d="M{x:.1f},{y - 9:.1f} L{x + 9:.1f},{y:.1f} L{x:.1f},{y + 9:.1f} L{x - 9:.1f},{y:.1f} Z"/>')
        anchor, dx = ("end", -14) if x > W * 0.7 else ("start", 14)
        out.append(f'<text class="direct" x="{x + dx:.1f}" y="{y - 12:.1f}" text-anchor="{anchor}">{escape(ship.name)}: {fmt_m(ship.value_musd)}</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- range strip (ship table)
def range_strip(ship: ShipResult, lo: float, hi: float) -> str:
    W, H, P = 170, 22, 6
    if ship.value_musd is None or hi <= lo:
        return ""
    s = lambda v: P + (v - lo) / (hi - lo) * (W - 2 * P)
    out = [f'<svg class="strip" viewBox="0 0 {W} {H}" aria-hidden="true">']
    if ship.low_musd is not None and ship.high_musd is not None:
        out.append(f'<line class="strip-range" x1="{s(ship.low_musd):.1f}" x2="{s(ship.high_musd):.1f}" y1="11" y2="11"/>')
    out.append(f'<circle class="strip-dot" cx="{s(ship.value_musd):.1f}" cy="11" r="5"/></svg>')
    return "".join(out)


# ---------------------------------------------------------------- database growth
def growth(rows: Sequence[SaleRow]) -> str:
    """Sales in the database, cumulative by report date."""
    if not rows:
        return '<p class="empty">Database page needs --data (the M1_Data/clean folder).</p>'
    W, H, L, R, T, B = 760, 300, 58, 24, 18, 44
    per_day = Counter(r.report_date for r in rows)
    days = sorted(per_day)
    cum, total = [], 0
    for d in days:
        total += per_day[d]
        cum.append((d, total))
    d0, d1 = days[0], days[-1]
    span = max((d1 - d0).days, 1)
    ytop = nice_max(total * 1.05)
    sx = lambda d: L + (d - d0).days / span * (W - L - R)
    sy = lambda v: T + (1 - v / ytop) * (H - T - B)
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Sales in the database by report date">']
    for t in ticks(ytop):
        out.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{sy(t):.1f}" y2="{sy(t):.1f}"/>'
                   f'<text class="tick" x="{L - 8}" y="{sy(t) + 4:.1f}" text-anchor="end">{t:g}</text>')
    m = dt.date(d0.year, d0.month, 1)
    while m <= d1:
        if m >= d0:
            out.append(f'<text class="tick" x="{sx(m):.1f}" y="{H - B + 18}" text-anchor="middle">{m:%b}</text>')
        m = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    out.append(f'<line class="axis" x1="{L}" x2="{W - R}" y1="{H - B}" y2="{H - B}"/>')
    path = " ".join(f"{sx(d):.1f},{sy(v):.1f}" for d, v in cum)
    out.append(f'<polyline class="line" points="{path}"/>')
    for d, v in cum:
        out.append(f'<circle class="hit"{_tip(f"{d:%d %b %Y}: {per_day[d]} sales reported · {v} in total")} '
                   f'cx="{sx(d):.1f}" cy="{sy(v):.1f}" r="9"/>')
    d, v = cum[-1]
    out.append(f'<circle class="line-end" cx="{sx(d):.1f}" cy="{sy(v):.1f}" r="5"/>'
               f'<text class="direct" x="{sx(d) - 10:.1f}" y="{sy(v) - 12:.1f}" text-anchor="end">{v} sales</text>')
    out.append("</svg>")
    return "".join(out)


def segment_bars(rows: Sequence[SaleRow]) -> str:
    """Sales by segment, largest first (one series, one colour); beyond 20 segments the rest are summed as Other."""
    if not rows:
        return ""
    counts: List[Tuple[str, int]] = Counter(r.segment for r in rows).most_common()
    top = counts[:20]
    rest = sum(n for _, n in counts[20:])
    if rest:
        top.append(("Other", rest))
    W, bar, gap, L, R = 470, 16, 6, 112, 40
    H = len(top) * (bar + gap) + 8
    mx = max(n for _, n in top)
    out = [f'<svg class="chart bars" viewBox="0 0 {W} {H}" role="img" aria-label="Sales by segment">']
    for i, (seg, n) in enumerate(top):
        y = 4 + i * (bar + gap)
        w = max(2, n / mx * (W - L - R))
        out.append(f'<text class="cat" x="{L - 10}" y="{y + bar / 2 + 4}" text-anchor="end">{escape(seg)}</text>'
                   f'<rect class="bar"{_tip(f"{seg}: {n} sales")} x="{L}" y="{y}" width="{w:.1f}" height="{bar}" rx="4"/>'
                   f'<text class="val" x="{L + w + 6:.1f}" y="{y + bar / 2 + 4}">{n}</text>')
    out.append("</svg>")
    return "".join(out)
