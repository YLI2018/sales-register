# Changelog

Versions follow semantic versioning (major.minor.patch).


## [Unreleased]
### Added
- Three synthetic sample reports (Advanced, Xclusiv and Intermodal layouts, made-up ships) in `data/sample/`, their expected rows, and `tests/test_sample_reports.py`, so the extractor can be tried and tested without private reports.
### Known issues (from code review, 15 Nov 2026)
- Repeat sales of the same ship can be dropped: duplicates are found by ship name and build year, with no date window, so a ship sold twice may have its second sale treated as a duplicate. Needs a sale identifier (ship + date).
- The 10 exact-price bulker sales in the 8 Intermodal reports are still not added (decision: note only). The +0.4% test on one ship does not prove the data is complete elsewhere.

## Run log - 2026-11-12 (no code change)
- Extract run on 40 earlier PDF reports (Intermodal 17, Xclusiv 15, Advanced 8) and 19 HSN screenshot dates, 16 Dec 2025 to 20 May 2026: 716 sale rows and 256 broker values in check_2026-11-12_202447.xlsx.
- Text recognition found no sale sentences on 6 HSN dates (16 Dec, 6 Jan, 28 Jan, 24 Feb, 3 Mar, 5 May); their 50 sales were typed into the check file from the screenshots.
- 8 Intermodal PDFs gave 0 sales (17 Dec, 25 Feb, 4 Mar, 18 Mar, 8 Apr, 30 Apr, 13 May, 20 May): reader limitation to look at.
- Checked by hand (15 Nov 2026): those 8 reports hold 11 MR tanker sales, all already in the data from Advanced or Xclusiv; and 10 bulker sales with an exact price (plus 2 approximate) not in the data. Effect on M1+ model A: +0.4% on the validation case. Not added.
- 102 rows left for a person were decided by written rules (see M1_v11_Comparable_Selection.md); 285 sales and 256 broker values added.

## [0.1.4] - 2026-11-05
### Changed
- The check file fills in Decision for clear rows (OK; Reject for rows already in the data or repeated). Only 'Check' rows are left empty for a person.

## [0.1.3] - 2026-11-05
### Changed
- Run from the VS Code Run menu (M1_RUN_MENU set): ends with a one-line message instead of the debugger's SystemExit pop-up.

## [0.1.2] - 2026-11-05
### Fixed
- A deleted check file no longer blocks its reports: Extract reads them again. 18 tests.

## [0.1.1] - 2026-11-05
### Fixed
- En bloc sales: sister ships sold together are joined and the package price is split equally (previously the whole package price went to one ship and the other ship had no price). Works when the price sits on either ship or between them, when the sister ship is not marked en bloc, and for three or more sisters; a buyer name printed across the rows is joined. A price marked 'each' is not split.
- HSN: a sentence naming two ships ("A & B") gives one row per ship with the price split.
- 17 tests (en bloc cases added, including two real reports).

## [0.1.0] - 2026-11-05
### Added
- Report finding by fingerprint, screenshot grouping, list of reports already read (first run lists the reports typed by hand during M1).
- Readers: Advanced (sales and indicative prices), Xclusiv (sales), Intermodal (sales), HSN Weekly Vessel Valuations screenshots (Apple text recognition).
- Duplicate checks against the data and between reports of the same week; Excel check file with suggestions; adding approved rows after a backup.
- 13 tests, including real reports. Agreement with the rows typed by hand during M1: 92% of rows found again; year built 100%, DWT 95%, segment 96% of those found; Advanced broker values 100%.
### Known limits
- Older Intermodal layout (weeks 7, 12, 18 of 2026) mostly not read; Xclusiv segment from DWT needs checking.
