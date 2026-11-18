# Changelog

All notable changes to this project. Versions follow semantic versioning (major.minor.patch).


## Run log - 2026-11-12 (no code change)
- The whole database (593 sales) is over the template's 300-row limit, so M1_Market_Database_v11.xlsx was filled from the MR rows of the data cut at 22 May 2026 (78 sales, 595 broker values): 43 comparables, $29.67m, recalculated in Excel. Entries below refer to the v10 seed data ($29.52m).

## [0.1.1] - 2026-11-05
### Changed
- Blank template in house style: black and grey only (dark grey headings, light grey formula cells, white input cells with a border, no coloured tabs, grey data-check highlight, grey and black charts).
- Seed export drops private research remarks from notes ("check whether linked to ..."); market facts are kept.

## [0.1.0] - 2026-11-05
### Added
- Data contract for `sales.csv`, `indicative_prices.csv` and the case JSON (`src/m1_fill/contract.py`, `docs/data_dictionary.md`).
- Checks: required columns and values, types, allowed values, limits, capacity, unique id; warnings for missing price or DWT, repeated sales, duplicate broker values, decisions without a reason.
- Writing into a copy of the blank template (input columns only), the case on Inputs, full recalculation on opening, log file; charts restored from the template.
- Blank template `M1_Comparable_Sales_Template_v1_blank.xlsx` (8 M1 sheets, formulas only).
- Seed export from M1 v10 (stands in for m1-extract).
- 25 tests, including a round trip to validation case 1 (Target Ship 1: 30 comparables, $29.52m).
### Decided during the first run
- `yard_country` is free text (v10 holds a Danish yard, outside the original list).
- Spaces at the start and end of values are removed (v10 held trailing spaces in 128 note cells).
