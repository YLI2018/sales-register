# Data dictionary: the data contract

The files Fill template reads, column by column. The code version of this contract is `src/m1_fill/contract.py`; a test checks that every field there is listed here.

## General format rules

| Rule | Detail |
|---|---|
| Encoding | UTF-8 (a byte-order mark is accepted) |
| Separator | Comma; text containing commas is quoted |
| Header | First row, column names exactly as below; order does not matter |
| Dates | `YYYY-MM-DD` (2026-05-22) |
| Numbers | Dot as decimal mark, no thousands separator (28.45; 51768). A comma is rejected, because "28,45" could be read as 2,845 |
| Empty | An empty cell means "not reported"; nothing is estimated |
| Spaces | Spaces at the start and end of every value are removed |
| Errors | Any error stops the run and nothing is written |
| Warnings | Listed in the log; the run continues |

## sales.csv → sheet "Sales Register", rows 5–304 (capacity 300)

| Column | Excel | Type | Required | Allowed values / limits | Meaning |
|---|---|---|---|---|---|
| `id` | A | whole number | yes | 1 to 1,000,000; unique | Row identifier |
| `report_date` | B | date | yes | | Date of the report that gave the sale |
| `vessel` | C | text | yes | | Ship name as reported |
| `segment` | D | choice | yes | Capesize, Post Panamax, Kamsarmax, Panamax, Ultramax, Supramax, Handysize, VLCC, Suezmax, Aframax, LR2, LR1, MR, Handy tanker, Chemical tanker, Panamax tanker, Container, Gas, Other | Ship type and size class |
| `dwt` | E | whole number | no (warning if empty) | 1,000 to 600,000 | Deadweight tonnes |
| `built` | F | whole number | yes | 1950 to 2035 | Year built (or due for delivery) |
| `shipyard` | G | text | no | | Shipyard |
| `yard_country` | H | text | no | Free text | Country of the shipyard |
| `price_musd` | I | number | no (warning if empty) | 0.01 to 1,000 | Exact reported price in $m. Empty when only an approximate price ("low $14m", "xs $20m") was reported; write that in `notes` |
| `buyer` | J | text | no | | Buyer as reported |
| `seller` | K | text | no | | Seller as reported |
| `features` | L | text | no | | Special features as reported: scrubber, DPP, "time charter attached" |
| `en_bloc` | N | choice | no | Y, N, Unknown | Y if sold as part of a package |
| `sale_type` | O | choice | yes | Secondhand, Resale, Auction | Type of sale |
| `source_file` | P | text | yes | | Source report file name |
| `source_url` | Q | text | no | | Link to the source |
| `notes` | R | text | no | | Everything else reported: survey dates, package details, approximate prices, other brokers' figures |
| `reviewed_decision` | Z | choice | no | Yes, No, Target | A person's decision; overrides the automatic screen when the case says so |
| `review_reason` | AA | text | no (warning if a decision has no reason) | | Rules failed, or the judgement made |
| `next_survey` | AE | date | no | | Next special survey or drydock, first of the month |

Checks across rows: `id` unique (error); the same vessel on the same report date twice (warning).

Columns M, S–Y, AB–AD, AF–AJ of the sheet are formulas and are never written.

## indicative_prices.csv → sheet "Indicative Prices", rows 5–1000 (capacity 996)

| Column | Excel | Type | Required | Allowed values / limits | Meaning |
|---|---|---|---|---|---|
| `report_date` | A | date | yes | | Report date |
| `broker` | B | text | yes | Must match Parameters exactly to be used as a benchmark (e.g. "Advanced Shipping") | Broker publishing the value |
| `segment` | C | text | yes | As the broker writes it (MR, MR2 …) | Segment label |
| `size` | D | text | no | | Reference size, e.g. 51k |
| `age` | E | text | yes | Must match the Parameters age labels exactly to be used ("5 years", "10 years", "15 years"); other labels such as "Resale" are stored | Age label |
| `value_musd` | F | number | yes | 0.01 to 1,000 | Published value, $m |
| `compared_with` | G | text | no | | Earlier period the broker compares with |
| `earlier_value_musd` | H | number | no | 0.01 to 1,000 | Earlier value, $m |
| `basis` | I | text | no | | Basis of the value, e.g. monthly average |
| `source_file` | J | text | yes | | Source report file name |

Check across rows: the same date, broker, segment and age twice (warning: the Benchmarks sheet would show "Duplicate").

## Case file (JSON) → sheet "Inputs", column C

| Field | Cell | Type | Required | Allowed values / limits | Meaning |
|---|---|---|---|---|---|
| `case_id` | C5 | text | yes | | Case reference; also used in the output file name |
| `purpose` | C6 | choice | yes | Sale price guide, Purchase bid, Loan collateral, Portfolio value, Back-test | Why the value is needed |
| `target_name` | C7 | text | yes | | Ship to value; as in `vessel` if the ship is in the data (it is then excluded from its own comparables) |
| `segment` | C8 | choice | yes | Same list as sales.csv; must have a row on Parameters | Segment |
| `dwt` | C9 | whole number | yes | 1,000 to 600,000 | Deadweight tonnes |
| `year_built` | C10 | whole number | yes | 1950 to 2035 | Year built |
| `shipyard` | C11 | text | no | | Shipyard and country |
| `valuation_date` | C12 | date | yes | | Date the value is for |
| `known_price_musd` | C13 | number | no | 0.01 to 1,000 | A known or offered price to test against |
| `use_reviewed_decisions` | C14 | choice | yes | Yes, No | Use `reviewed_decision` where filled |
| `prepared_by` | C15 | text | no | | Preparer |
| `date_prepared` | C16 | date | no | | Date prepared |

Example: `examples/case_target_ship_1.json`.

## Output

| File | Content |
|---|---|
| `M1_<case_id>_<YYYY-MM-DD_HHMMSS>.xlsx` | Copy of the blank template with the data and the case; Excel recalculates it on opening |
| Same name, `.log` | Version, files used, row counts, every error and warning |
