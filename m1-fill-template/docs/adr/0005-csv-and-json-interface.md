# 0005: CSV files and a JSON case file as the interface

Date: 2026-11-05. Status: accepted.

## Context
m1-extract (producer) and m1-fill-template / m1-calculate (consumers) are separate projects. They need a format that any tool can write, a person can read, and a program can check line by line.

## Decision
Two CSV files (`sales.csv`, `indicative_prices.csv`) and one JSON file per case, with the rules in `docs/data_dictionary.md`: UTF-8, named columns, ISO dates, dot decimals, empty = not reported. Commas in numbers are rejected rather than guessed.

## Consequences
- The files can be opened in Excel or a text editor for checking.
- A database can replace the CSV files later without changing the contract's fields.
