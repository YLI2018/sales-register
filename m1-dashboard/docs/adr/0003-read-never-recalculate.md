# ADR 0003: Read Calculate's results, never recalculate

**Status:** accepted (2026-11-06)

**Context.** Two programs computing the same values can drift apart.

**Decision.** The dashboard only reads Calculate's output files. The only values it derives are for display (axis scales, the curve drawn from a and b).

**Consequences.** The dashboard always agrees with Calculate; a change of method happens in one place (m1-calculate).
