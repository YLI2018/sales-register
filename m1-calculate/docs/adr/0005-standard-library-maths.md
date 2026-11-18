# 0005: Only the Python standard library for the maths

Date: 2026-11-05. Status: replaced by 0006 (15 Nov 2026).

The least-squares fit is a few lines (two sums and a division), so no numerical add-on is used. The only add-on is openpyxl, to read the Parameters sheet. Fewer add-ons mean fewer versions to manage and code a reviewer can read line by line.
