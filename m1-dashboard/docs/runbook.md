# Runbook

## Each week, after Calculate

1. VS Code: **Cmd+Shift+D** (or View › Run), choose **Dashboard - make it from the newest Calculate results (5 m1-dashboard)**, click ▶.
   Or double-click `scripts/make_dashboard.command`, which also opens the file.
2. The Terminal shows the results folder used and `Dashboard: …/M1_Data/dashboard/M1_Dashboard_<date_time>.html`, then **Finished.**
3. Open that file in your browser (double-click it in Finder). Use the tabs at the top: Overview, Ship detail, Database, Model roadmap.

## Messages

| Message | Meaning | Do |
|---|---|---|
| `Cannot start: no Calculate results in …` | Calculate has not been run, or `--results` is the wrong folder | Run Calculate (project 4) first |
| `… results.csv not found` | `--run` is not a Calculate run folder | Choose a folder named `M1_calc_<date_time>` |
| `--data must be the M1_Data/clean folder` | The database folder is wrong | Check the path in `.vscode/launch.json` |

## Presenting

- The Overview page answers "what are the values"; Ship detail answers "why"; the Model roadmap answers "what next".
- Print or save as PDF from the browser: each page prints on its own sheet.
- The file holds no broker names or reports, only model results; check the ship names before sending it to anyone.
