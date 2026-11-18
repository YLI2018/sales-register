# M1 Age Curve chart in Python: same fit as the Excel Age Curve sheet
# Reads M1_Market_Database_v11.xlsx (read-only) and draws:
#   dots = the comparables (43 in v11) (adjusted price vs age), line = fitted curve a × e^(b × age),
#   band = fitted ± 1 SD, Target Ship 1 = fitted value and known price at age 14.
import os
import math
import numpy as np
import openpyxl
import matplotlib.pyplot as plt

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

os.chdir(DIR)
ws = openpyxl.load_workbook(FILE, data_only=True)["Age Curve"]

# ── Inputs ──────────────────────────────────────────────
in_Target_Name = ws["B5"].value or "Target Ship 1"
in_Target_Age  = ws["B6"].value                  # 14
in_Known_Price = ws["B7"].value                  # 28.45
in_Range_SD    = 1

age, price = [], []
for r in range(11, 71):
    a, p = ws[f"B{r}"].value, ws[f"C{r}"].value  # B = age, C = adjusted price $m
    if isinstance(a, (int, float)) and isinstance(p, (int, float)):
        age.append(a); price.append(p)
age, price = np.array(age, float), np.array(price, float)

# ── Fit: ln(price) = c + b × age ────────────────────────
lnp = np.log(price)
calc_b = ((age - age.mean()) * (lnp - lnp.mean())).sum() / ((age - age.mean()) ** 2).sum()
calc_a = math.exp(lnp.mean() - calc_b * age.mean())
calc_R2 = np.corrcoef(age, lnp)[0, 1] ** 2
out_SD = (price - calc_a * np.exp(calc_b * age)).std(ddof=1)
out_Value = calc_a * math.exp(calc_b * in_Target_Age)

# ── Chart ───────────────────────────────────────────────
INK, MUTED, GRID = "#1f2328", "#6b7280", "#e5e7eb"
DOT, LINE, BAND, CASE = "#2f6db5", "#1f2328", "#dbe7f5", "#c2410c"

x = np.linspace(0, max(age.max(), in_Target_Age) + 2, 200)
y = calc_a * np.exp(calc_b * x)

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.fill_between(x, y - in_Range_SD * out_SD, y + in_Range_SD * out_SD,
                color=BAND, lw=0, label=f"Range: fitted ± {in_Range_SD} SD (${out_SD:.2f}m)")
ax.plot(x, y, color=LINE, lw=2,
        label=f"Fitted curve: {calc_a:.2f} × e^({calc_b:.4f} × age)")
ax.scatter(age, price, s=36, color=DOT, edgecolor="white", linewidth=1.2, zorder=3,
           label=f"Comparable sales, adjusted to valuation date (n = {len(age)})")
ax.scatter([in_Target_Age], [out_Value], s=90, marker="D", color=CASE,
           edgecolor="white", linewidth=1.5, zorder=4,
           label=f"{in_Target_Name}: fitted value ${out_Value:.2f}m")
if isinstance(in_Known_Price, (int, float)):
    ax.scatter([in_Target_Age], [in_Known_Price], s=90, marker="o", facecolor="white",
               edgecolor=CASE, linewidth=2, zorder=4,
               label=f"{in_Target_Name}: known price ${in_Known_Price:.2f}m")

ax.annotate(f"{in_Target_Name}\n${out_Value:.2f}m at age {in_Target_Age}",
            xy=(in_Target_Age, out_Value), xytext=(in_Target_Age + 1.2, out_Value + 9),
            color=INK, fontsize=9, arrowprops=dict(arrowstyle="-", color=MUTED, lw=1))

ax.set_title(f"M1 age curve: value falls {1 - math.exp(calc_b):.1%} per year  (R² = {calc_R2:.3f})",
             loc="left", fontsize=12, color=INK)
ax.set_xlabel("Age at sale (years)", color=MUTED)
ax.set_ylabel("Adjusted price ($m)", color=MUTED)
ax.set_xlim(0, x.max()); ax.set_ylim(0, None)
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(GRID)
ax.tick_params(colors=MUTED)
ax.legend(frameon=False, fontsize=8.5, loc="upper right")
fig.tight_layout()

OUT = os.environ.get("AGE_CURVE_PNG")            # optional: save instead of showing
if OUT:
    fig.savefig(OUT, dpi=150)
else:
    plt.show()
