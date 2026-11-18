# Contributing

How the team changes this project.

## Workflow
1. **Branch** from `main`: `git switch -c short-description` (for example `add-lr2-segment`).
2. **Change** the code, and in the same branch the documents it affects: `docs/data_dictionary.md` for any contract change, `docs/runbook.md` for new messages, a new `docs/adr/NNNN-*.md` for a design decision.
3. **Test**: `PYTHONPATH=src:tests python3 -m unittest discover -s tests -v`. The owner also runs the private round-trip test (kept off GitHub; needs `M1_DATA` and `M1_REFERENCE`) before any release.
4. **Commit** in small steps with a message saying what and why, in the present tense ("Reject comma decimals in prices").
5. **Review**: open a pull request; another analyst reviews; the model owner approves changes to the contract, the template or the checks.
6. **Merge** to `main`; update `CHANGELOG.md` and the version in `pyproject.toml` and `src/m1_fill/__init__.py` when releasing.

## Rules
- Never commit data: no CSV, PDF, filled workbook or log (see `.gitignore` and ADR 0001).
- The contract lives in `contract.py`; never hard-code a column elsewhere.
- Every function has a docstring saying what it does, its inputs and its outputs.
- A change to the template's columns is a contract change: update `contract.py`, `docs/data_dictionary.md` and the blank template together, and bump the minor version.

## Versions
Semantic versioning: patch (0.1.1) for fixes, minor (0.2.0) for new fields or checks that stay compatible, major (1.0.0) when the contract changes in a way that breaks existing files.
