"""Write the results: results.csv (one row per ship), comparables.csv (one row per ship and comparable), results.xlsx
(Results sheet and one Age Curve sheet with chart per ship) and a log.

Column names follow docs/data_dictionary.md. Numbers are written with full precision and a dot; a file that already
exists is never overwritten (each run writes into a new folder named with the date and time).
"""
import csv
import datetime as dt
from pathlib import Path
from typing import List

from . import __version__
from .engine import Result
from .workbook import write_workbook

RESULT_COLUMNS = ["case_id", "target_name", "segment", "valuation_date", "target_age", "value_musd", "range_low_musd",
                  "range_high_musd", "loss_rate", "a_musd", "b", "r_squared", "n_comparables", "sd_residuals_musd",
                  "near_age_average_musd", "near_age_count", "known_price_musd", "known_gap_pct",
                  "valuation_benchmark_date", "information_cutoff", "sales_after_cutoff",
                  "broker_values_after_cutoff", "parameters_status", "status", "failed_checks", "message"]
COMPARABLE_COLUMNS = ["case_id", "sale_id", "vessel", "report_date", "age_at_sale", "price_musd", "benchmark_date",
                      "days_to_benchmark", "benchmark_age", "index_factor", "adjusted_price_musd", "log_price", "age_gap",
                      "log_price_gap", "fitted_price_musd", "residual_musd", "decision_source"]


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, float):
        return repr(round(v, 10))
    return str(v)


def write_results(results: List[Result], out_dir: Path, inputs_note: List[str]) -> Path:
    """Create out_dir/M1_calc_<date_time>/ with results.csv, comparables.csv, results.xlsx and run.log. Returns that folder."""
    run = out_dir / f"M1_calc_{dt.datetime.now():%Y-%m-%d_%H%M%S}"
    run.mkdir(parents=True, exist_ok=False)
    with (run / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(RESULT_COLUMNS)
        for r in results:
            c = r.curve
            w.writerow([_fmt(x) for x in (
                r.ship.case_id, r.ship.target_name, r.ship.segment, r.ship.valuation_date, r.target_age, r.value_musd,
                r.range_low_musd, r.range_high_musd, c.loss_rate if c else None, c.a_musd if c else None, c.b if c else None,
                c.r_squared if c else None, r.n_comparables, r.sd_residuals_musd, r.near_age_average_musd, r.near_age_count,
                r.ship.known_price_musd, r.known_gap_pct, r.valuation_benchmark_date, r.information_cutoff,
                r.sales_after_cutoff, r.broker_values_after_cutoff, r.parameters_status, r.status,
                "; ".join(k for k, v in r.checks.items() if v != "Pass"), r.message)])
    with (run / "comparables.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COMPARABLE_COLUMNS)
        for r in results:
            for c in r.comparables:
                w.writerow([_fmt(x) for x in (
                    r.ship.case_id, c.sale.id, c.sale.vessel, c.sale.report_date, c.age_at_sale, c.sale.price_musd,
                    c.benchmark_date, c.days_to_benchmark, c.benchmark_age_label, c.index_factor, c.adjusted_price_musd,
                    c.log_price, c.age_gap, c.log_price_gap, c.fitted_price_musd, c.residual_musd, c.decision_source)])
    lines = [f"m1_calc {__version__}", f"run: {dt.datetime.now():%Y-%m-%d %H:%M:%S}"] + inputs_note
    for r in results:
        value = f"${r.value_musd:.2f}m (range {r.range_low_musd:.2f}–{r.range_high_musd:.2f})" if r.value_musd else "no value"
        lines.append(f"{r.ship.case_id} {r.ship.target_name}: {value}; {r.n_comparables} comparables; {r.status}"
                     + (f"; {r.message}" if r.message else ""))
        lines.append(f"    information up to {r.information_cutoff}: left out {r.sales_after_cutoff} later sales and "
                     f"{r.broker_values_after_cutoff} later broker values")
        for k, v in r.checks.items():
            if v != "Pass":
                lines.append(f"    {v}: {k}")
    write_workbook(results, run / "results.xlsx")
    (run / "run.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return run
