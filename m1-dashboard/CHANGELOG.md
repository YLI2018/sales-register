# Changelog

Versions follow semantic versioning (major.minor.patch).

## [0.2.2] - 2026-11-18
### Added
- Automation page: flow from broker reports to this dashboard (download parked, extract, database, calculate, results, dashboard; fill template optional; M3 results file), the five projects with version and status, and facts about this run.
### Changed
- Model roadmap: the voyage estimator is shown as built but not used in this case (grey dashed box and dashed link, with a key), because M3's voyage values are placeholders. M5 (this dashboard) is shown as built, in solid blue, so it no longer looks like the voyage estimator.

## [0.2.1] - 2026-11-18
### Changed
- M3 page: a verdict with warnings shows as a warning, not OK; maximum-bid table shows the re-test and notes that a bid at the top of the grid is not a measured limit and that liquidity is not part of the bid.

## [0.2.0] - 2026-11-18
### Added
- Fifth page, Acquisition and finance (M3), read from the newest M3 results file (`--m3`, optional): headline tiles, verdicts (a deal result is not shown as a model error), owners' cash and the bank year by year, equity IRR sensitivity table, the three bids and the maximum bid, and provenance (model file, SHA-256 fingerprint, results file, data used).
- 5 tests on a made-up M3 results file (13 in all).
### Changed
- Model roadmap: M1+, VE, M2 and M3 now shown as built.

## [0.1.0] - 2026-11-06
### Added
- Dashboard with four pages (Overview, Ship detail, Database, Model roadmap) made from the newest Calculate run.
- Age curve chart per ship (comparable sales, fitted curve, the ship with its value range), validity checks pass or fail, database growth and segment charts, model roadmap diagram.
- Light and dark themes; hover notes on every chart mark; tables behind every chart; prints one page per sheet.
- Run menu item, double-click shortcut, 8 tests.
