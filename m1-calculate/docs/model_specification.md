# Model specification

The method this project implements is described in the M1 model specification (owner: model owner):

- `M1_Comparable_Sales_Model_Specification_v1.docx`, in the shared drive folder `Modelling/02_Models/M1_Sales_Register/`.

Validation case 1 (Target Ship 1, 22 May 2026), on data reported by that date (v11, 12 Nov 2026): 43 comparables, $29.67m, range $26.27m–$33.06m; Excel (M1_Market_Database_v11.xlsx) and this project agree to 9 decimal places (`scripts/age_curve_check.py`, and a private reconciliation test on the full database, kept off GitHub as it needs the private data). Since 0.3.0 the program itself uses nothing reported after the valuation date, so it gives these numbers on the full database. The original v10 validation (30 comparables, $29.52m) used four sales reported after the valuation date; the cutoff no longer allows that, and it is no longer a test.
