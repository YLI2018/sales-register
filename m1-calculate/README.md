# m1-calculate

Ship valuation model – personal portfolio project. **Calculate** values one ship, or a whole list, with the M1 comparable sales model, in Python, without Excel. Its results match the Excel model to 9 decimal places.

> **About this project.** A personal portfolio project showing how a ship valuation model can be built, tested and automated as a team would. Any business scenario is hypothetical. It is not affiliated with, or endorsed by, any company. No broker data is included in this repository.

| M1 project | Does | Status |
|---|---|---|
| m1-report-download | 1 Download: saves broker reports into the archive | v0.1.1, parked (websites block automated download; reports are saved by hand) |
| m1-extract | 2 Extract: reads new reports into a check file; adds approved rows to the database | v0.1.4 |
| m1-fill-template | 3 Fill template (optional): puts the database and one ship into the Excel template | v0.1.1 |
| **m1-calculate** | **4 Calculate: values a list of ships in Python with the template's settings** | **v0.2.1** |
| m1-dashboard | 5 Dashboard: presents Calculate's results as a multi-page HTML dashboard | v0.1.0 |

How the projects fit together, with a flow chart: *M1 Automation System Document* (Google Drive, `M1_Sales_Register/Documentation/1_System`).

## What it does

1. Reads the clean data (`sales.csv`, `indicative_prices.csv`), the settings from the template's **Parameters** sheet, and the ships to value (`ships.csv`, or one case `.json`).
2. For each ship: applies the selection rules R1–R7 and the reviewed decisions, finds each sale's benchmark date, moves every price to the valuation date (indexation), fits the age curve (log-linear least squares), and reads the value, the range and the cross-checks.
3. Runs the 9 validity checks and gives each ship a status: VALID, usable with warning (draft settings), or NOT VALID.
4. Writes a new folder `M1_calc_<date_time>` with `results.xlsx` (a Results sheet and one Age Curve sheet with chart per ship), `results.csv`, `comparables.csv` and `run.log`.

Method: see the model specification (`docs/model_specification.md`). Every step is named after the Excel column it reproduces (`docs/architecture.md`).

## Install

Python 3.10 or later, two add-ons, and the valuation repository **shipping-vessel-valuation**, which holds the one
M1 age-curve fit (m1-calculate calls it; it does not keep its own copy):

```bash
python3 -m pip install openpyxl==3.1.2 numpy
export SHIPPING_VALUATION_SRC="<folder of shipping-vessel-valuation>/src"
```

Without `SHIPPING_VALUATION_SRC` the program stops with a message saying so.

## Run

```bash
PYTHONPATH=src python3 -m m1_calc --data "<data folder>/clean" --parameters "<template>.xlsx" --ships examples/ships_example.csv --out "<output folder>"
```

or double-click `scripts/calculate.command`. Example output (whole database on 12 Nov 2026, all report dates):

```
  VAL-001    Target Ship 1                 $29.79m   52 comparables  VALID
  VAL-002    Target Ship 2                 $29.73m   52 comparables  VALID
  VAL-003    Example MR 2015           $38.65m   53 comparables  VALID
  VAL-004    Target Ship 1                 $29.77m   50 comparables  NOT VALID: see failed checks
```

**Valuing as of a past date (no hindsight).** Calculate uses every row it is given. For a valuation dated in the past, first cut the data at that date, then run on the cut:

```bash
python3 scripts/historical_cut.py "<M1_Data folder>" 2026-05-22
PYTHONPATH=src python3 -m m1_calc --data "<M1_Data folder>/historical_2026-05-22/clean" --parameters "<template>.xlsx" --ships "<ships>.csv" --out "<M1_Data folder>/historical_2026-05-22"
PYTHONPATH=src python3 scripts/selection_register.py "<M1_Data folder>" 2026-05-22 "<template>.xlsx"
```

Target Ship 1 on data reported by 22 May 2026: **$29.67m, 43 comparables, VALID** (the M1 v11 result). `selection_register.py` writes one line per MR sale: used, or left out and why.

Step-by-step use and troubleshooting: `docs/runbook.md`. File formats: `docs/data_dictionary.md`.

## Project structure

```
m1-calculate/
├── README.md                  ← start here
├── CHANGELOG.md               ← what changed in each version
├── CONTRIBUTING.md            ← how to make a change
├── pyproject.toml             ← Python version and add-on
├── .gitignore                 ← keeps data, results and personal settings out of Git
├── src/m1_calc/
│   ├── inputs.py              ← reads data, parameters and ships
│   ├── engine.py              ← the valuation, one function per Excel step
│   ├── shared_m1.py           ← finds the one M1 fit in shipping-vessel-valuation
│   ├── outputs.py             ← results.csv, comparables.csv, run.log
│   ├── workbook.py            ← results.xlsx: Results sheet, one Age Curve sheet per ship
│   └── __main__.py            ← command line
├── scripts/
│   └── calculate.command      ← double-click shortcut
├── examples/
│   ├── ships_example.csv      ← four example cases
│   └── case_target_ship_1.json    ← validation case 1
├── tests/                     ← 27 automatic checks, incl. reconciliation with Excel
└── docs/
    ├── architecture.md        ← steps, Excel equivalents, design choices
    ├── runbook.md             ← how to run it; messages; troubleshooting
    ├── data_dictionary.md     ← input and output files, column by column
    ├── model_specification.md ← where the model specification is
    └── adr/                   ← decision records
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The reconciliation with Excel needs three settings; without them it is skipped:

```bash
export M1_DATA="<data folder>"
export M1_PARAMETERS="<M1 template workbook>"
export M1_EXCEL="<workbook saved by Excel with validation case 1>"
```

## Owner

Model owner: the project author. Changes follow `CONTRIBUTING.md`; decisions are recorded in `docs/adr/`.
