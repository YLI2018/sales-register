"""Command line.

    python3 -m m1_extract extract --sources SOURCES --data M1_DATA      read new reports into a check file
    python3 -m m1_extract add     --data M1_DATA [--check FILE]          add the rows marked OK to the clean data
    python3 -m m1_extract status  --sources SOURCES --data M1_DATA       list reports: new, waiting, added, typed in M1

Exit codes: 0 done; 1 something needs your attention (unreadable report, undecided rows, failed checks); 2 cannot start.
"""
import argparse
import os
import datetime as dt
import shutil
import sys
from pathlib import Path

import pdfplumber

from . import __version__
from . import check_file, data_files, readers
from .reports import find_reports, load_register, new_reports, save_register, seed_register

PDF_READERS = {"advanced": readers.read_advanced, "xclusiv": readers.read_xclusiv, "intermodal": readers.read_intermodal}


def _paths(data: Path):
    return data / "clean", data / "staging", data / "extracted_reports.csv"


def cmd_extract(sources: Path, data: Path) -> int:
    clean, staging, reg_path = _paths(data)
    sales_now, values_now = data_files.read_csv(clean / "sales.csv"), data_files.read_csv(clean / "indicative_prices.csv")
    reports = find_reports(sources)
    register = load_register(reg_path)
    if not register:
        register = seed_register(reports, data_files.typed_source_files(sales_now, values_now))
        print(f"First run: {len(register)} reports already typed in M1 are listed as read.")
    gone = [r for r in register if r.get("status") == "read, waiting for check"
            and not (staging / r.get("check_file", "")).is_file()]
    if gone:
        # The check file was deleted (or moved): forget those reports, so they are read again now.
        register = [r for r in register if r not in gone]
        print(f"Check file missing ({', '.join(sorted({r['check_file'] for r in gone}))}): "
              f"reading {len(gone)} report(s) again.")
    waiting = [r for r in register if r.get("status") == "read, waiting for check"]
    if waiting:
        print(f"Note: {len(waiting)} report(s) are still waiting in a check file: {', '.join(sorted({r['check_file'] for r in waiting}))}")
    todo = new_reports(reports, register)
    if not todo:
        save_register(reg_path, register)
        print("No new reports in", sources)
        return 0
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    check_path = staging / f"check_{stamp}.xlsx"
    all_sales, all_values, log, failed = [], [], [f"m1_extract {__version__}  run {stamp}"], 0
    for rep in todo:
        try:
            if rep.broker == "hsn":
                s, v = readers.read_hsn(rep.files, rep.report_date)
            else:
                with pdfplumber.open(rep.files[0]) as pdf:
                    s, v = PDF_READERS[rep.broker](pdf, rep.files[0].name, rep.report_date)
        except Exception as exc:                                       # one bad report must not stop the others
            failed += 1
            log.append(f"FAILED  {rep.report_id}: {exc}")
            print(f"  could not read {rep.report_id}: {exc}")
            continue
        for r in s:
            r["_dup"] = data_files.already_in_data(r, sales_now)
            twin = next((x for x in all_sales + s[:s.index(r)] if x is not r and x["vessel"]
                         and data_files.norm_key(x["vessel"]) == data_files.norm_key(r["vessel"]) and x["built"] == r["built"]), None)
            if twin and not r["_dup"]:
                # Same sale in two reports: keep the first row, suggest rejecting the repeat, note the second source.
                r["_dup"] = f"in this file: same sale as {twin['vessel']} from {twin['source_file']}"
                price_note = f" at ${r['price_musd']}m" if r["price_musd"] is not None else ""
                twin["notes"] = f"{twin['notes']}; also reported in {r['source_file']}{price_note}"
                if r["price_musd"] is not None and twin["price_musd"] is not None and r["price_musd"] != twin["price_musd"]:
                    twin["_warnings"].append(f"price differs between reports: ${twin['price_musd']}m here, ${r['price_musd']}m in {r['source_file']}")
        for value in v:
            value["_dup"] = data_files.value_already_in_data(value, values_now)
        all_sales += s
        all_values += v
        register.append({"report_id": rep.report_id, "broker": rep.broker, "report_date": rep.report_date.isoformat(),
                         "files": rep.file_names, "fingerprint": rep.fingerprint, "status": "read, waiting for check",
                         "read_at": stamp, "sales_found": len(s), "values_found": len(v), "check_file": check_path.name})
        line = f"read    {rep.report_id}: {len(s)} sales, {len(v)} broker values"
        log.append(line)
        print("  " + line)
    if all_sales or all_values:
        check_file.write(check_path, all_sales, all_values, log[1:])
        print(f"Check file: {check_path}")
    save_register(reg_path, register)
    staging.mkdir(parents=True, exist_ok=True)
    (staging / f"extract_{stamp}.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    return 1 if failed else 0


def cmd_add(data: Path, check: Path = None) -> int:
    clean, staging, reg_path = _paths(data)
    if check is None:
        files = sorted(staging.glob("check_*.xlsx"))
        if not files:
            print("No check file waiting in", staging)
            return 1
        check = files[-1]
    if check.name.startswith("~$"):
        print("That is Excel's temporary file; close the check file in Excel and run again.")
        return 2
    sales, values, problems = check_file.read(check)
    problems += data_files.check_rows(sales, values)
    if problems:
        print(f"Nothing added. Fix these in {check.name}, save, and run again:")
        for p in problems[:15]:
            print("  -", p)
        if len(problems) > 15:
            print(f"  … and {len(problems) - 15} more ({sum('Decision' in p for p in problems)} rows without a decision in all)")
        return 1
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    data_files.backup(clean, stamp)
    n_s, n_v = data_files.append(clean, sales, values)
    done = staging / "done"
    done.mkdir(exist_ok=True)
    shutil.move(str(check), done / check.name)
    register = load_register(reg_path)
    for r in register:
        if r.get("check_file") == check.name and r.get("status") == "read, waiting for check":
            r.update(status="checked and added", added_at=stamp,
                     sales_added=sum(1 for s in sales if s.get("source_file") and r["files"].split(";")[0].strip() in s["source_file"]),
                     values_added=sum(1 for v in values if r["report_id"] in (v.get("source_file") or "")))
    save_register(reg_path, register)
    msg = f"Added {n_s} sales and {n_v} broker values to {clean}. Backup of the previous files: clean/backup/{stamp}_*.csv"
    (staging / "done" / f"add_{stamp}.log").write_text(f"m1_extract {__version__}\n{check.name}\n{msg}\n", encoding="utf-8")
    print(msg)
    print(f"Check file moved to {done / check.name}")
    return 0


def cmd_status(sources: Path, data: Path) -> int:
    _, _, reg_path = _paths(data)
    register = load_register(reg_path)
    by_fp = {r["fingerprint"]: r for r in register}
    for rep in find_reports(sources):
        row = by_fp.get(rep.fingerprint)
        status = row["status"] if row else "NEW: not read yet"
        print(f"  {rep.report_date}  {rep.broker:10}  {status:28}  {rep.file_names}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="m1_extract", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["extract", "add", "status"])
    p.add_argument("--sources", type=Path, help="the report archive folder (Sources)")
    p.add_argument("--data", type=Path, required=True, help="the M1_Data folder (holds clean/)")
    p.add_argument("--check", type=Path, help="check file to add (default: the newest in staging)")
    a = p.parse_args(argv)
    clean = a.data / "clean"
    if not (clean / "sales.csv").exists() or not (clean / "indicative_prices.csv").exists():
        print(f"Cannot start: {clean} must hold sales.csv and indicative_prices.csv")
        return 2
    if a.command in ("extract", "status") and (not a.sources or not a.sources.is_dir()):
        print("Cannot start: --sources must be the report archive folder")
        return 2
    print(f"m1_extract {__version__}")
    if a.command == "extract":
        return cmd_extract(a.sources, a.data)
    if a.command == "add":
        return cmd_add(a.data, a.check)
    return cmd_status(a.sources, a.data)


if __name__ == "__main__":
    code = main()
    if os.environ.get("M1_RUN_MENU"):
        # Started from the VS Code Run menu: end quietly (a non-zero exit would open the debugger's 'SystemExit' pop-up).
        print({0: "Finished.", 1: "Finished: see the messages above.", 2: "Could not start: see the message above."}[code])
    else:
        sys.exit(code)
