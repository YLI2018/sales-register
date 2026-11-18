"""Command line.

    python3 -m m1_dash --results M1_DATA/results [--run FOLDER] [--data M1_DATA/clean] [--m3 M3_RESULTS] --out M1_DATA/dashboard

--results  the folder holding Calculate's runs (M1_calc_<date_time>); the newest run is used unless --run is given
--run      one Calculate run folder to show instead of the newest
--data     the database folder (clean/), for the Database page (optional)
--m3       the M3 results folder (M3_results_*.json; the newest is used) or one file, for the M3 page (optional)
--out      where to write M1_Dashboard_<date_time>.html (a new file each time; nothing is overwritten)

Exit codes: 0 dashboard written; 2 an input could not be read (nothing written).
"""
import argparse
import datetime as dt
import os
import sys
from pathlib import Path

from . import __version__, page
from .inputs import InputError, latest_run, read_database, read_run
from .m3 import read_m3


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="m1_dash", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--results", type=Path, help="folder holding Calculate's M1_calc_* runs")
    p.add_argument("--run", type=Path, help="one Calculate run folder (default: the newest in --results)")
    p.add_argument("--data", type=Path, help="the database folder M1_Data/clean (for the Database page)")
    p.add_argument("--m3", type=Path, help="M3 results folder or file (for the Acquisition and finance page)")
    p.add_argument("--out", type=Path, required=True, help="folder for the dashboard file")
    a = p.parse_args(argv)
    print(f"m1_dash {__version__}")
    try:
        if a.run is None and a.results is None:
            raise InputError("give --results (the results folder) or --run (one run folder)")
        run = a.run or latest_run(a.results)
        info, ships = read_run(run)
        db = read_database(a.data)
        m3r = read_m3(a.m3)
    except InputError as exc:
        print(f"Cannot start: {exc}")
        return 2
    now = dt.datetime.now()
    a.out.mkdir(parents=True, exist_ok=True)
    path = a.out / f"M1_Dashboard_{now:%Y-%m-%d_%H%M%S}.html"
    path.write_text(page.build(info, ships, db, now, m3r), encoding="utf-8")
    print(f"results: {run.name} ({len(ships)} ships)" + (f"; database: {len(db)} sales" if db else "")
          + (f"; M3: {m3r['_file']}" if m3r else ""))
    print(f"Dashboard: {path}")
    return 0


if __name__ == "__main__":
    code = main()
    if os.environ.get("M1_RUN_MENU"):
        # Started from the VS Code Run menu: end quietly (a non-zero exit would open the debugger's pop-up).
        print({0: "Finished. Open the dashboard file in your browser.", 2: "Could not start: see the message above."}[code])
    else:
        sys.exit(code)
