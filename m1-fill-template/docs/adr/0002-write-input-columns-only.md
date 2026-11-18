# 0002: Write input columns only; never overwrite; stop on any error

Date: 2026-11-05. Status: accepted.

## Context
The template's formulas are the model. A program that writes into a formula cell, edits the template itself or overwrites an earlier result would change the model or lose the audit trail without anyone noticing.

## Decision
- The blank template is opened and never saved; every run writes a new file named with the case and the time.
- Only the columns listed in `contract.py` are written; every other column is left as in the template.
- Before writing, the program checks the template is blank and that its input columns hold no formulas.
- Any data error stops the run before anything is written.

## Consequences
- A filled workbook is always template + data, and can be rebuilt.
- A data file with one bad line produces no workbook until it is fixed. This is intended: a partly filled workbook could be mistaken for a complete one.
