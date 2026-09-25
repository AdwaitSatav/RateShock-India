"""Turn a bank's maturity buckets into an average portfolio duration."""
import pandas as pd

from .pricing import bucket_duration

# Typical maturity (years) assumed for each bucket in the annual report table.
BUCKET_MATURITY = {
    "1 day": 0.003, "2-7 days": 0.013, "8-14 days": 0.03,
    "15-30 days": 0.06, "31 days-2 months": 0.125, "2-3 months": 0.21,
    "3-6 months": 0.375, "6 months-1 year": 0.75,
    "1-3 years": 2, "3-5 years": 4, "over 5 years": 10,
}


def average_durations(maturity_df, over5_maturity=10):
    """Weighted-average duration per bank. Returns a Series indexed by bank."""
    bm = dict(BUCKET_MATURITY, **{"over 5 years": over5_maturity})
    d = maturity_df.copy()
    unknown = set(d["bucket"]) - set(bm)
    if unknown:
        raise ValueError(f"Unknown bucket names: {sorted(unknown)}")
    d["duration"] = d["bucket"].map(bm).apply(bucket_duration)
    d["weighted"] = d["amount_crore"] * d["duration"]
    g = d.groupby("bank")
    return g["weighted"].sum() / g["amount_crore"].sum()
