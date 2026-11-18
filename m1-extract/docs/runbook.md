# Runbook: adding new broker reports to the data

## Each week

1. **Save the new reports** in the report archive (`M1_Sales_Register/Sources`), named like the others:
   `2026-11-07_AdvancedShipping_Market_wk45.pdf`, `2026-11-09_Xclusive_SalesPurchase_wk46.pdf`,
   `2026-11-11_intermodal-report-wk45.pdf`, `2026-11-10_HSN_VesselValuations_wk_1.png` (and `_wk_2.png` if the article needs two screenshots).
2. **Extract.** VS Code Run and Debug → "Extract - read new reports into a check file" → ▶ (or double-click `scripts/extract.command`).
   The Terminal lists each report read and how many sales it gave, and the check file's name.
3. **Check.** Open the check file in `M1_Data/staging` in Excel. On the "Sales" and "Broker values" sheets:
   - read **What to check** and **Already in data**; open the report at the **Page** shown when in doubt;
   - correct any cell that is wrong;
   - **Decision** is filled in already for clear rows (OK; Reject for rows already in the data or repeated from another report). Change any you disagree with. Rows marked **Check** have an empty Decision: read **What to check** and choose **OK** or **Reject**;
   - en bloc (sister ships sold together): the price is already split equally between the ships and the note says so ("package $23.5m for … split equally"). Check the ships and the split in the report; mark each ship OK or Reject;
   - save (keep .xlsx and the name) and close Excel.
4. **Add.** Run and Debug → "Add checked rows - add OK rows to the clean data" → ▶ (or double-click `scripts/add_checked_rows.command`).
   The Terminal says how many sales and broker values were added and where the backup is.
5. Projects 3 and 4 now use the new data.

**Status** (Run menu "Status") lists every report: typed in M1, read and waiting for check, checked and added, or NEW.

## Messages

| Message | Meaning | What to do |
|---|---|---|
| `No new reports in …` | Every report in Sources has been read | Save the new reports first |
| `could not read <report>: …` | A report's layout was not recognised | Type its MR sales by hand in the check file or the data; tell the developer |
| `Note: N report(s) are still waiting in a check file` | An earlier check file has not been added yet | Finish and add it |
| `Nothing added. … Decision is 'empty'` | Some rows have no decision | Choose OK or Reject for them |
| `Nothing added. … segment 'X' is not allowed` | A corrected cell breaks the data contract | Use a segment from the list |
| `That is Excel's temporary file` | The check file is still open in Excel | Close it and run again |
| `Cannot start: … must hold sales.csv` | Wrong data folder | Check `scripts/local_settings.sh` |

## Undo an addition

Copy the two files from `M1_Data/clean/backup/<date_time>_*.csv` back over `clean/sales.csv` and `clean/indicative_prices.csv` (remove the date prefix), move the check file back from `staging/done` to `staging`, and set the reports' status in `extracted_reports.csv` back to `read, waiting for check`.
