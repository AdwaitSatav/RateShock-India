"""How often have rate rises of a given size actually happened?"""
import pandas as pd


def load_yields(path):
    y = pd.read_csv(path)
    y.columns = ["date", "yield_10y"]
    y["date"] = pd.to_datetime(y["date"])
    y["yield_10y"] = pd.to_numeric(y["yield_10y"], errors="coerce")
    return y.dropna().sort_values("date").reset_index(drop=True)


def rises(yields, months=12):
    """Change in yield (% points) versus `months` earlier."""
    return yields["yield_10y"].diff(months).dropna()


def likelihood(yields, breakevens, months=12):
    """Share of past windows where the rise reached each breakeven."""
    r = rises(yields, months)
    out = breakevens[["bank", "breakeven_svb_pct"]].copy()
    out["pct_of_periods_reached"] = out["breakeven_svb_pct"].apply(
        lambda be: round((r >= be).mean() * 100, 1))
    out["worst_rise_on_record"] = round(r.max(), 2)
    return out
