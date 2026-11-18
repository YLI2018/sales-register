# Data dictionary

## Inputs (written by m1-calculate)

| File | Columns used |
|---|---|
| `results.csv` | case_id, target_name, segment, valuation_date, target_age, value_musd, range_low_musd, range_high_musd, loss_rate, a_musd, b, r_squared, n_comparables, known_price_musd, status, failed_checks (separated by `;`), message |
| `comparables.csv` | case_id, vessel, report_date, age_at_sale, price_musd, adjusted_price_musd, fitted_price_musd |
| `run.log` | lines `m1_calc <version>`, `run: <date time>`, `sales: N; broker values: N; ships: N` |
| `clean/sales.csv` (optional) | report_date, segment |

## Output

`M1_Dashboard_<YYYY-MM-DD_HHMMSS>.html`: one HTML file, UTF-8, no outside links.

## Values shown

| Shown as | From | Meaning |
|---|---|---|
| Value | value_musd | Market value in US$ million on the valuation date |
| Value range | range_low_musd to range_high_musd | Value ± one standard deviation of the curve's residuals |
| Value lost per year | loss_rate | 1 − e^b: share of value lost each year of age |
| Curve fit (R²) | r_squared | How closely the curve fits the comparables (1 = perfectly) |
| Status | status | VALID; Usable with warning; NOT VALID with the failed checks |
| Age curve | a_musd, b | value = a × e^(b × age) |
