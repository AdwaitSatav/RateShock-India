"""Stress losses and breakeven rate shocks.

Loss ~= amount x duration x rate rise.
- Normal case: only AFS + FVTPL bonds are marked to market.
- SVB case:    the bank is forced to sell everything, HTM included.
"""
import pandas as pd


def stress_losses(banks, shocks=(0.01, 0.02, 0.03)):
    """One row per bank per shock. `banks` needs a `duration` column."""
    rows = []
    for _, b in banks.iterrows():
        marked = b["govt_afs_crore"] + b["govt_fvtpl_crore"]
        for s in shocks:
            normal = marked * b["duration"] * s
            svb = b["govt_securities_india_crore"] * b["duration"] * s
            rows.append({
                "bank": b["bank"], "type": b["type"], "shock_pct": s * 100,
                "normal_loss_crore": round(normal),
                "normal_pct_cet1": round(normal / b["cet1_capital_crore"] * 100, 1),
                "svb_loss_crore": round(svb),
                "svb_pct_cet1": round(svb / b["cet1_capital_crore"] * 100, 1),
            })
    return pd.DataFrame(rows)


def breakeven(banks, threshold=0.20):
    """Rate rise (in % points) that wipes out `threshold` of CET1."""
    out = banks[["bank", "type", "duration"]].copy()
    cushion = threshold * banks["cet1_capital_crore"]
    marked = banks["govt_afs_crore"] + banks["govt_fvtpl_crore"]
    out["breakeven_normal_pct"] = (cushion / (marked * banks["duration"]) * 100).round(2)
    out["breakeven_svb_pct"] = (
        cushion / (banks["govt_securities_india_crore"] * banks["duration"]) * 100
    ).round(2)
    return out


def htm_hidden_loss(banks):
    """Unrealised loss already inside the HTM book (cost minus fair value)."""
    out = banks[["bank", "year"]].copy()
    out["htm_hidden_loss_crore"] = (
        banks["govt_htm_cost_crore"] - banks["govt_htm_fair_value_crore"]
    ).round()
    out["hidden_loss_pct_cet1"] = (
        out["htm_hidden_loss_crore"] / banks["cet1_capital_crore"] * 100
    ).round(2)
    return out
