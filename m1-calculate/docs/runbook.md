# Runbook: valuing ships

## Before you start

- `sales.csv` and `indicative_prices.csv` are in `M1_Data/clean`.
- The M1 template (with its Parameters sheet) is available.
- The ships to value are in your own ships file in the data folder (`M1_Data/ships.csv`): start from a copy of `examples/ships_example.csv`, keep the header, one row per ship. Your list stays with the data, not in Git. Edit it in VS Code or a text editor (Excel rewrites the dates).

## Run

**Double-click** `scripts/calculate.command` (paths come from `scripts/local_settings.sh`, which stays on your computer), or **in VS Code**: Run and Debug → "Calculate - value the ships in examples/ships_example.csv", or **in Terminal** from this folder:

```bash
PYTHONPATH=src python3 -m m1_calc --data "<data folder>/clean" --parameters "<template>.xlsx" --ships "<ships file>" --out "<output folder>"
```

## Reading the result

The screen shows one line per ship (value, number of comparables, status) and the folder written. In that folder:

- `results.csv`: open in Excel; one row per ship.
- `comparables.csv`: the sales behind each value, with adjusted prices and residuals.
- `run.log`: the run, and which checks failed for any ship that is not VALID.

Use a value only if its status is **VALID**, or "Usable with warning" with the warning stated.

## Messages

| Message | Meaning | What to do |
|---|---|---|
| `STOPPED: sales.csv: not found` | Wrong data folder | Point `--data` at the `clean` folder |
| `STOPPED: ... has a comma` | A number written with a comma | Fix the data file (use a dot) |
| `STOPPED: ... missing columns` | A file does not follow the data contract | Fix the header |
| `STOPPED: Parameters row N ... not a number` | A setting is blank or text | Fix the Parameters sheet |
| `STOPPED: ... '22/05/2026' is not a date YYYY-MM-DD` | The file was saved by Excel, which rewrote the dates | Change the dates back to 2026-05-22; edit CSV files in VS Code or a text editor, not Excel |
| `STOPPED: ships.csv: case_id must be unique` | Two ships share a case_id | Give each its own |
| `NOT VALID` with "N sales need a reviewed decision" | Flagged sales (en bloc, DPP …) have no decision and the case does not use reviewed decisions | Decide them (reviewed_decision in sales.csv) or set `use_reviewed_decisions` to Yes |
| `NOT VALID` with "Comparables' benchmark dates within max days" | Weekly benchmark reports are missing for some sales | Add those reports to indicative_prices.csv |
| `NOT VALID` with "segment ... has no Parameters row" | The segment has no settings | Add and validate a row on Parameters |
| `Usable with warning (draft parameters)` | The segment's settings are not validated yet | Check them, back-test, set status to Validated |
