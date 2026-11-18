"""The dashboard page: one self-contained HTML file with five pages (Overview, Ship detail, Database, Acquisition
and finance (M3), Model roadmap).
No add-ons and no internet needed; it opens in any browser and can be sent as one file."""
import datetime as dt
from collections import Counter
from html import escape
from typing import List, Sequence

from . import __version__, automation, charts, m3, roadmap
from .inputs import RunInfo, SaleRow, ShipResult

# The validity checks Calculate runs (names as in m1-calculate engine.py), in the order shown.
CHECKS = ["Comparables at least the minimum", "Target age inside the comparables' age range", "R squared at least the minimum",
          "Valuation-date benchmark within max days", "Comparables' benchmark dates within max days", "Review rows decided",
          "Target DWT inside the segment band", "Value falls with age (b below 0)", "Segment parameters validated"]

ICON = {"good": "✓", "warning": "!", "critical": "✕"}


def status_label(ship: ShipResult) -> str:
    text = "VALID" if ship.status == "VALID" else ("Usable with warning" if ship.status_kind == "warning" else "NOT VALID")
    return f'<span class="status {ship.status_kind}"><b>{ICON[ship.status_kind]}</b>{text}</span>'


def tile(label: str, value: str, note: str = "") -> str:
    return (f'<div class="tile"><div class="tile-label">{escape(label)}</div><div class="tile-value">{value}</div>'
            + (f'<div class="tile-note">{escape(note)}</div>' if note else "") + "</div>")


def overview(info: RunInfo, ships: List[ShipResult], db: Sequence[SaleRow]) -> str:
    valid = sum(s.status == "VALID" for s in ships)
    latest = max((r.report_date for r in db), default=None)
    sales = info.sales if info.sales is not None else (len(db) or None)
    tiles = (tile("Ships valued", str(len(ships)))
             + tile("VALID", f"{valid} of {len(ships)}", "passed every validity check")
             + tile("Sales in the database", f"{sales:,}" if sales else "–", "comparable sales available")
             + tile("Latest report", f"{latest:%d %b %Y}" if latest else "–", "newest broker report in the data"))
    vals = [v for s in ships for v in (s.low_musd, s.high_musd, s.value_musd) if v is not None]
    lo, hi = (min(vals) * 0.95, max(vals) * 1.05) if vals else (0, 1)
    rows = []
    for s in ships:
        rng = f"{charts.fmt_m(s.low_musd)} – {charts.fmt_m(s.high_musd)}" if s.low_musd is not None else "–"
        r2 = f"{s.r_squared:.2f}" if s.r_squared is not None else "–"
        rows.append(f'<tr class="link" data-go="ship/{escape(s.case_id)}" tabindex="0">'
                    f'<td><b>{escape(s.name)}</b><div class="sub">{escape(s.case_id)}</div></td>'
                    f'<td>{escape(s.segment)}</td><td class="num">{s.target_age}</td><td>{s.valuation_date:%d %b %Y}</td>'
                    f'<td class="num"><b>{charts.fmt_m(s.value_musd)}</b></td>'
                    f'<td>{charts.range_strip(s, lo, hi)}<div class="sub">{rng}</div></td>'
                    f'<td class="num">{s.n_comparables}</td><td class="num">{r2}</td><td>{status_label(s)}</td></tr>')
    return (f'<section id="p-overview" class="page">'
            f'<h2>Valuation results</h2><p class="lead">Each ship valued with the M1 comparable sales method. '
            f'Click a ship to see its age curve and checks.</p>'
            f'<div class="tiles">{tiles}</div>'
            f'<div class="card"><table class="tbl ships"><thead><tr><th>Ship</th><th>Segment</th><th class="num">Age</th>'
            f'<th>Valuation date</th><th class="num">Value</th><th>Value range</th><th class="num">Comparables</th>'
            f'<th class="num">R²</th><th>Status</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>')


def ship_panel(s: ShipResult) -> str:
    tiles = (tile("Value range", f'<span class="small">{charts.fmt_m(s.low_musd)} – {charts.fmt_m(s.high_musd)}</span>', "± one standard deviation of residuals")
             + tile("Comparables", str(s.n_comparables), "sales used for the curve")
             + tile("Value lost per year", f"{s.loss_rate * 100:.1f}%" if s.loss_rate is not None else "–", "from the age curve")
             + tile("Curve fit (R²)", f"{s.r_squared:.2f}" if s.r_squared is not None else "–", "1.00 = perfect fit"))
    known = ""
    if s.known_price_musd and s.value_musd:
        gap = (s.value_musd - s.known_price_musd) / s.known_price_musd * 100
        known = (f'<p class="note">Known price {charts.fmt_m(s.known_price_musd)}: the model is {abs(gap):.1f}% '
                 f'{"above" if gap > 0 else "below"} it.</p>')
    checks = []
    for c in CHECKS:
        failed = c in s.failed_checks
        kind = ("warning" if c == "Segment parameters validated" else "critical") if failed else "good"
        word = {"good": "Pass", "warning": "Warning", "critical": "Fail"}[kind]
        checks.append(f'<li><span class="status {kind}"><b>{ICON[kind]}</b>{word}</span>{escape(c)}</li>')
    comp_rows = "".join(f"<tr><td>{escape(c.vessel)}</td><td>{c.report_date:%d %b %Y}</td><td class='num'>{c.age}</td>"
                        f"<td class='num'>{c.price_musd:g}</td><td class='num'>{c.adjusted_price_musd:.2f}</td></tr>"
                        for c in sorted(s.comparables, key=lambda c: c.age))
    return (f'<div class="ship" data-ship="{escape(s.case_id)}">'
            f'<div class="hero"><div><div class="hero-label">{escape(s.name)} · {escape(s.segment)} · age {s.target_age} · '
            f'{s.valuation_date:%d %b %Y}</div><div class="hero-value">{charts.fmt_m(s.value_musd)}</div></div>'
            f'<div>{status_label(s)}</div></div>'
            + (f'<p class="note warn">{escape(s.message)}</p>' if s.message else "") + known +
            f'<div class="tiles">{tiles}</div>'
            f'<div class="grid2"><div class="card"><h3>Age curve</h3>'
            f'<div class="legend"><span><i class="k-dot"></i>Comparable sales</span><span><i class="k-line"></i>Fitted age curve</span>'
            f'<span><i class="k-target"></i>{escape(s.name)} with value range</span></div>{charts.age_curve(s)}'
            f'<details><summary>Table of the {len(s.comparables)} comparable sales</summary><table class="tbl"><thead><tr>'
            f'<th>Ship</th><th>Reported</th><th class="num">Age</th><th class="num">Price $m</th>'
            f'<th class="num">Brought to valuation date $m</th></tr></thead><tbody>{comp_rows}</tbody></table></details></div>'
            f'<div class="card"><h3>Validity checks</h3><ul class="checks">{"".join(checks)}</ul>'
            f'<p class="sub">The value is VALID only when every check passes.</p></div></div></div>')


def ship_page(ships: List[ShipResult]) -> str:
    opts = "".join(f'<option value="{escape(s.case_id)}">{escape(s.name)} ({escape(s.case_id)})</option>' for s in ships)
    return (f'<section id="p-ship" class="page"><div class="pick"><h2>Ship detail</h2>'
            f'<label>Ship <select id="ship-select">{opts}</select></label></div>'
            + "".join(ship_panel(s) for s in ships) + "</section>")


def database_page(info: RunInfo, db: Sequence[SaleRow]) -> str:
    if not db:
        body = '<p class="empty">Run with --data (the M1_Data/clean folder) to see the database.</p>'
    else:
        segs = Counter(r.segment for r in db)
        latest = max(r.report_date for r in db)
        body = (f'<div class="tiles">{tile("Sales", f"{len(db):,}")}'
                + tile("Broker values", f"{info.broker_values:,}" if info.broker_values else "–", "indicative prices for indexing")
                + tile("Segments", str(len(segs)))
                + tile("Latest report", f"{latest:%d %b %Y}") + "</div>"
                f'<div class="grid2"><div class="card"><h3>Sales in the database, by report date</h3>{charts.growth(db)}'
                f'<p class="sub">Each week the automation reads new broker reports, a person approves the rows, and they '
                f'are added here.</p></div>'
                f'<div class="card"><h3>Sales by segment</h3>{charts.segment_bars(db)}</div></div>')
    return f'<section id="p-database" class="page"><h2>Database</h2><p class="lead">The sales the valuations draw on.</p>{body}</section>'


def roadmap_page() -> str:
    return (f'<section id="p-roadmap" class="page"><h2>Model roadmap</h2>'
            f'<p class="lead">One case runs through every model: <b>{escape(roadmap.QUESTION)}</b> M1 is the base: '
            f'every later model needs a market value and an age curve.</p>'
            f'<div class="card">{roadmap.diagram()}</div>'
            f'<div class="card"><h3>What M1 gives each model</h3>{roadmap.gives_table()}</div></section>')


CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;
--axis:#c3c2b7;--ring:rgba(11,11,11,.10);--s1:#2a78d6;--s2:#eb6834;--good:#0ca30c;--warning:#fab219;--critical:#d03b3b;
--accent:#2a78d6;--chip:#eef3fb}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;
--muted:#898781;--grid:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10);--s1:#3987e5;--s2:#d95926;--accent:#3987e5;--chip:#1f2a3a}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:var(--surface);border-bottom:1px solid var(--ring);position:sticky;top:0;z-index:5}
.bar{max-width:1180px;margin:0 auto;padding:12px 16px;display:flex;flex-wrap:wrap;gap:8px 24px;align-items:center;justify-content:space-between}
.brand b{font-size:17px}.brand span{color:var(--ink2);font-size:13px;margin-left:8px}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{color:var(--ink2);text-decoration:none;padding:7px 12px;border-radius:8px;font-size:14px}
nav a:hover{background:var(--chip)} nav a.on{background:var(--accent);color:#fff}
main{max-width:1180px;margin:0 auto;padding:20px 16px 40px}
.page{display:none}.page.on{display:block}
h2{font-size:22px;margin:4px 0 4px}h3{font-size:15px;margin:0 0 10px}
.lead{color:var(--ink2);margin:0 0 16px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:0 0 16px}
.tile,.card{background:var(--surface);border:1px solid var(--ring);border-radius:12px;padding:14px 16px}
.card{margin:0 0 16px;overflow-x:auto}
.tile-label{font-size:13px;color:var(--ink2)}.tile-value{font-size:26px;font-weight:650;margin:2px 0}
.tile-note{font-size:12px;color:var(--muted)}.tile-value .small{font-size:20px;white-space:nowrap}
.grid2{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:16px}
@media (max-width:900px){.grid2{grid-template-columns:1fr}}
.tbl{border-collapse:collapse;width:100%;font-size:14px}
.tbl th{font-size:12.5px;color:var(--ink2);font-weight:500;text-align:left;border-bottom:1px solid var(--axis);padding:8px}
.tbl td{border-bottom:1px solid var(--grid);padding:8px;vertical-align:middle}
.num{text-align:right;font-variant-numeric:tabular-nums}
.sub{font-size:12px;color:var(--muted)}
tr.link{cursor:pointer} tr.link:hover,tr.link:focus{background:var(--chip);outline:none}
.status{display:inline-flex;gap:6px;align-items:center;font-size:13px;font-weight:600;white-space:nowrap}
.status b{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:50%;color:#fff;font-size:11px}
.status.good b{background:var(--good)}.status.warning b{background:var(--warning);color:#0b0b0b}.status.critical b{background:var(--critical)}
.hero{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin:0 0 12px}
.hero-label{color:var(--ink2);font-size:14px}.hero-value{font-size:44px;font-weight:700;line-height:1.1}
.pick{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin:0 0 10px}
select{font:inherit;padding:6px 10px;border-radius:8px;border:1px solid var(--axis);background:var(--surface);color:var(--ink)}
.ship{display:none}.ship.on{display:block}
.note{font-size:14px;color:var(--ink2);margin:0 0 12px}.note.warn{border-left:3px solid var(--critical);padding-left:10px}
.checks{list-style:none;margin:0;padding:0}.checks li{display:flex;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--grid);font-size:14px}
.checks .status{min-width:92px}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--ink2);margin:0 0 6px}
.legend i{display:inline-block;vertical-align:middle;margin-right:6px}
.k-dot{width:10px;height:10px;border-radius:50%;background:var(--s1)}
.k-line{width:18px;height:2px;background:var(--s2)}
.k-target{width:10px;height:10px;background:var(--ink);transform:rotate(45deg)}
details{margin-top:8px;font-size:14px}summary{cursor:pointer;color:var(--ink2)}
svg.chart{width:100%;height:auto;display:block;min-width:520px}svg.chart.bars{min-width:0}
.grid{stroke:var(--grid);stroke-width:1}.axis{stroke:var(--axis);stroke-width:1}
.tick{fill:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}.axis-title{fill:var(--ink2);font-size:12.5px}
.direct{fill:var(--ink);font-size:13px;font-weight:600;paint-order:stroke;stroke:var(--surface);stroke-width:4px}
.dot{fill:var(--s1);stroke:var(--surface);stroke-width:2;cursor:pointer}.dot:hover,.dot:focus{r:7;outline:none}
.curve{fill:none;stroke:var(--s2);stroke-width:2}
.target{fill:var(--ink);stroke:var(--surface);stroke-width:2;cursor:pointer}.whisker{stroke:var(--ink);stroke-width:2}
.line{fill:none;stroke:var(--s1);stroke-width:2}.line-end{fill:var(--s1);stroke:var(--surface);stroke-width:2}
.hit{fill:transparent;cursor:pointer}.hit:hover,.hit:focus{fill:var(--s1);fill-opacity:.25;outline:none}
.bar{fill:var(--s1);cursor:pointer}.bar:hover{fill-opacity:.8}.cat{fill:var(--ink2);font-size:13px}.val{fill:var(--ink2);font-size:12.5px;font-variant-numeric:tabular-nums}
svg.strip{width:170px;height:22px;display:block}.strip-range{stroke:var(--axis);stroke-width:4;stroke-linecap:round}
.strip-dot{fill:var(--s1);stroke:var(--surface);stroke-width:2}
.roadmap{min-width:760px}.rm-node rect{fill:var(--surface);stroke:var(--axis);stroke-width:1.5}
.rm-node.built rect{fill:var(--chip);stroke:var(--accent);stroke-width:2.5}.rm-node.unused rect{fill:var(--surface);stroke:var(--muted);stroke-width:2;stroke-dasharray:7 5}.rm-node.started rect{stroke:var(--accent);stroke-dasharray:6 4;stroke-width:2}
.rm-title{fill:var(--ink);font-size:14px;font-weight:650}.rm-line{fill:var(--ink2);font-size:12px}
.rm-status{fill:var(--muted);font-size:11.5px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.rm-node.built .rm-status,.rm-node.started .rm-status{fill:var(--accent)}
.rm-edge{fill:none;stroke:var(--ink2);stroke-width:1.6}.au-box rect{fill:var(--surface);stroke:var(--axis);stroke-width:1.5}.au-box.step rect{fill:var(--chip);stroke:var(--accent);stroke-width:2.5}.au-box.parked rect{stroke:var(--muted);stroke-dasharray:7 5;stroke-width:2}.au-box.optional rect{stroke:var(--muted)}.au-box.parked text,.au-box.optional text{fill:var(--muted)}.rm-edge.dashed{stroke-dasharray:6 5;stroke:var(--muted)}.rm-head{fill:var(--ink2)}.rm-label{fill:var(--ink2);font-size:12px;font-style:italic;paint-order:stroke;stroke:var(--surface);stroke-width:4px}
.empty{color:var(--muted)}
footer{max-width:1180px;margin:0 auto;padding:0 16px 30px;font-size:12px;color:var(--muted)}
#tip{position:fixed;z-index:20;max-width:320px;background:var(--ink);color:var(--surface);font-size:13px;line-height:1.4;padding:8px 10px;border-radius:8px;pointer-events:none;display:none;box-shadow:0 4px 14px rgba(0,0,0,.25)}
@media print{header{position:static}.page{display:block!important;break-after:page}.ship{display:block!important;break-after:page}}
"""

JS = """
(function(){
var pages=['overview','ship','database','automation','m3','roadmap'];
function show(hash){
  var h=(hash||'#overview').slice(1), parts=h.split('/'), p=pages.indexOf(parts[0])<0?'overview':parts[0];
  pages.forEach(function(x){document.getElementById('p-'+x).classList.toggle('on',x===p);
    document.querySelector('nav a[href="#'+x+'"]').classList.toggle('on',x===p);});
  if(p==='ship'){var sel=document.getElementById('ship-select');var id=parts[1]||sel.value;sel.value=id;
    document.querySelectorAll('.ship').forEach(function(e){e.classList.toggle('on',e.getAttribute('data-ship')===id);});}
  window.scrollTo(0,0);}
window.addEventListener('hashchange',function(){show(location.hash);});
document.getElementById('ship-select').addEventListener('change',function(){location.hash='ship/'+this.value;});
document.querySelectorAll('tr.link').forEach(function(r){var go=function(){location.hash=r.getAttribute('data-go');};
  r.addEventListener('click',go);r.addEventListener('keydown',function(e){if(e.key==='Enter')go();});});
var tip=document.getElementById('tip');
function place(x,y){var w=tip.offsetWidth,h=tip.offsetHeight;var l=Math.min(Math.max(8,x+14),innerWidth-w-8),t=y+16;
  if(t+h>innerHeight-8)t=Math.max(8,y-h-12);tip.style.left=l+'px';tip.style.top=t+'px';}
document.querySelectorAll('[data-tip]').forEach(function(el){
  el.addEventListener('mousemove',function(e){tip.textContent=el.getAttribute('data-tip');tip.style.display='block';place(e.clientX,e.clientY);});
  el.addEventListener('mouseleave',function(){tip.style.display='none';});
  el.addEventListener('focus',function(){var r=el.getBoundingClientRect();tip.textContent=el.getAttribute('data-tip');tip.style.display='block';place(r.left,r.bottom);});
  el.addEventListener('blur',function(){tip.style.display='none';});});
show(location.hash);
})();
"""


def build(info: RunInfo, ships: List[ShipResult], db: Sequence[SaleRow], made: dt.datetime, m3_results=None) -> str:
    run = f"Calculate run {escape(info.run_time or info.folder)}" + (f" ({escape(info.version)})" if info.version else "")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>M1 Valuation Dashboard</title><style>{CSS}</style></head><body>
<header><div class="bar"><div class="brand"><b>M1 Ship Valuation</b><span>{run}</span></div>
<nav><a href="#overview">Overview</a><a href="#ship">Ship detail</a><a href="#database">Database</a><a href="#automation">Automation</a><a href="#m3">Acquisition &amp; finance</a><a href="#roadmap">Model roadmap</a></nav></div></header>
<main>{overview(info, ships, db)}{ship_page(ships)}{database_page(info, db)}{automation.page(info, db)}{m3.page(m3_results)}{roadmap_page()}</main>
<footer>Made {made:%d %b %Y %H:%M} by m1_dash {__version__} from {escape(info.folder)}. Values are model outputs of a personal portfolio
project (M1 comparable sales; M3 acquisition and finance from its results file); not investment advice. Hover over any mark for its numbers.</footer>
<div id="tip" role="tooltip"></div><script>{JS}</script></body></html>"""
