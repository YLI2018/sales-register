"""Reference calculation used only by the tests: the template's valuation logic in plain Python.

It reads a filled workbook's input data and Parameters (not Excel's calculated values, which openpyxl cannot
compute) and returns the market value. If Fill template wrote the data correctly, validation case 1 gives the
values in docs/model_specification.md: 30 comparables, $29.52m. The full calculation belongs to the separate
m1-calculate project; this is a test oracle, kept small on purpose.
"""
import math
import statistics as st

import openpyxl


def value_case(path):
    wb = openpyxl.load_workbook(path)
    inp, par, sr, ip = wb["Inputs"], wb["Parameters"], wb["Sales Register"], wb["Indicative Prices"]
    target, seg, built, valdate, use_rev = (inp["C7"].value, inp["C8"].value, inp["C10"].value, inp["C12"].value,
                                            inp["C14"].value)
    prow = next(r for r in range(6, 21) if par[f"A{r}"].value == seg)
    g = lambda c: par[f"{c}{prow}"].value
    dmin, dmax, tol, amin, amax, prov, lab = g("C"), g("D"), g("E"), g("F"), g("G"), g("H"), g("I")
    labels, ages = [g("J"), g("K"), g("L")], [g("M"), g("N"), g("O")]
    ckw = [par["C25"].value.lower(), par["C26"].value.lower()]; rkw = [par["C27"].value.lower(), par["C28"].value.lower()]

    prices = [(ip[f"A{r}"].value, ip[f"B{r}"].value, ip[f"C{r}"].value, ip[f"E{r}"].value, ip[f"F{r}"].value)
              for r in range(5, 1001) if ip[f"A{r}"].value]
    bm = {}
    for d in sorted({p[0] for p in prices if p[1] == prov and p[2] == lab}):
        vals = [[p[4] for p in prices if p[0] == d and p[1] == prov and p[2] == lab and p[3] == L] for L in labels]
        if all(len(v) == 1 for v in vals):
            bm[d] = [v[0] for v in vals]
    ok = sorted(bm)

    def near(x):
        b = [d for d in ok if d <= x]; a = [d for d in ok if d >= x]
        if not b or not a:
            return (b or a)[-1 if b else 0]
        return b[-1] if (x - b[-1]) <= (a[0] - x) else a[0]

    vd, seen, comps = near(valdate), set(), []
    for r in range(5, 305):
        name = sr[f"C{r}"].value
        if not name or sr[f"D{r}"].value != seg:
            continue
        first_time = name not in seen
        seen.add(name)
        if name == target:
            continue
        rd, dwt, yb, price, z = sr[f"B{r}"].value, sr[f"E{r}"].value, sr[f"F{r}"].value, sr[f"I{r}"].value, sr[f"Z{r}"].value
        age = rd.year - yb
        notes = f"{sr[f'L{r}'].value or ''} {sr[f'R{r}'].value or ''}".lower()
        fails = (not isinstance(dwt, (int, float)) or dwt < dmin * (1 - tol) or dwt > dmax * (1 + tol)
                 or sr[f"O{r}"].value == "Resale" or age < amin or not isinstance(price, (int, float))
                 or any(k in notes for k in ckw) or age > amax or not first_time)
        auto = "No" if fails else ("Review" if sr[f"N{r}"].value == "Y" or any(k in notes for k in rkw) else "Yes")
        used = z if (use_rev == "Yes" and z and z != "Target") else auto
        if used != "Yes":
            continue
        k = 0 if age < (ages[0] + ages[1]) / 2 else (1 if age < (ages[1] + ages[2]) / 2 else 2)
        ab = near(rd)
        comps.append((age, price * bm[vd][k] / bm[ab][k]))
    xs, ys = [c[0] for c in comps], [math.log(c[1]) for c in comps]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = math.exp(my - b * mx)
    sd = st.stdev([c[1] - a * math.exp(b * c[0]) for c in comps])
    value = a * math.exp(b * (valdate.year - built))
    return {"n": len(comps), "a": a, "b": b, "value": value, "low": value - sd, "high": value + sd}
