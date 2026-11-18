# Sales register automation

Code that reads weekly broker sale-and-purchase reports and turns them into a checked sales register (the data behind the M1 vessel age curve).

| Folder | What it does | Status |
|---|---|---|
| `m1-extract` | Reads the broker reports, pulls out the ship sales, writes an Excel check file for a person to approve, then adds the approved rows to the database. | v0.1.4 |
| `m1-calculate` | Values a ship from the sales register with the M1 age curve (comparable sales, moved to the valuation date, log price on age). | v0.3.0 |
| `m1-fill-template` | Optional: puts one ship and its comparables into the M1 Excel template. | v0.1.1 |

The real broker reports cannot be published. `m1-extract/data/sample/` holds three **synthetic** reports (made-up ships, prices and dates, every page marked SYNTHETIC) with the rows the extractor should produce. All ship and company names in the tests and examples are made up; the validation case is called Target Ship 1. Tests that need the private data (the real reports, the reconciliation with the Excel workbook, the template round trip) are kept off GitHub.

`m1-calculate` does not keep its own copy of the M1 age curve: it calls the fit in the valuation repository (shipping-vessel-valuation), so there is one version of M1. Set `SHIPPING_VALUATION_SRC` to that repository's `src` folder.

The results dashboard for all the valuation models (M1, M1+, M2, cost approach) is in its own repository, **shipping-valuation-dashboard**.
