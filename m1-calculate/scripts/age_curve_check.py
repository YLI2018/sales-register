# M1 Age Curve in Python: reproduces Age Curve cells O5 to O20
# Reads M1_Market_Database_v11.xlsx (values saved by Excel) and prints Python beside Excel.
# Read-only: changes nothing in the workbook.
import os
import math
import numpy as np
import openpyxl

# ── Folder and file ─────────────────────────────────────
# The M1 folder: M1_FOLDER if set, else the folder of M1_PARAMETERS (scripts/local_settings.sh),
# else the Google Drive folder found under ~/Library/CloudStorage (no personal path in the code).
def _m1_folder():
    import glob
    if os.environ.get("M1_FOLDER"):
        return os.environ["M1_FOLDER"]
    if os.environ.get("M1_PARAMETERS"):
        return os.path.dirname(os.environ["M1_PARAMETERS"])
    hits = glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/My Drive/"
                                        "Shipping Finance Career/Modelling/02_Models/M1_Sales_Register"))
    if not hits:
        raise SystemExit("M1 folder not found: set M1_FOLDER to the folder that holds the workbook")
    return hits[0]


DIR = _m1_folder()
FILE = "M1_Market_Database_v11.xlsx"

os.chdir(DIR)                                    # enter the folder
wb = openpyxl.load_workbook(FILE, data_only=True)   # read values, not formulas
ws = wb["Age Curve"]

if ws["B6"].value is None:
    raise SystemExit("No values stored. Open the file in Excel, save, close, then run again.")

# ── Inputs ──────────────────────────────────────────────
in_Target_Age  = ws["B6"].value                  # Target Ship 1 age = 14
in_Known_Price = ws["B7"].value                  # known price = 28.45
in_Range_SD    = 1                               # range = ± 1 SD (as in O13, O14)
in_Near_Window = 1                               # ± 1 year (as in O15)

age, price = [], []                              # comparables list, rows 11-70
for r in range(11, 71):
    a, p = ws[f"B{r}"].value, ws[f"C{r}"].value  # B = age, C = adjusted price $m
    if isinstance(a, (int, float)) and isinstance(p, (int, float)):
        age.append(a); price.append(p)
age, price = np.array(age, float), np.array(price, float)
n = len(age)

# ── Fit: ln(adjusted price) = c + b × age, by OLS ───────
lnp    = np.log(price)
dx     = age - age.mean()                        # age gap from average age
dy     = lnp - lnp.mean()                        # ln price gap from average
calc_b = (dx * dy).sum() / (dx ** 2).sum()       # slope = covariance ÷ variance  (SLOPE)
calc_c = lnp.mean() - calc_b * age.mean()        # intercept                     (INTERCEPT)
calc_a = math.exp(calc_c)                        # value at age 0, $m
calc_r = math.exp(calc_b)                        # yearly factor ≈ 0.92

calc_R2 = 1 - ((lnp - (calc_c + calc_b * age)) ** 2).sum() / (dy ** 2).sum()   # RSQ

# ── Value, range and checks ─────────────────────────────
out_Value     = calc_a * calc_r ** in_Target_Age # a × r^age
out_Loss_Year = 1 - calc_r                       # value lost per year
out_SD        = (price - calc_a * calc_r ** age).std(ddof=1)   # STDEV of $m residuals
out_Low       = out_Value - in_Range_SD * out_SD
out_High      = out_Value + in_Range_SD * out_SD

near = np.abs(age - in_Target_Age) <= in_Near_Window
out_Near_Avg  = price[near].mean()
out_Near_N    = int(near.sum())

out_Gap_m   = in_Known_Price - out_Value
out_Gap_pct = in_Known_Price / out_Value - 1
out_Inside  = "Yes" if out_Low <= in_Known_Price <= out_High else "No"

# ── Print beside the Excel cells, to check they match ───
rows = [("a (value at age 0)", calc_a, "O5"), ("b (slope)", calc_b, "O6"),
        ("Value lost per year", out_Loss_Year, "O7"), ("R²", calc_R2, "O8"),
        ("Comparables used", n, "O9"), ("Market value $m", out_Value, "O11"),
        ("SD of residuals $m", out_SD, "O12"), ("Range low $m", out_Low, "O13"),
        ("Range high $m", out_High, "O14"), ("Near-age average $m", out_Near_Avg, "O15"),
        ("Near-age count", out_Near_N, "O16"), ("Known − fitted $m", out_Gap_m, "O18"),
        ("Known ÷ fitted − 1", out_Gap_pct, "O19"), ("Known inside range?", out_Inside, "O20")]

def f(v):
    return f"{v:12.4f}" if isinstance(v, (int, float)) else f"{str(v):>12}"

def same(py, xl):
    if isinstance(py, (int, float)) and isinstance(xl, (int, float)):
        return abs(py - xl) < 1e-9
    return str(py) == str(xl)

print(f"{'Result':24}{'Python':>12}{'Excel':>12}  Cell  Check")
all_ok = True
for name, py, cell in rows:
    xl = ws[cell].value
    ok = same(py, xl); all_ok &= ok
    print(f"{name:24}{f(py)}{f(xl)}  {cell:4}  {'OK' if ok else 'DIFF'}")
print("\nAll match Excel." if all_ok else "\nSome rows differ from Excel.")
