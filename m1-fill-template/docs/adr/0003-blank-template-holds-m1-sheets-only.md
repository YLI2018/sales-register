# 0003: The blank template holds the 8 M1 sheets only

Date: 2026-11-05. Status: accepted.

## Context
The full template (built from the development workbook M1 v10) also contains market data sheets (Market Data, Newbuilding, Demolition, Freight, Bunker, Commodities, Stocks, Segments, Summary, Read Me, Guide). No M1 formula refers to them; they hold broker data.

## Decision
`scripts/make_blank_template.py` keeps Start Here, Inputs, Outputs, Parameters, Sales Register, Indicative Prices, Benchmarks and Age Curve, clears every input column of the data contract, the case and the case log, and keeps all formulas, named cells, validation lists and charts.

## Consequences
- The blank template contains no broker data and can sit in Git (ADR 0001).
- Market data for later models (M2–M5) gets its own template and its own fill project when those models are built.
