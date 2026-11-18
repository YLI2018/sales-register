# 0001: Data stays outside Git

Date: 2026-11-05. Status: accepted.

## Context
The inputs are broker reports and data typed from them. Broker reports are free to read but their terms may restrict storing and redistributing their content. The data changes every week; the code changes only through review.

## Decision
The repository holds code, documents, tests, examples and the blank template (formulas, no data). Broker PDFs, `sales.csv`, `indicative_prices.csv`, filled workbooks and logs live in the shared drive (`M1_Sales_Register/M1_Data/`). `.gitignore` excludes `*.csv`, `*.pdf`, `*.png`, `*.log` and every `.xlsx` except the blank template.

## Consequences
- The repository can be shared inside the company (and reviewed) without exposing licensed data.
- A result is reproduced from a code version (Git) plus a data snapshot (the drive); the log records both.
- The round-trip test needs the data folder and is skipped without it.
