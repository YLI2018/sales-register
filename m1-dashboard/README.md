# m1-dashboard

Ship valuation model – personal portfolio project. **Dashboard** turns the results of Calculate (project 4) into one HTML file with six pages, so the valuation can be presented, not just computed.

> **About this project.** A personal portfolio project showing how a ship valuation model can be built, tested, automated and presented as a team would. Any business scenario is hypothetical. It is not affiliated with, or endorsed by, any company. No broker data is included in this repository.

| M1 project | Does | Status |
|---|---|---|
| m1-report-download | 1 Download: saves broker reports into the archive | v0.1.1, parked (websites block automated download; reports are saved by hand) |
| m1-extract | 2 Extract: reads new reports into a check file; adds approved rows to the database | v0.1.4 |
| m1-fill-template | 3 Fill template (optional): puts the database and one ship into the Excel template | v0.1.1 |
| m1-calculate | 4 Calculate: values a list of ships in Python with the template's settings | v0.3.0 |
| **m1-dashboard** | **5 Dashboard (M5): presents Calculate's results (and the M3 acquisition and finance results) as a multi-page HTML dashboard** | **v0.2.2** |

How the projects fit together, with a flow chart: *M1 Automation System Document* (Google Drive, `M1_Sales_Register/Documentation/1_System`).

## The six pages

| Page | Shows |
|---|---|
| **Overview** | Headline tiles (ships valued, how many VALID, sales in the database, latest report) and a table of every ship: value, value range, comparables, R², status |
| **Ship detail** | One ship: value, range, value lost per year, curve fit, gap to a known price; the age curve with its comparable sales; the nine validity checks, pass or fail |
| **Database** | Sales in the database by report date, and by segment |
| **Automation** | How broker reports become these valuations: the flow from reports to this dashboard, the five projects with version and status, and facts about this run |
| **Acquisition and finance (M3)** | From the newest M3 results file: equity IRR against the required return, maximum bid and which test limits it, lowest debt service cover, value-rule headroom, the four verdicts, owners' cash and the bank year by year, the equity IRR sensitivity table, and where the numbers came from (model file, fingerprint, data used) |
| **Model roadmap** | How M1 feeds the next models (voyage estimator, valuation, acquisition and finance, build vs buy, hedonic regression, dashboard) and what M1 gives each |

The file is self-contained: no internet, no add-ons, one file to open or send. Hover over any chart mark for its numbers.

## Run

```bash
PYTHONPATH=src python3 -m m1_dash --results "$M1_DATA/results" --data "$M1_DATA/clean" --m3 "$M3_RESULTS" --out "$M1_DATA/dashboard"
```

It uses the newest Calculate run (`--run FOLDER` picks another) and, with `--m3`, the newest `M3_results_*.json` in the M3 results folder (without it the M3 page says how to add it) and writes `M1_Dashboard_<date_time>.html`; nothing is overwritten. Or use the VS Code Run menu (*Dashboard - make it from the newest Calculate results*), or double-click `scripts/make_dashboard.command`, which also opens the file. Step by step: `docs/runbook.md`.

## Project structure

```
m1-dashboard/
├── README.md, CHANGELOG.md, CONTRIBUTING.md, pyproject.toml, requirements.txt, .gitignore
├── src/m1_dash/
│   ├── inputs.py     ← read Calculate's results.csv, comparables.csv, run.log and the database
│   ├── charts.py     ← age curve, range strip, database growth and segment charts (inline SVG)
│   ├── roadmap.py    ← the model roadmap: models, links, what M1 gives each
│   ├── m3.py         ← read the M3 results file; the Acquisition and finance page
│   ├── automation.py ← the Automation page: flow and the five projects
│   ├── page.py       ← the six pages, styles (light and dark) and hover notes
│   └── __main__.py   ← command line and exit codes
├── scripts/          ← double-click shortcut; local_settings.example.sh
├── tests/            ← tests on a small made-up Calculate output
└── docs/             ← architecture, runbook, data dictionary, decision records
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Owner

Project owner: the project author. Changes follow `CONTRIBUTING.md`; decisions are recorded in `docs/adr/`.
