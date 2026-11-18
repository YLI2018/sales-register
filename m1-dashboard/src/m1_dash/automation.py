"""Automation page: how the M1 projects turn broker reports into the valuations on this dashboard."""
from html import escape

# (step, project, what it does, in -> out, version, status)
STEPS = [
    ("1", "m1-report-download", "Saves weekly broker reports into the archive",
     "broker websites → report archive (PDF)", "v0.1.1",
     "Parked: the websites block automated download, so reports are saved by hand"),
    ("2", "m1-extract", "Reads new reports into a check file; you approve rows; approved rows go into the database",
     "PDF reports → check file → sales database (sales.csv)", "v0.1.4", "In use"),
    ("3", "m1-fill-template", "Puts the database and one ship into the Excel template, to show the workings",
     "database + one ship → Excel workbook", "v0.1.1", "Optional (showcase)"),
    ("4", "m1-calculate", "Values every ship on the list with the template's settings, using only sales reported by "
     "the valuation date", "database + ship list → results (value, range, checks)", "v0.3.0", "In use"),
    ("5", "m1-dashboard (M5)", "Turns the newest results, the database and the M3 results file into this dashboard",
     "results + database + M3 results → this HTML file", "v0.2.2", "In use"),
]

# boxes: (key, label, sub, x, y, kind)
BOXES = [
    ("rep", "Broker reports", "PDF archive", 10, 70, "data"),
    ("ext", "2 · Extract", "check file, you approve", 190, 70, "step"),
    ("db", "Sales database", "sales.csv", 370, 70, "data"),
    ("calc", "4 · Calculate", "no sales after the date", 550, 70, "step"),
    ("res", "Results", "value, range, checks", 730, 70, "data"),
    ("dash", "5 · Dashboard (M5)", "this page", 910, 70, "step"),
    ("dl", "1 · Download", "parked: saved by hand", 10, 190, "parked"),
    ("tpl", "3 · Fill template", "optional Excel workings", 370, 190, "optional"),
    ("m3", "M3 results file", "acquisition and finance", 730, 190, "data"),
]
ARROWS = [("rep", "ext"), ("ext", "db"), ("db", "calc"), ("calc", "res"), ("res", "dash"), ("dl", "rep"),
          ("db", "tpl"), ("m3", "dash")]
W, H = 160, 64


def _box(key, label, sub, x, y, kind):
    return (f'<g class="au-box {kind}"><rect x="{x}" y="{y}" width="{W}" height="{H}" rx="9"/>'
            f'<text class="rm-title" x="{x + 12}" y="{y + 26}">{escape(label)}</text>'
            f'<text class="rm-line" x="{x + 12}" y="{y + 46}">{escape(sub)}</text></g>')


def _arrow(a, b):
    pa = next(x for x in BOXES if x[0] == a)
    pb = next(x for x in BOXES if x[0] == b)
    ax, ay, bx, by = pa[3], pa[4], pb[3], pb[4]
    if ay == by:
        d = f"M{ax + W},{ay + H / 2} L{bx - 2},{by + H / 2}"
    elif ax == bx:
        d = f"M{ax + W / 2},{ay + (0 if by < ay else H)} L{bx + W / 2},{by + (H + 2 if by < ay else -2)}"
    else:
        d = f"M{ax + W},{ay + H / 2} H{(ax + W + bx) / 2} V{by + H / 2} H{bx - 2}"
    dashed = " dashed" if a == "dl" else ""
    return f'<path class="rm-edge{dashed}" d="{d}" marker-end="url(#au-ah)"/>'


def diagram() -> str:
    out = ['<svg class="chart roadmap" viewBox="0 0 1080 270" role="img" aria-label="How the M1 automation runs">',
           '<defs><marker id="au-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           'orient="auto"><path d="M0,0 L10,5 L0,10 z" class="rm-head"/></marker></defs>']
    out += [_arrow(a, b) for a, b in ARROWS]
    out += [_box(*b) for b in BOXES]
    out.append("</svg>")
    out.append('<p class="sub">Blue: a project that runs. Plain: data. Grey dashed: parked. Grey: optional.</p>')
    return "".join(out)


def page(info, db) -> str:
    rows = "".join(f'<tr><td class="num">{s}</td><td>{escape(p)}</td><td>{escape(w)}</td><td>{escape(io)}</td>'
                   f'<td>{escape(v)}</td><td>{escape(st)}</td></tr>' for s, p, w, io, v, st in STEPS)
    latest = max((r.report_date for r in db), default=None)
    facts = [("Latest Calculate run", f"{info.run_time or info.folder}" + (f" ({info.version})" if info.version else "")),
             ("Sales in the database", f"{len(db):,}" if db else (f"{info.sales:,}" if info.sales else "–")),
             ("Latest broker report in the database", latest.strftime("%d %b %Y") if latest else "–"),
             ("No-hindsight rule", "a valuation uses only sales reported on or before its valuation date; later "
                                   "sales stay in the database but are left out of that valuation")]
    ftab = "".join(f"<tr><td>{escape(a)}</td><td>{escape(b)}</td></tr>" for a, b in facts)
    return (f'<section id="p-automation" class="page"><h2>Automation</h2>'
            f'<p class="lead">How weekly broker reports become the valuations on this dashboard: five small projects, '
            f'each with its own code, tests and documents.</p>'
            f'<div class="card">{diagram()}</div>'
            f'<div class="card"><h3>The five projects</h3><table class="tbl"><thead><tr><th class="num">Step</th>'
            f'<th>Project</th><th>Does</th><th>In → out</th><th>Version</th><th>Status</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            f'<div class="card"><h3>This run</h3><table class="tbl"><tbody>{ftab}</tbody></table></div></section>')
