# ADR 0001: One self-contained HTML file

**Status:** accepted (2026-11-06)

**Context.** The dashboard is shown in interviews and sent to people who may not have Python, Excel add-ins or internet access.

**Decision.** Write one HTML file with all styles, charts (inline SVG) and script inside it; four pages switched by tabs.

**Consequences.** Opens in any browser and can be emailed; no server. Each run writes a new file, so earlier dashboards are kept.
