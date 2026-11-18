# Contributing

1. **Branch** from `main`: `git switch -c short-description`.
2. **Change** the code and, in the same branch, the documents it affects (`docs/data_dictionary.md`, `docs/architecture.md`, a new ADR for a design decision).
3. **Test**: `PYTHONPATH=src python3 -m unittest discover -s tests -v`, with `SHIPPING_VALUATION_SRC`, `M1_DATA`, `M1_PARAMETERS` and `M1_EXCEL` set so the reconciliation with Excel runs. A change that breaks the reconciliation is not merged unless the Excel template changes in the same way (and the model owner approves).
4. **Commit** in small steps, present tense ("Add near-age window to the results").
5. **Review**: pull request; another analyst reviews; the model owner approves method changes.
6. **Release**: update `CHANGELOG.md` and the version in `pyproject.toml` and `src/m1_calc/__init__.py`; tag `vX.Y.Z`.

Rules: never commit data or results; keep one function per method step with a docstring naming its Excel equivalent; no company or personal names in the repository.
