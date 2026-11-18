# Synthetic sample reports

The real broker reports cannot be published, so this repository includes three **synthetic** reports instead (this folder). Each one copies the table layout of a report the extractor reads:

| Synthetic file | Layout copied from |
|---|---|
| `2026-01-09_AdvancedShipping_Market_wk02_SYNTHETIC.pdf` | Advanced Shipping & Trading weekly market report (sales and indicative prices) |
| `2026-01-12_Xclusive_SalesPurchase_wk03_SYNTHETIC.pdf` | Xclusiv weekly sale & purchase report |
| `2026-01-14_intermodal-report-wk02_SYNTHETIC.pdf` | Intermodal weekly report |

The ships, prices and dates are made up, and every page says SYNTHETIC. Each file has a matching `expected_*.csv` listing the rows the extractor should produce, written by hand from the made-up data. `tests/test_sample_reports.py` checks that the extractor produces them. The samples include a two-line yard name, an approximate price, an en bloc pair, an auction and a resale.

The extractor is also tested on the real reports. Those reports and that test stay private, so they are not in this repository.

HSN screenshots are not included in the samples.

To remake the samples: `.venv/bin/python data/sample/make_sample_reports.py` (no extra library needed).

