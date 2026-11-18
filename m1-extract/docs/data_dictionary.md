# Data dictionary

## Inputs

| Input | Where | Notes |
|---|---|---|
| Broker reports | `Sources/` (report archive) | File names start with the date: `2026-10-31_AdvancedShipping_Market_wk44.pdf`, `2026-11-02_Xclusive_SalesPurchase_wk45.pdf`, `2026-11-04_intermodal-report-wk44.pdf`, `2026-11-04_HSN_VesselValuations_wk_1.png` (+ `_wk_2.png`). The broker is recognised from the name |
| Clean data | `M1_Data/clean/sales.csv`, `indicative_prices.csv` | The data contract shared with m1-fill-template (see its data dictionary); used for duplicates and next ids |

## Outputs

| Output | Where | Content |
|---|---|---|
| List of reports | `M1_Data/extracted_reports.csv` | One row per report: `report_id`, `broker`, `report_date`, `files`, `fingerprint` (SHA-256), `status` (`typed in M1`, `read, waiting for check`, `checked and added`), `read_at`, `sales_found`, `values_found`, `check_file`, `added_at`, `sales_added`, `values_added` |
| Check file | `M1_Data/staging/check_<date_time>.xlsx` | Sheets "How to check", "Sales", "Broker values". Columns: `Decision` (OK / Reject, chosen from a list), `Suggestion`, `What to check`, `Already in data`, `Report`, `Page`, then the data-contract fields |
| Extract log | `M1_Data/staging/extract_<date_time>.log` | Reports read and the number of rows each produced, and any report that could not be read |
| Added rows | appended to `M1_Data/clean/*.csv` | In the data-contract format; new sales get the next free id |
| Backup | `M1_Data/clean/backup/<date_time>_sales.csv`, `…_indicative_prices.csv` | The clean files as they were before each addition |
| Done | `M1_Data/staging/done/` | Checked files and `add_<date_time>.log` |

## Typing conventions followed (as in M1)

| Field | Rule |
|---|---|
| `report_date` | The report's date (file name; for HSN the article title) |
| `price_musd` | Exact prices only. "rgn", "high", "low", "xs" … leave it empty and go to `features` as "Approximate price: …" |
| `features` | Scrubber, ice class, DPP, charter, approximate price |
| `notes` | Page, survey dates ("SS 02/2027"), container size in TEU, VesselsValue value, other reports of the same sale |
| `next_survey` | The earliest SS or DD date given, first of the month |
| `sale_type` | Resale if built after the report year or marked resale; Auction if sold by auction or bidding |
| `en_bloc` | Y when the report says en bloc, or two ships share one sale. Each ship gets one row; `price_musd` is the package price divided equally, and `notes` names the package |
| `segment` | From the broker's type or size code; from DWT when none is given (flagged) |
