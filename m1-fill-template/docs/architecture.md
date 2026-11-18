# Architecture

## Where this project sits

```mermaid
flowchart LR
    A[m1-report-download<br/>broker PDFs] --> B[m1-extract<br/>reads PDFs]
    B -->|sales.csv<br/>indicative_prices.csv| C[m1-fill-template<br/>this project]
    K[case JSON] --> C
    T[blank template] --> C
    C -->|filled workbook + log| X[Excel<br/>audit view of one case]
    B -->|same files| D[m1-calculate<br/>values one ship or a list]
```

The projects share no code. They connect through two kinds of file whose format is written down: the **data contract** (`docs/data_dictionary.md`) and the **blank template**. A project can be rebuilt or replaced as long as it keeps to them.

## Inside this project

```mermaid
flowchart TD
    S[sales.csv] --> R[read_data.read_sales]
    P[indicative_prices.csv] --> R2[read_data.read_prices]
    C[case JSON] --> R3[read_data.read_case]
    R & R2 & R3 --> V{errors?}
    V -->|yes| E[print errors, write nothing, exit 1]
    V -->|no| W[write_workbook.fill]
    T[blank template] --> W
    W --> CH[charts.restore_charts]
    CH --> O[M1_case_date.xlsx + .log]
```

| Module | Responsibility |
|---|---|
| `contract.py` | The data contract as code: every field's column name, Excel column, type, required flag, allowed values, limits, meaning. Nothing else in the code hard-codes a column |
| `read_data.py` | Turns text into typed values (`parse_value`), checks each row (`read_table`), then whole-table checks: unique id, repeated sale, duplicate broker value, review reason |
| `write_workbook.py` | Confirms the template is blank, writes values into input columns only, writes the case, sets full recalculation, saves a new file |
| `charts.py` | Puts the template's original chart definitions back into the saved file |
| `__main__.py` | Command line, log file, exit codes |

## Design choices

| Choice | Reason | Record |
|---|---|---|
| Data stays outside Git | Broker licences and confidentiality; data changes weekly, code is reviewed | ADR 0001 |
| Write input columns only; never overwrite | Formulas are the model; a filled workbook must be reproducible from template + data | ADR 0002 |
| Blank template holds the 8 M1 sheets only | M1 formulas use no other sheet; other market data belongs to later models | ADR 0003 |
| Restore charts from the template | The Excel library rewrites charts with default formatting | ADR 0004 |
| CSV + JSON as the interface | Readable by any tool and by people; easy to check line by line | ADR 0005 |
| Errors stop the whole run | A partly filled workbook could be mistaken for a complete one | ADR 0002 |

## Limits

- openpyxl cannot calculate formulas. The filled workbook carries no calculated values until Excel opens it; the tests check the data with a separate reference calculation (`tests/reference_calc.py`).
- Capacity: 300 sales and 996 broker values (the template's ranges). The checks stop the run before anything is cut off.
- Only the M1 input columns are covered. A change to the template's columns needs the same change in `contract.py` and `docs/data_dictionary.md` (a test checks they agree).
