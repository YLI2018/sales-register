"""M3 Acquisition and finance page: reads the newest M3 results file (M3_results_<base date>_<version>.json, written by
the M3 workbook's export script) and shows the deal, the bank tests, the maximum bid, the sensitivities and where the
numbers came from (model version, file fingerprint, data used)."""
import json
from html import escape
from pathlib import Path

from .inputs import InputError

SCHEMA = "m3-results/1"


def read_m3(folder):
    """Newest M3 results file in `folder` (or the file itself); None if no folder was given."""
    if folder is None:
        return None
    folder = Path(folder)
    if folder.is_file():
        path = folder
    else:
        files = sorted(folder.glob("M3_results_*.json"), key=lambda p: p.stat().st_mtime)
        if not files:
            raise InputError(f"no M3_results_*.json in {folder}")
        path = files[-1]
    try:
        j = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"cannot read {path.name}: {exc}") from exc
    if j.get("schema") != SCHEMA:
        raise InputError(f"{path.name}: unknown schema {j.get('schema')!r} (expected {SCHEMA})")
    j["_file"] = path.name
    return j


def _pct(x, d=1):
    return "n/a" if not isinstance(x, (int, float)) else f"{x:.{d}%}"


def _m(x, d=2):
    return "–" if not isinstance(x, (int, float)) else f"{x:,.{d}f}"


def _status(ok, text: str) -> str:
    kind, icon = {True: ("good", "✓"), False: ("critical", "✕"), None: ("warning", "!")}[ok]
    return f'<span class="status {kind}"><b>{icon}</b>{escape(text)}</span>'


def _tile(label, value, note=""):
    return (f'<div class="tile"><div class="tile-label">{escape(label)}</div><div class="tile-value">{value}</div>'
            + (f'<div class="tile-note">{escape(note)}</div>' if note else "") + "</div>")


def page(j) -> str:
    if j is None:
        return ('<section id="p-m3" class="page"><h2>Acquisition and finance (M3)</h2>'
                '<p class="empty">Run with --m3 (the M3 results folder) to see this page.</p></section>')
    r = {k: v["value"] for k, v in j["results"].items()}
    i = {k: v["value"] for k, v in j["inputs"].items()}
    case, model = j["case"], j["model"]
    ke, irr = i.get("I_Hurdle"), r.get("R_Eq_IRR")
    tiles = (_tile("Equity IRR", _pct(irr), f"owners' required return {_pct(ke, 2)}")
             + _tile("Maximum bid", f"${_m(r.get('R_Max_Bid'))}m",
                     f"price tested ${_m(case['price_tested_musd'])}m · limited by {r.get('R_Bid_Binding')}")
             + _tile("Lowest debt service cover", f"{_m(r.get('R_Min_DSCR'))}×",
                     f"minimum {_m(i.get('I_Min_DSCR'))}× (assumed)")
             + _tile("Value-rule headroom", _pct(r.get("R_Cov_Headroom")),
                     f"value can fall {_pct(r.get('R_Max_Fall'))} before the bank's rule breaks"))
    verdicts = [("Model works (formulas, links, totals)", r.get("R_Model_OK")),
                ("Bank rules at this price", r.get("R_Bank_OK")),
                ("Inputs still placeholders", r.get("R_Data_OK")),
                ("Deal earns the required return", r.get("R_Deal_OK"))]
    def state(lab, v):
        if "warning" in str(v).lower():
            return None, "Warning"
        if str(v).startswith(("PASS", "YES", "none")):
            return True, "OK"
        return (None, "Warning") if lab.startswith("Inputs still") else (False, "Not met")
    vlist = "".join(f'<li>{_status(*state(lab, v))}<span>{escape(lab)}: <b>{escape(str(v))}</b></span></li>'
                    for lab, v in verdicts)

    by = j["by_year"]
    yrs = by["years"]
    show = [("Operating cash after carbon", "Ship cash"), ("Interest", "Interest"), ("Scheduled repayment", "Repayment"),
            ("Balloon (repaid from the sale)", "Balloon"), ("Sale proceeds after commission", "Sale, after commission"),
            ("Cash to / from our equity", "Owners' cash"), ("Debt service cover", "Debt service cover ×")]
    head = "".join(f'<th class="num">Year {y}</th>' for y in yrs)
    body = ""
    for key, lab in show:
        vals = by.get(key, [])
        cells = "".join(f'<td class="num">{"" if v is None else (_m(v) if key == "Debt service cover" else _m(v, 3))}</td>'
                        for v in vals)
        b = ' style="font-weight:650"' if key == "Cash to / from our equity" else ""
        body += f"<tr{b}><td>{escape(lab)}</td>{cells}</tr>"
    cash = f'<table class="tbl"><thead><tr><th>$m</th>{head}</tr></thead><tbody>{body}</tbody></table>'

    bids = (f'<table class="tbl"><thead><tr><th>Bid</th><th>Rule</th><th class="num">$m</th></tr></thead><tbody>'
            f'<tr><td>Return bid</td><td>Equity IRR = required return</td><td class="num">{_m(r.get("R_Bid_IRR"))}</td></tr>'
            f'<tr><td>Value-rule bid</td><td>Value ≥ {_m(i.get("I_MVC"))} × loan every year</td>'
            f'<td class="num">{_m(r.get("R_Bid_Cov"), 1)}</td></tr>'
            f'<tr><td>Debt-service bid</td><td>Cover ≥ {_m(i.get("I_Min_DSCR"))}× every year</td>'
            f'<td class="num">{_m(r.get("R_Bid_DSCR"), 1)}</td></tr>'
            f'<tr style="font-weight:650"><td>Maximum bid</td><td>Lowest of the three</td>'
            f'<td class="num">{_m(r.get("R_Max_Bid"))}</td></tr>'
            + (f'<tr><td>Re-test at the maximum bid</td><td>All three tests run again at that price</td>'
               f'<td class="num">{escape(str(r["R_Bid_Retest"]))}</td></tr>' if "R_Bid_Retest" in r else "")
            + '</tbody></table><p class="sub">A bid equal to the top of the price grid means no limit was found '
              'inside the grid. Monthly liquidity is tested separately and is not part of the maximum bid.</p>')

    a = j["sensitivities"]["A_equity_irr_hire_x_sale"]
    ahead = "".join(f'<th class="num">Sale {c:+.0%}</th>' for c in a["columns"])
    arows = ""
    for t, row in zip(a["rows"], a["values"]):
        cells = ""
        for k, v in enumerate(row):
            base = t == 0 and a["columns"][k] == 0
            meets = isinstance(v, (int, float)) and ke is not None and v >= ke
            style = ' style="background:var(--chip);font-weight:700"' if base else (' style="font-weight:700"' if meets else "")
            tip = f'Hire {t:+,.0f} $/day, sale {a["columns"][k]:+.0%}: equity IRR {_pct(v)}'
            cells += f'<td class="num"{style} data-tip="{escape(tip)}" tabindex="0">{_pct(v)}</td>'
        arows += f'<tr><td>Hire {t:+,.0f} $/day</td>{cells}</tr>'
    sens = (f'<table class="tbl"><thead><tr><th></th>{ahead}</tr></thead><tbody>{arows}</tbody></table>'
            f'<p class="sub">Shaded = base case. Bold = meets the {_pct(ke, 2)} required return. '
            f'n/a = no return can be worked out (very little of the money comes back).</p>')

    data = "".join(f'<tr><td>{escape(d["what"])}</td><td>{escape(d["source"])}</td></tr>' for d in j["data_used"])
    prov = (f'<table class="tbl"><tbody>'
            f'<tr><td>Model file</td><td>{escape(model["file"])} (saved {escape(model["file_saved"])})</td></tr>'
            f'<tr><td>Fingerprint (SHA-256)</td><td><code>{escape(model["sha256"][:16])}…</code></td></tr>'
            f'<tr><td>Results file</td><td>{escape(j["_file"])} (made {escape(j["made"])})</td></tr>'
            f'<tr><td>Specification</td><td>{escape(model.get("spec") or "")}</td></tr>'
            f'{data}</tbody></table>')

    return (f'<section id="p-m3" class="page"><h2>Acquisition and finance (M3)</h2>'
            f'<p class="lead">{escape(case["description"])}, bought at ${_m(case["price_tested_musd"])}m on '
            f'{escape(case["base_date"])}, {escape(str(case["employment"]).lower())}, '
            f'{_pct(i.get("I_LTV"), 0)} loan, sold after {case["hold_years"]} years.</p>'
            f'<div class="tiles">{tiles}</div>'
            f'<div class="grid2"><div class="card"><h3>Owners\' cash and the bank, year by year</h3>{cash}</div>'
            f'<div class="card"><h3>Verdicts</h3><ul class="checks">{vlist}</ul>'
            f'<p class="sub">A "not met" bank rule or return is a result for this deal, not a model error.</p></div></div>'
            f'<div class="grid2"><div class="card"><h3>Equity IRR: hire change × sale value change</h3>{sens}</div>'
            f'<div class="card"><h3>Maximum bid</h3>{bids}</div></div>'
            f'<div class="card"><h3>Where these numbers come from</h3>{prov}</div></section>')
