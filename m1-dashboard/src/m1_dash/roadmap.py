"""The model roadmap: how M1 links to the models built next. Edit MODELS and LINKS as the portfolio grows."""
from html import escape

# key: (title, one line, status, x, y)
MODELS = {
    "M1": ("M1 · Sales register + age curve", "Market value from comparable sales", "Built and automated", 20, 150),
    "M1+": ("M1+ · Hedonic regression", "Price from age, size, yard, specs", "Built", 20, 310),
    "VE": ("VE · Voyage estimator", "Earnings per day (TCE), EU ETS cost", "Built · not used in this case", 380, 10),
    "M2": ("M2 · Valuation", "Comparables + cash flow, scenarios", "Built · v5", 380, 150),
    "M4": ("M4 · Build vs buy", "Second-hand ship vs a newbuilding", "Planned", 380, 310),
    "M3": ("M3 · Acquisition and finance", "Deal IRR, loan-to-value covenants", "Built · v3", 740, 150),
    "M5": ("M5 · Dashboard", "Presents every model's results", "Built · this dashboard", 740, 310),
}
# (from, to, label, label dx, label dy[, "dashed" = built but not used in this case])
LINKS = [
    ("M1", "M2", "value + age curve", 0, -8),
    ("VE", "M2", "earnings per day (not linked)", 8, 4, "dashed"),
    ("M2", "M3", "price + collateral", 0, -8),
    ("M1+", "M1", "improves the curve", 8, 4),
    ("M1", "M4", "second-hand value by age", 8, 0),
    ("M3", "M5", "results", 8, 4),
    ("M4", "M5", "results", 0, -8),
]
GIVES = [
    ("M2 Valuation", "Today's market value from comparable sales (one leg of the valuation), and the age curve to value the ship at the end of the cash-flow period"),
    ("M3 Acquisition and finance", "The value that sets the price to pay and the collateral value; the age curve projects that value year by year to test loan-to-value covenants"),
    ("M4 Build vs buy", "Second-hand values at each age, to compare with the price of a newbuilding"),
    ("M1+ Hedonic regression", "The same sales database; M1+ adds size, yard and specification to age and checks whether the curve improves"),
    ("M5 Dashboard", "The valuations and the sales database (Overview, Ship detail and Database pages); M3 adds the Acquisition and finance page"),
]
QUESTION = "Should we buy this MR tanker?"

NW, NH = 230, 82


def _node(key: str) -> str:
    title, line, status, x, y = MODELS[key]
    cls = ("unused" if "not used" in status else "built" if status.startswith("Built")
           else "started" if status.startswith("Started") else "planned")
    return (f'<g class="rm-node {cls}"><rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="10"/>'
            f'<text class="rm-title" x="{x + 14}" y="{y + 26}">{escape(title)}</text>'
            f'<text class="rm-line" x="{x + 14}" y="{y + 46}">{escape(line)}</text>'
            f'<text class="rm-status" x="{x + 14}" y="{y + 68}">{escape(status)}</text></g>')


def _edge(a: str, b: str, label: str, lx: float, ly: float, style: str = ""):
    _, _, _, ax, ay = MODELS[a]
    _, _, _, bx, by = MODELS[b]
    acx, acy, bcx, bcy = ax + NW / 2, ay + NH / 2, bx + NW / 2, by + NH / 2
    if ay == by:                      # same row: right edge to left edge
        x1, y1, x2, y2 = ax + NW, acy, bx, bcy
    elif ax == bx:                    # same column: bottom/top edges
        x1, x2 = acx, bcx
        y1, y2 = (ay + NH, by) if by > ay else (ay, by + NH)
    else:                             # elbow: leave sideways, enter from the side
        x1, y1, x2, y2 = ax + NW, acy, bx, bcy
    if x1 != x2 and y1 != y2:
        mx = (x1 + x2) / 2
        d = f"M{x1},{y1} H{mx} V{y2} H{x2 - 2}"
        tx, ty = mx + lx, (y1 + y2) / 2 + ly
    else:
        d = f"M{x1},{y1} L{x2 - (2 if y1 == y2 else 0)},{y2 - (2 if x1 == x2 and y2 > y1 else -2 if x1 == x2 else 0)}"
        tx, ty = (x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly
    anchor = "start" if x1 == x2 or (x1 != x2 and y1 != y2) else "middle"
    return (f'<path class="rm-edge{" dashed" if style == "dashed" else ""}" d="{d}" marker-end="url(#rm-ah)"/>',
            f'<text class="rm-label" x="{tx}" y="{ty}" text-anchor="{anchor}">{escape(label)}</text>')


def diagram() -> str:
    W, H = 990, 410
    out = [f'<svg class="chart roadmap" viewBox="0 0 {W} {H}" role="img" aria-label="How M1 links to the next models">',
           '<defs><marker id="rm-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           '<path d="M0,0 L10,5 L0,10 z" class="rm-head"/></marker></defs>']
    edges = [_edge(*e) for e in LINKS]
    out += [e[0] for e in edges]          # lines first, then boxes, then labels on top
    out += [_node(k) for k in MODELS]
    out += [e[1] for e in edges]
    out.append("</svg>")
    out.append('<p class="sub">Blue box: built and used in this case. Grey dashed box and line: built, but not used '
               'in this case (the voyage estimator\'s values are placeholders in M3). Grey box: planned.</p>')
    return "".join(out)


def gives_table() -> str:
    rows = "".join(f"<tr><td>{escape(m)}</td><td>{escape(g)}</td></tr>" for m, g in GIVES)
    return f'<table class="tbl"><thead><tr><th>Model</th><th>What M1 gives it</th></tr></thead><tbody>{rows}</tbody></table>'
