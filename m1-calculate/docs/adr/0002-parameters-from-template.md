# 0002: Settings are read from the template's Parameters sheet

Date: 2026-11-05. Status: accepted.

## Context
The Excel template and this project must apply the same settings (size band, ages, benchmark provider, thresholds). Two copies of the settings would drift apart.

## Decision
The settings are read from the Parameters sheet of the M1 template, typed values only (rows 6–20, keywords in C25:C28). The workbook is opened read-only; calculated cells are never read.

## Consequences
- One source of settings, under the template's change log.
- This project needs the template file to run. If the Parameters layout changes, `inputs.read_parameters` and `docs/data_dictionary.md` change with it.
