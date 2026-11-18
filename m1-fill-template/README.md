# m1-fill-template

Ship valuation model – personal portfolio project. **Fill template** is one of four projects that automate M1, the comparable sales valuation model. It takes the checked data files and a valuation case and writes them into a copy of the blank M1 Excel template, ready to open.

> **About this project.** A personal portfolio project showing how a ship valuation model can be built, tested and automated as a team would. The business scenario (a shipowner valuing and selling an MR tanker) is hypothetical. It is not affiliated with, or endorsed by, any company. No broker data is included in this repository.


| M1 project | Does | Status |
|---|---|---|
| m1-report-download | 1 Download: saves broker reports into the archive | v0.1.1, parked (websites block automated download; reports are saved by hand) |
| m1-extract | 2 Extract: reads new reports into a check file; adds approved rows to the database | v0.1.4 |
| **m1-fill-template** | **3 Fill template (optional): puts the database and one ship into the Excel template** | **v0.1.1** |
| m1-calculate | 4 Calculate: values a list of ships in Python with the template's settings | v0.2.1 |
| m1-dashboard | 5 Dashboard: presents Calculate's results as a multi-page HTML dashboard | v0.1.0 |

How the projects fit together, with a flow chart: *M1 Automation System Document* (Google Drive, `M1_Sales_Register/Documentation/1_System`).

The projects connect only through files. The file format between m1-extract and this project is the **data contract** in `docs/data_dictionary.md`.

## What it does

1. Reads `sales.csv` and `indicative_prices.csv` from a data folder, and a case file (JSON).
2. Checks every value against the data contract. **Errors stop the run** and nothing is written; **warnings** are listed and the run continues.
3. Copies the blank template, writes the data into the **input columns only**, and writes the case on the Inputs sheet.
4. Saves `M1_<case_id>_<date_time>.xlsx` and a `.log` with every check. Excel recalculates the workbook on opening.

It never changes the blank template, never writes over a formula and never overwrites an output.

## Install

Python 3.10 or later. One add-on:

```bash
python3 -m pip install openpyxl==3.1.2
```

## Run

```bash
PYTHONPATH=src python3 -m m1_fill --data "<data folder>/clean" --case examples/case_target_ship_1.json --out "<data folder>/output"
```

Or double-click `scripts/fill_template.command` (folders are set at the top of that file).

Options: `--check-only` runs the checks and writes nothing; `--template FILE` uses another blank template. Exit code 0 = written, 1 = data errors, 2 = template or file problem. Step-by-step use, messages and troubleshooting: `docs/runbook.md`.

## Project structure

```
m1-fill-template/
├── README.md                      ← start here
├── CHANGELOG.md                   ← what changed in each version
├── CONTRIBUTING.md                ← how to make a change
├── pyproject.toml                 ← Python version and add-ons
├── .gitignore                     ← keeps data and filled workbooks out of Git
├── templates/
│   └── M1_Comparable_Sales_Template_v1_blank.xlsx   ← the 8 M1 sheets, formulas, no data
├── src/m1_fill/
│   ├── contract.py                ← the data contract: fields, types, allowed values, target cells
│   ├── read_data.py               ← reads and checks the files
│   ├── write_workbook.py          ← writes into a copy of the template
│   ├── charts.py                  ← keeps the template's charts exactly as designed
│   └── __main__.py                ← command line
├── scripts/
│   ├── fill_template.command      ← double-click shortcut
│   ├── make_blank_template.py     ← builds the blank template from the full template
│   └── export_seed_from_v10.py    ← one-off: v10's data as contract files (stands in for m1-extract)
├── examples/
│   └── case_target_ship_1.json        ← validation case 1
├── tests/                         ← automatic checks (25)
└── docs/
    ├── architecture.md            ← how it works and why
    ├── runbook.md                 ← how to run it; messages; troubleshooting
    ├── data_dictionary.md         ← the data contract, column by column
    ├── model_specification.md     ← where the model specification is
    └── adr/                       ← decision records
```

Data is **not** in this repository (`docs/adr/0001-data-outside-git.md`). It lives in the shared drive:

```
M1_Sales_Register/M1_Data/
├── clean/      ← sales.csv, indicative_prices.csv
└── output/     ← filled workbooks and logs
```

## Tests

```bash
PYTHONPATH=src:tests python3 -m unittest discover -s tests -v
```

The round-trip test (seed data → filled workbook → same data as the reference template → validation case 1 gives $29.52m) also needs:

```bash
export M1_DATA="<data folder>"
export M1_REFERENCE="<path to M1_Comparable_Sales_Template_v1.xlsx>"
```

Without them it is skipped; the other tests need no data.

## Owner

Model owner: the project author. Changes follow `CONTRIBUTING.md`; decisions are recorded in `docs/adr/`.
