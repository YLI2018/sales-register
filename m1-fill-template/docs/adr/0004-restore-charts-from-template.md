# 0004: Restore the template's charts after saving

Date: 2026-11-05. Status: accepted.

## Context
openpyxl, the library used to write the workbook, reads charts only partly and writes them back with default formatting (titles, colours, trendline label and labelled points are lost or changed).

## Decision
After saving, `charts.restore_charts` copies the chart definitions (`xl/charts/chartN.xml`) from the template file into the saved file. It refuses if the two files do not hold the same chart parts.

## Consequences
- Filled workbooks show the charts exactly as designed.
- If the template's charts change, nothing in the code changes; if a chart is added, the parts still match because both files come from the same template.
