# Runbook: filling the template

For analysts. How to run Fill template, what the messages mean and what to do when it stops.

## Before you start

- `sales.csv` and `indicative_prices.csv` are in `M1_Data/clean/` (from m1-extract, or the seed export).
- A case file exists, for example a copy of `examples/case_target_ship_1.json` with your ship.
- Excel does not need to be open; the program never edits an open file.

## Run

**Double-click** `scripts/fill_template.command`. A Terminal window shows the result; press Return to close it.

or **in Terminal**, from this folder:

```bash
PYTHONPATH=src python3 -m m1_fill --data "<data folder>/clean" --case "<case file>" --out "<data folder>/output"
```

To check the data without writing anything, add `--check-only`.

## Write a case file

Copy `examples/case_target_ship_1.json`, change the values and save it under a new name. Field rules are in `docs/data_dictionary.md` (case section). Dates as `YYYY-MM-DD`; numbers with a dot.

## Reading the result

```
sales rows: 275; broker value rows: 395
errors: 0; warnings: 41
written: .../output/M1_VAL-001_2026-11-05_193014.xlsx
41 warnings: see M1_VAL-001_2026-11-05_193014.log
```

Open the workbook in Excel: it recalculates, then the Outputs sheet shows the value and the validity status. Save it in Excel once so the calculated values are stored.

## Messages

| Message | Meaning | What to do |
|---|---|---|
| `ERROR ... missing columns: ...` | A column named in the contract is not in the file | Fix the header row (names exactly as in the data dictionary) |
| `ERROR ... line N, X: required value is empty` | A required field is blank | Fill it from the source report |
| `ERROR ... '28,45' has a comma` | Number written with a comma | Use a dot: 28.45 |
| `ERROR ... is not a date YYYY-MM-DD` | Wrong date format | Write 2026-05-22 |
| `ERROR ... is not allowed; allowed: ...` | Value outside the list (segment, sale type …) | Use a listed value; a new segment needs a change to the contract |
| `ERROR ... is outside A to B` | Number outside its limits | Check for a typing error |
| `ERROR ... already used on line N` | Two rows share an id | Give each row its own id |
| `ERROR ... the template holds 300` | More rows than the template holds | Extend the template (developer task) |
| `WARNING ... price_musd: empty` | No exact price (approximate price in notes) | Nothing; the row cannot be a comparable (rule R3) |
| `WARNING ... dwt: empty` | DWT not reported | Add it if another source gives it |
| `WARNING ... same sale twice?` | Same vessel and report date on two lines | Keep one row; record other reports in notes |
| `WARNING ... reviewed decision without a reason` | Decision in Z without reason | Add the reason |
| `WARNING ... will show 'Duplicate'` | Same broker value twice | Delete one row in indicative_prices.csv |
| `STOPPED: ... already exists` | Output file name taken | Run again (the name includes the time) |
| `STOPPED: template already holds sales data` | A filled workbook was given as template | Use `templates/M1_Comparable_Sales_Template_v1_blank.xlsx` |
| `No module named m1_fill` | Run from the wrong folder, or without `PYTHONPATH=src` | Run from this folder as shown above |
| `No module named openpyxl` | Add-on not installed | `python3 -m pip install openpyxl==3.1.2` |

## After the run

- Keep the `.log` with the workbook: it records the code version and the files used.
- Add the case to the Outputs case log in the workbook (copy row 45, paste values).
