# Data dictionary

## Inputs

**sales.csv and indicative_prices.csv**: the data contract shared with m1-fill-template (see that project's `docs/data_dictionary.md`). This project reads these columns:

| File | Columns read |
|---|---|
| sales.csv | `id`, `report_date`, `vessel`, `segment`, `dwt`, `built`, `price_musd`, `features`, `en_bloc`, `sale_type`, `notes`, `reviewed_decision` |
| indicative_prices.csv | `report_date`, `broker`, `segment`, `age`, `value_musd` |

Rows are used in file order (rule R6 looks for a name listed earlier).

**Parameters** (sheet of the M1 template; rows 6–20, one per segment):

| Column | Setting | Python name |
|---|---|---|
| A | Segment | `segment` |
| B | Status (Validated / Draft) | `status` |
| C, D, E | DWT min, max, tolerance | `dwt_min`, `dwt_max`, `dwt_tolerance` |
| F, G | Min and max age at sale | `age_min`, `age_max` |
| H, I | Benchmark provider and segment label | `benchmark_provider`, `benchmark_segment` |
| J–L, M–O | Benchmark age labels and ages | `benchmark_labels`, `benchmark_ages` |
| P | Max days sale to benchmark | `benchmark_max_days` |
| Q, R | Min comparables, min R² | `min_comparables`, `min_r_squared` |
| S, T | Range (× SD), near-age window | `range_sd`, `near_age_window` |
| C25:C26, C27:C28 | Charter keywords, review keywords | `charter_keywords`, `review_keywords` |

**ships.csv** (one row per ship to value):

| Column | Required | Meaning |
|---|---|---|
| `case_id` | yes, unique | Reference; repeated in the results |
| `target_name` | yes | Ship name; if it matches a `vessel` in sales.csv, that sale is excluded from its own comparables |
| `segment` | yes | Must have a row on Parameters |
| `dwt` | yes | Deadweight tonnes |
| `year_built` | yes | Year built |
| `valuation_date` | yes | YYYY-MM-DD |
| `known_price_musd` | no | A known or offered price to test against |
| `use_reviewed_decisions` | no (default Yes) | Yes or No |

A single case can also be given as a `.json` file with the same fields (the format of m1-fill-template).

## Outputs (folder `M1_calc_<date_time>`)

**results.csv**: one row per ship.

| Column | Meaning | Excel equivalent |
|---|---|---|
| `case_id`, `target_name`, `segment`, `valuation_date` | The case | Inputs |
| `target_age` | Valuation year − year built | Inputs C19 |
| `value_musd` | Market value | Age Curve O11 |
| `range_low_musd`, `range_high_musd` | Value ∓ Range_SD × SD | O13, O14 |
| `loss_rate` | 1 − e^b | O7 |
| `a_musd`, `b`, `r_squared` | Curve | O5, O6, O8 |
| `n_comparables` | Comparables used | O9 |
| `sd_residuals_musd` | SD of residuals | O12 |
| `near_age_average_musd`, `near_age_count` | Cross-check | O15, O16 |
| `known_price_musd`, `known_gap_pct` | Test against a known price | O17, O19 |
| `valuation_benchmark_date` | Benchmark date used for the valuation date | Benchmarks B72 |
| `information_cutoff` | Latest report date used (= valuation date); later sales and broker values are left out | — |
| `sales_after_cutoff` | Sales of the segment reported after the cutoff, left out | — |
| `broker_values_after_cutoff` | Benchmark broker values reported after the cutoff, left out | — |
| `parameters_status` | Validated / Draft | Inputs C24 |
| `status` | VALID / Usable with warning (draft parameters) / NOT VALID: see failed checks | Outputs C32 |
| `failed_checks` | Checks that failed or warned | Outputs D29:D38 |
| `message` | Extra information, e.g. sales still needing a reviewed decision | – |

**comparables.csv**: one row per ship and comparable: `case_id`, `sale_id`, `vessel`, `report_date`, `age_at_sale`, `price_musd`, `benchmark_date`, `days_to_benchmark`, `benchmark_age`, `index_factor`, `adjusted_price_musd`, `log_price`, `age_gap`, `log_price_gap`, `fitted_price_musd`, `residual_musd`, `decision_source` (Sales Register S, AB, AJ, AD, AC; Age Curve D, T, U, F, G; Sales Register AI).

**results.xlsx**: the same results for reading in Excel.

| Sheet | Content |
|---|---|
| Results | One row per ship (as results.csv), with a link to its Age Curve sheet |
| Curve <case_id> | Laid out like the template's Age Curve sheet: key numbers from Python (column B) beside an Excel check (column C: live SLOPE, INTERCEPT, RSQ, COUNT, STDEV formulas on the table below, recalculated when Excel opens the file); the comparables table from row 26 (vessel, report date, age, price, benchmark date and age, index factor, adjusted price, LN, fitted price, residual, decision source); a chart of adjusted price against age with the exponential trendline, its equation and R², and the target ship marked |

**run.log**: version, inputs, one line per ship, and any failed check.
