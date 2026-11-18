"""The one M1 age-curve fit. It lives in the valuation repository (shipping-vessel-valuation), in
shipping_valuation/models/age_curve.py; m1-calculate calls it instead of keeping its own copy (docs/adr/0006-one-m1-fit.md).

Where it is found, in this order:
1. already importable (for example after `pip install -e` or with PYTHONPATH set);
2. SHIPPING_VALUATION_SRC: the `src` folder of shipping-vessel-valuation.
"""
import os
import sys

try:
    from shipping_valuation.models.age_curve import AgeCurve, fit_age_curve
except ImportError:
    _src = os.environ.get("SHIPPING_VALUATION_SRC")
    if not _src:
        raise ImportError("The M1 fit was not found. Set SHIPPING_VALUATION_SRC to the src folder of the "
                          "shipping-vessel-valuation repository (see README, Setup).") from None
    sys.path.insert(0, _src)
    from shipping_valuation.models.age_curve import AgeCurve, fit_age_curve

__all__ = ["AgeCurve", "fit_age_curve"]
