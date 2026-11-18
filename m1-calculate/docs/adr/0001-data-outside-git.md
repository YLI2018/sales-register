# 0001: Data and results stay outside Git

Date: 2026-11-05. Status: accepted.

The repository holds code, documents, tests and small examples. Broker data, the clean data files, the template with data and all results live in the shared drive. `.gitignore` excludes `*.csv` (except `examples/`), `*.xlsx`, `*.pdf`, `*.log`, the personal settings file and editor settings. A result is reproduced from a code version plus a data snapshot; `run.log` records both.
