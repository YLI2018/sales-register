# Contributing

1. **Branch** from `main`: `git switch -c short-description`.
2. **Change** code and, in the same branch, the documents it affects (runbook, data dictionary, a new ADR for a design decision).
3. **Test**: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v` (the owner also runs the private real-report test, with `M1_SOURCES` and `M1_DATA` set). A change to a reader must keep the agreement test passing; add a test for the report that prompted the change.
4. **Commit** in small steps, present tense. **Review** by pull request; the project owner approves changes to the data contract or the typing conventions.
5. **Release**: update CHANGELOG.md and the version in `src/m1_extract/__init__.py`; tag `vX.Y.Z`.

Rules: never commit reports, data, check files or local settings; nothing is added to the data without a person's decision; no company or personal names in the repository.
