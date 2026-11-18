# 0006: One M1 fit, shared with the valuation repository

Date: 2026-11-15. Status: accepted. Replaces 0005.

m1-calculate had its own copy of the M1 age-curve fit, and the valuation repository (shipping-vessel-valuation) had
another. Two copies of the same sum can drift apart: a change made in one would not reach the other, and the same ship
could get two different values without anyone noticing. A code review (15 Nov 2026) asked for one copy.

Decision: the fit (a, b, R squared, SD of residuals) is done only by `shipping_valuation.models.age_curve.fit_age_curve`.
`engine.fit_curve` calls it, through `shared_m1.py`, and keeps only the gap columns that the Age Curve sheet shows for
the hand calculation. The shared fit needs numpy, so numpy is now an add-on (0005 is replaced).

The shared fit refuses data it cannot fit (fewer than 3 sales, all sales the same age, a price not above 0). The
valuation then has no curve, the status is NOT VALID and the message says why, instead of the program stopping.

Check: all tests pass, including the reconciliation with the Excel workbook; the validation case is unchanged.
