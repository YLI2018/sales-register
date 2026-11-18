# 0003: Function and column names follow the Excel steps

Date: 2026-11-05. Status: accepted.

Each step is one function whose docstring names the Excel column or cell it reproduces (for example `adjusted_price` = Sales Register AC). Variable names state what they hold and their unit (`adjusted_price_musd`, `days_to_benchmark`); `a` and `b` keep their names from the formula a × e^(b × age). Output columns use the same names. A reviewer can trace every number to a cell.
