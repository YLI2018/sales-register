# m1-extract

Ship valuation model – personal portfolio project. **Extract** reads the broker reports in the report archive (PDF reports and HSN valuation screenshots), writes what it finds into an Excel **check file**, and, once a person has approved each row, adds the approved rows to the clean data files used by the M1 model.

> **About this project.** A personal portfolio project showing how a ship valuation model can be built, tested and automated as a team would. Any business scenario is hypothetical. It is not affiliated with, or endorsed by, any company. No reports or other broker data are included in this repository.

| M1 project | Does | Status |
|---|---|---|
| m1-report-download | 1 Download: saves broker reports into the archive | v0.1.1, parked (websites block automated download; reports are saved by hand) |
| **m1-extract** | **2 Extract: reads new reports into a check file; adds approved rows to the database** | **v0.1.4** |
| m1-fill-template | 3 Fill template (optional): puts the database and one ship into the Excel template | v0.1.1 |
| m1-calculate | 4 Calculate: values a list of ships in Python with the template's settings | v0.2.1 |
| m1-dashboard | 5 Dashboard: presents Calculate's results as a multi-page HTML dashboard | v0.1.0 |

How the projects fit together, with a flow chart: *M1 Automation System Document* (Google Drive, `M1_Sales_Register/Documentation/1_System`).

## What it does

1. **Finds new reports.** Every report in the archive (`Sources`) is fingerprinted; a report not on the list of reports already read (`extracted_reports.csv`) is new. The first time, reports already typed by hand during M1 are listed without being read.
2. **Reads them.**
   - Advanced Shipping & Trading: reported sales and the indicative price table.
   - Xclusiv and Intermodal: reported sales.
   - HSN Weekly Vessel Valuations: the sale sentences in the screenshots (`…_1.png`, `…_2.png` read as one report), using Apple's built-in text recognition.
3. **Prepares a check file** (`M1_Data/staging/check_<date_time>.xlsx`). For every row it shows the report and page it came from, what to check, and whether the sale is already in the data or is a repeat of another report this week. Clear rows get their **Decision** filled in (OK, or Reject for repeats); rows that need a person say **Check** and have an empty Decision.
4. **Adds approved rows** (`add`). This only runs when every row has a decision. It backs up the clean files, appends the OK rows (new sales get the next ids), moves the check file to `staging/done` and updates the list.

## Install (once)

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Set your folders in `scripts/local_settings.sh` (not in Git):

```bash
export M1_SOURCES="<report archive folder>"
export M1_DATA="<M1_Data folder>"
```

## Run

```bash
PYTHONPATH=src .venv/bin/python -m m1_extract extract --sources "$M1_SOURCES" --data "$M1_DATA"
PYTHONPATH=src .venv/bin/python -m m1_extract add --data "$M1_DATA"
PYTHONPATH=src .venv/bin/python -m m1_extract status --sources "$M1_SOURCES" --data "$M1_DATA"
```

You can also double-click `scripts/extract.command` and `scripts/add_checked_rows.command`, or use the VS Code Run menu. Step by step, with messages: `docs/runbook.md`.

## Project structure

```
m1-extract/
├── README.md, CHANGELOG.md, CONTRIBUTING.md, requirements.txt, .gitignore
├── src/m1_extract/
│   ├── reports.py        ← find reports, group screenshots, fingerprints, list of reports already read
│   ├── pdf_columns.py    ← read a PDF table by word positions (wrapped cells, centred titles)
│   ├── readers.py        ← one reader per broker; HSN text recognition and sentence parsing
│   ├── normalise.py      ← numbers, prices, yards, segments, survey dates, names
│   ├── check_file.py     ← write and read the Excel check file
│   ├── data_files.py     ← clean data: duplicates, checks, backup, append
│   └── __main__.py       ← commands: extract, add, status
├── scripts/              ← double-click shortcuts
├── tests/                ← unit tests and tests on the synthetic reports
└── docs/                 ← architecture, runbook, data dictionary, decision records
```

## Sample reports (synthetic)

The real broker reports cannot be published, so this repository includes three **synthetic** reports instead (`data/sample/`). Each one copies the table layout of a report the extractor reads:

| Synthetic file | Layout copied from |
|---|---|
| `2026-01-09_AdvancedShipping_Market_wk02_SYNTHETIC.pdf` | Advanced Shipping & Trading weekly market report (sales and indicative prices) |
| `2026-01-12_Xclusive_SalesPurchase_wk03_SYNTHETIC.pdf` | Xclusiv weekly sale & purchase report |
| `2026-01-14_intermodal-report-wk02_SYNTHETIC.pdf` | Intermodal weekly report |

The ships, prices and dates are made up, and every page says SYNTHETIC. Each file has a matching `expected_*.csv` listing the rows the extractor should produce, written by hand from the made-up data. `tests/test_sample_reports.py` checks that the extractor produces them. The samples include a two-line yard name, an approximate price, an en bloc pair, an auction and a resale.

The extractor is also tested on the real reports. Those reports and that test stay private, so they are not in this repository.

HSN screenshots are not included in the samples.

To remake the samples: `.venv/bin/python data/sample/make_sample_reports.py` (no extra library needed).

## Tests

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

All tests here run anywhere, with no private data. The ship and company names in the tests are made up. The private test on the real reports (kept off GitHub) checks week 44 of Advanced (21 sales, 32 values), Xclusiv and Intermodal, an HSN screenshot, and agreement with the rows typed by hand during M1.

## Owner

Project owner: the project author. Changes follow `CONTRIBUTING.md`; decisions are recorded in `docs/adr/`.
