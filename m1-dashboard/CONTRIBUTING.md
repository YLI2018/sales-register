# Contributing

1. Make a branch for each change.
2. Keep to the Python standard library (see `docs/adr/0002-no-add-ons.md`).
3. Run all tests; they must pass.
4. Open the made dashboard and look at every page in a browser (light and dark) before committing: the tests check the content, not the look.
5. Update `CHANGELOG.md` and the version in `src/m1_dash/__init__.py` and `pyproject.toml`.
6. Record any design choice in `docs/adr/`.
7. Never commit data, results or dashboards (`.gitignore` keeps them out).
