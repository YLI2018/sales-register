"""Write results.xlsx: a Results sheet (one row per ship) and one Age Curve sheet per ship, laid out like the
Age Curve sheet of the Excel template, with a chart. House style: black and grey only.

Each Age Curve sheet shows Python's numbers and, beside them, an "Excel check": live Excel formulas (SLOPE, INTERCEPT,
RSQ, STDEV) on the same comparables table. Excel recalculates them on opening, so every sheet checks itself.
"""
from pathlib import Path
from typing import List

import openpyxl
from openpyxl.chart import Reference, ScatterChart, Series
from openpyxl.chart.marker import Marker
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.trendline import Trendline
from openpyxl.drawing.line import LineProperties
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .engine import Result

DARK, LIGHT = "404040", "F2F2F2"
HEAD_FILL, HEAD_FONT = PatternFill("solid", fgColor=DARK), Font(bold=True, color="FFFFFF")
GREY_FILL = PatternFill("solid", fgColor=LIGHT)
TITLE, NOTE, BOLD = Font(bold=True, size=14), Font(italic=True, size=9, color="595959"), Font(bold=True)
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

FIRST_ROW = 26   # first row of the comparables table on an Age Curve sheet


def _head(ws, row, labels, col=1):
    for i, text in enumerate(labels):
        c = ws.cell(row, col + i, text)
        c.fill, c.font, c.border = HEAD_FILL, HEAD_FONT, BOX
        c.alignment = Alignment(wrap_text=True, vertical="center")


def _sheet_name(r: Result, used: set) -> str:
    base = f"Curve {r.ship.case_id}"[:31]
    name, k = base, 2
    while name in used:
        name, k = f"{base[:28]} {k}", k + 1
    used.add(name)
    return name


def _results_sheet(wb, results: List[Result], names: List[str]) -> None:
    ws = wb.active
    ws.title = "Results"
    ws["A1"] = "M1 valuation results"; ws["A1"].font = TITLE
    ws["A2"] = "One row per ship. Each ship's comparables, curve and chart are on its own 'Curve' sheet."; ws["A2"].font = NOTE
    cols = ["Case", "Ship", "Segment", "Valuation date", "Age", "Value ($m)", "Range low ($m)", "Range high ($m)",
            "Loss per year", "a ($m)", "b", "R²", "Comparables", "Known price ($m)", "Known vs fitted", "Status", "Sheet"]
    _head(ws, 4, cols)
    for i, (r, sheet) in enumerate(zip(results, names), start=5):
        c = r.curve
        row = [r.ship.case_id, r.ship.target_name, r.ship.segment, r.ship.valuation_date, r.target_age, r.value_musd,
               r.range_low_musd, r.range_high_musd, c.loss_rate if c else None, c.a_musd if c else None, c.b if c else None,
               c.r_squared if c else None, r.n_comparables, r.ship.known_price_musd, r.known_gap_pct, r.status, sheet]
        for j, v in enumerate(row, start=1):
            cell = ws.cell(i, j, v)
            cell.border = BOX
        for j, fmt in ((4, "d mmm yyyy"), (6, "0.00"), (7, "0.00"), (8, "0.00"), (9, "0.0%"), (10, "0.000"), (11, "0.00000"),
                       (12, "0.000"), (14, "0.00"), (15, "0.0%")):
            ws.cell(i, j).number_format = fmt
        ws.cell(i, 17).hyperlink = f"#'{sheet}'!A1"
    for j, w in enumerate([10, 24, 10, 13, 6, 11, 11, 11, 10, 9, 10, 8, 12, 12, 12, 36, 16], start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = w
    ws.freeze_panes = "A5"


def _curve_sheet(wb, r: Result, name: str) -> None:
    ws = wb.create_sheet(name)
    s, c, comps = r.ship, r.curve, r.comparables
    n = len(comps)
    last = FIRST_ROW + max(n, 1) - 1
    rng = lambda col: f"${col}${FIRST_ROW}:${col}${last}"
    ws["A1"] = f"Age curve: {s.target_name} ({s.case_id})"; ws["A1"].font = TITLE
    ws["A2"] = (f"{s.segment}, {s.dwt:,.0f} DWT, built {s.year_built}; valuation date {s.valuation_date:%d %b %Y}. "
                "Curve: adjusted price = a × e^(b × age), fitted on LN(adjusted price) against age.")
    ws["A2"].font = NOTE
    _head(ws, 4, ["Result", "Python", "Excel check", "Excel formula used for the check"])
    a_chk, b_chk = "$C$7", "$C$8"
    rows = [
        ("Status", r.status, None, None, None),
        ("Target age (years)", r.target_age, None, None, "0"),
        ("a ($m at age 0)", c.a_musd if c else None, f"=EXP(INTERCEPT({rng('I')},{rng('C')}))", "EXP(INTERCEPT(LN price, age))", "0.000"),
        ("b (per year)", c.b if c else None, f"=SLOPE({rng('I')},{rng('C')})", "SLOPE(LN price, age)", "0.00000"),
        ("Value lost per year", c.loss_rate if c else None, f"=1-EXP({b_chk})", "1 − e^b", "0.0%"),
        ("R² (on LN price)", c.r_squared if c else None, f"=RSQ({rng('I')},{rng('C')})", "RSQ(LN price, age)", "0.000"),
        ("Comparables", r.n_comparables, f"=COUNT({rng('H')})", "COUNT(adjusted price)", "0"),
        ("Market value ($m)", r.value_musd, f"={a_chk}*EXP({b_chk}*$B$6)", "a × e^(b × target age)", "0.00"),
        ("SD of residuals ($m)", r.sd_residuals_musd, f"=STDEV({rng('K')})", "STDEV(residual)", "0.00"),
        ("Range low ($m)", r.range_low_musd, None, None, "0.00"),
        ("Range high ($m)", r.range_high_musd, None, None, "0.00"),
        ("Near-age average ($m)", r.near_age_average_musd, None, None, "0.00"),
        ("Near-age count", r.near_age_count, None, None, "0"),
        ("Known price ($m)", s.known_price_musd, None, None, "0.00"),
        ("Known vs fitted", r.known_gap_pct, None, None, "0.0%"),
        ("Valuation-date benchmark", r.valuation_benchmark_date, None, None, "d mmm yyyy"),
    ]
    for i, (label, py, chk, how, fmt) in enumerate(rows, start=5):
        ws.cell(i, 1, label).border = BOX
        p = ws.cell(i, 2, py); p.border = BOX; p.fill = GREY_FILL
        k = ws.cell(i, 3, chk if (chk and n >= 2) else None); k.border = BOX; k.fill = GREY_FILL
        ws.cell(i, 4, how).font = NOTE
        if fmt:
            p.number_format = k.number_format = fmt
    ws["B5"].font = BOLD
    failed = [f"{v}: {k}" for k, v in r.checks.items() if v != "Pass"]
    ws.cell(22, 1, "Checks not passed: " + ("; ".join(failed) if failed else "none") + (f". {r.message}" if r.message else ""))
    ws.cell(22, 1).font = NOTE

    heads = ["Vessel", "Report date", "Age at sale", "Price ($m)", "Benchmark date", "Benchmark age", "Index factor",
             "Adjusted price ($m)", "LN(adjusted price)", "Fitted price ($m)", "Residual ($m)", "Decision source"]
    ws.cell(24, 1, "Comparables (one row per sale used in the fit)").font = BOLD
    _head(ws, 25, heads)
    for i, x in enumerate(comps, start=FIRST_ROW):
        vals = [x.sale.vessel, x.sale.report_date, x.age_at_sale, x.sale.price_musd, x.benchmark_date, x.benchmark_age_label,
                x.index_factor, x.adjusted_price_musd, f"=LN(H{i})", x.fitted_price_musd, x.residual_musd, x.decision_source]
        for j, v in enumerate(vals, start=1):
            cell = ws.cell(i, j, v); cell.border = BOX
            if j in (9, 10, 11):
                cell.fill = GREY_FILL
        for j, fmt in ((2, "d mmm yyyy"), (4, "0.00"), (5, "d mmm yyyy"), (7, "0.0000"), (8, "0.00"), (9, "0.0000"),
                       (10, "0.00"), (11, "+0.00;-0.00")):
            ws.cell(i, j).number_format = fmt
    # target point for the chart
    ws["Q24"] = "Target (chart)"
    ws["Q25"], ws["R25"] = "Age", "Value ($m)"
    ws["Q26"], ws["R26"] = r.target_age, r.value_musd
    for ref in ("Q24", "Q25", "R25", "Q26", "R26"):
        ws[ref].font = NOTE
    for j, w in enumerate([24, 13, 12, 12, 14, 12, 11, 13, 13, 12, 11, 16, 3, 3, 3, 3, 10, 10], start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = w
    if n >= 2:
        _chart(ws, r, last)


def _chart(ws, r: Result, last: int) -> None:
    ch = ScatterChart()
    ch.title = f"{r.ship.segment} comparables: adjusted price against age"
    ch.style = 1
    ch.x_axis.title, ch.y_axis.title = "Age at sale (years)", "Price at valuation date ($m)"
    ch.x_axis.majorGridlines = None
    ch.x_axis.delete = ch.y_axis.delete = False
    ch.legend.position = "b"
    xs = Reference(ws, min_col=3, min_row=FIRST_ROW, max_row=last)
    ys = Reference(ws, min_col=8, min_row=FIRST_ROW, max_row=last)
    comp = Series(ys, xs, title="Comparables (adjusted)")
    comp.marker = Marker(symbol="circle", size=6)
    comp.marker.graphicalProperties = GraphicalProperties(solidFill="7F7F7F", ln=LineProperties(solidFill="7F7F7F"))
    comp.graphicalProperties = GraphicalProperties(ln=LineProperties(noFill=True))
    comp.trendline = Trendline(trendlineType="exp", dispRSqr=True, dispEq=True,
                               spPr=GraphicalProperties(ln=LineProperties(solidFill="000000", prstDash="dash", w=19050)))
    tgt = Series(Reference(ws, min_col=18, min_row=26, max_row=26), Reference(ws, min_col=17, min_row=26, max_row=26),
                 title=f"{r.ship.target_name} (value)")
    tgt.marker = Marker(symbol="diamond", size=10)
    tgt.marker.graphicalProperties = GraphicalProperties(solidFill="000000", ln=LineProperties(solidFill="000000"))
    tgt.graphicalProperties = GraphicalProperties(ln=LineProperties(noFill=True))
    ch.series.extend([comp, tgt])
    ch.width, ch.height = 18, 10
    ws.add_chart(ch, "F4")


def write_workbook(results: List[Result], path: Path) -> Path:
    """Create results.xlsx at path: Results sheet plus one Age Curve sheet per ship. Excel recalculates on opening."""
    wb = openpyxl.Workbook()
    used, names = {"Results"}, []
    for r in results:
        names.append(_sheet_name(r, used))
    _results_sheet(wb, results, names)
    for r, name in zip(results, names):
        _curve_sheet(wb, r, name)
    wb.calculation.fullCalcOnLoad = True
    wb.save(path)
    return path
