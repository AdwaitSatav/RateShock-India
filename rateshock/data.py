"""Load and check input data (multi-bank CSVs or a one-bank template)."""
import pandas as pd

TEMPLATE_BUCKETS = {
    "maturity_upto_1y_crore": "6 months-1 year",
    "maturity_1_3y_crore": "1-3 years",
    "maturity_3_5y_crore": "3-5 years",
    "maturity_over_5y_crore": "over 5 years",
}


def _clean(df):
    df.columns = df.columns.str.strip().str.replace("﻿", "")
    return df


def load_multi(summary_path, maturity_path):
    summary = _clean(pd.read_csv(summary_path))
    maturity = _clean(pd.read_csv(maturity_path))
    return summary, maturity


def load_template(path):
    """Read a filled one-bank template; return (summary, maturity) frames."""
    t = _clean(pd.read_csv(path))
    v = dict(zip(t["field"].str.strip(), t["value"]))
    missing = [k for k, x in v.items() if pd.isna(x) or str(x).strip() == ""]
    if missing:
        raise ValueError(f"Template has empty fields: {missing}")
    num = lambda k: float(str(v[k]).replace(",", ""))
    summary = pd.DataFrame([{
        "bank": v["bank_name"], "type": v["type"], "year": v["year"],
        "cet1_capital_crore": num("cet1_capital_crore"),
        "govt_htm_cost_crore": num("govt_htm_cost_crore"),
        "govt_htm_fair_value_crore": num("govt_htm_fair_value_crore"),
        "govt_afs_crore": num("govt_afs_crore"),
        "govt_fvtpl_crore": num("govt_fvtpl_crore"),
    }])
    s = summary.iloc[0]
    summary["govt_securities_india_crore"] = (
        s["govt_htm_cost_crore"] + s["govt_afs_crore"] + s["govt_fvtpl_crore"])
    # Short end is put in one bucket; "up to 1 year" is treated as ~0.75y maturity.
    maturity = pd.DataFrame([
        {"bank": v["bank_name"], "bucket": b, "amount_crore": num(k)}
        for k, b in TEMPLATE_BUCKETS.items()])
    return summary, maturity


def check(summary, maturity):
    """Print warnings for inputs that look inconsistent."""
    for _, b in summary.iterrows():
        parts = b["govt_htm_cost_crore"] + b["govt_afs_crore"] + b["govt_fvtpl_crore"]
        total = b["govt_securities_india_crore"]
        if abs(parts - total) / total > 0.02:
            print(f"WARNING {b['bank']} {b['year']}: HTM+AFS+FVTPL ({parts:,.0f}) "
                  f"differs from govt securities total ({total:,.0f}) by >2%")
    for bank in summary["bank"].unique():
        if bank not in set(maturity["bank"]):
            print(f"WARNING {bank}: no maturity data found")
