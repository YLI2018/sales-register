# Changelog

Versions follow semantic versioning (major.minor.patch).


## [0.3.0] - 2026-11-15
### Changed
- One M1: the age-curve fit now comes from the valuation repository (shipping-vessel-valuation, `fit_age_curve`) instead of m1-calculate's own copy (docs/adr/0006-one-m1-fit.md). Set `SHIPPING_VALUATION_SRC` to its `src` folder. numpy is now needed. Results unchanged: all tests pass, including the reconciliation with Excel.
- Information cutoff: a valuation uses only sales and broker values reported on or before its valuation date (no later comparable, no later benchmark). results.csv and run.log record the cutoff and how many later rows were left out. On today's database the validation case is again $29.67m from 43 comparables (before: $29.79m from 52, using 16 sales reported after 22 May). The reconciliation test now checks against M1_Market_Database_v11.xlsx on the full database; v10 used sales reported after its valuation date, so it can no longer be reproduced.
### Fixed
- Data that cannot be fitted (fewer than 3 comparables, all the same age) gives NOT VALID with the reason, instead of stopping the program. 27 tests.

## [Unreleased] - 2026-11-12
### Added
- `scripts/historical_cut.py`: copies the database cut at a valuation date (sales and broker values reported on or before it) to `M1_Data/historical_<date>/clean/`, so a past-date valuation uses no later information.
- `scripts/selection_register.py`: one line per MR sale for a valuation date (used / excluded and why) and the count removed by each rule.
### Changed
- `scripts/age_curve_check.py` and `scripts/age_curve_plot.py` read M1_Market_Database_v11.xlsx (43 comparables, $29.67m); all 14 results match Excel.
- README and model_specification.md: validation case 1 on data reported by 22 May 2026.

## [0.2.1] - 2026-11-05
### Fixed
- The reconciliation with Excel now runs on the data as it was when the Excel workbook was saved (first 275 sales, 395 broker values). Before, it failed as soon as new weeks were added to the database, although the calculation was right. 25 tests.

## [0.2.0] - 2026-11-05
### Added
- results.xlsx in every run: a Results sheet (one row per ship) and one Age Curve sheet per ship, laid out like the template's Age Curve sheet: key numbers, an "Excel check" column of live formulas (SLOPE, INTERCEPT, RSQ, STDEV) on the same comparables, the comparables table, and a black-and-grey chart with the exponential trendline and the target marked.

## [0.1.1] - 2026-11-05
### Changed
- A date written as DD/MM/YYYY now stops with a hint that Excel rewrote the dates (found when a ships file was saved from Excel).

## [0.1.0] - 2026-11-05
### Added
- Readers for the clean data files, the template's Parameters sheet and a ship list (CSV) or a single case (JSON).
- The valuation engine, one function per Excel step: benchmark table, nearest benchmark date, rules R1–R6, automatic screen, decision used, benchmark age, indexation, OLS age curve, value, range, near-age cross-check, known-price test, 9 validity checks and status.
- Outputs: results.csv, comparables.csv and run.log in a new dated folder.
- 22 tests, including reconciliation with Excel's saved values for validation case 1 (to 9 decimal places).
