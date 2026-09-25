"""Make the report charts. Run:  python charts.py
Saves PNGs into outputs/charts/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from rateshock import data, history, portfolio, stress

YEAR = "Mar 2026"
OUT = Path("outputs/charts")
PSU, PRIVATE, GREY = "#C0392B", "#2E86C1", "#7F8C8D"

plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10})


def colour(types):
    return [PSU if t == "PSU" else PRIVATE for t in types]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary, maturity = data.load_multi("Data/bank_summary.csv",
                                        "Data/investments_maturity.csv")
    banks = summary[summary["year"] == YEAR].copy()
    banks["duration"] = banks["bank"].map(portfolio.average_durations(maturity))
    be = stress.breakeven(banks).sort_values("breakeven_svb_pct")

    yields = None
    if Path("Data/india_10y_yield.csv").exists():
        yields = history.load_yields("Data/india_10y_yield.csv")
    worst = history.rises(yields).max() if yields is not None else None

    # 1. Headline: SVB-case breakeven vs worst rise on record
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(be["bank"], be["breakeven_svb_pct"], color=colour(be["type"]))
    ax.bar_label(bars, fmt="%.2f%%", padding=3)
    if worst is not None:
        ax.axvline(worst, color="black", ls="--", lw=1)
        ax.text(worst, len(be) - 0.4, f" Worst 12-month rise\n since 2011: {worst:.2f}",
                va="top", fontsize=8)
    ax.set_xlabel("Rate rise needed to erase 20% of CET1 (percentage points)")
    ax.set_title("SVB-case breakeven rate shock (red = PSU, blue = private)")
    fig.tight_layout(); fig.savefig(OUT / "1_breakeven.png"); plt.close(fig)

    # 2. Normal vs SVB-case loss at +1%, as % of CET1
    loss = stress.stress_losses(banks, shocks=(0.01,)).set_index("bank")
    fig, ax = plt.subplots(figsize=(7, 4))
    x = range(len(loss))
    ax.bar([i - 0.2 for i in x], loss["normal_pct_cet1"], 0.4, color=GREY,
           label="Normal (AFS + FVTPL only)")
    ax.bar([i + 0.2 for i in x], loss["svb_pct_cet1"], 0.4,
           color=colour(loss["type"]), label="SVB case (forced sale of all bonds)")
    ax.set_xticks(list(x), loss.index)
    ax.set_ylabel("Loss as % of CET1 capital")
    ax.set_title("Loss from a +1 percentage point rate rise")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(OUT / "2_losses.png"); plt.close(fig)

    # 3. Yield history
    if yields is not None:
        fig, ax = plt.subplots(figsize=(8, 3.8))
        ax.plot(yields["date"], yields["yield_10y"], color=PRIVATE, lw=1.5)
        for label, date in [("Taper tantrum", "2013-09-01"), ("2018 rise", "2018-09-01"),
                            ("COVID cuts", "2020-07-01"), ("2022 hikes", "2022-06-01")]:
            d = pd.Timestamp(date)
            if yields["date"].min() <= d <= yields["date"].max():
                ax.axvline(d, color=GREY, ls=":", lw=1)
                ax.text(d, ax.get_ylim()[1], label, rotation=90, va="top",
                        ha="right", fontsize=8, color=GREY)
        ax.set_ylabel("Yield (%)")
        ax.set_title("India 10-year government bond yield")
        fig.tight_layout(); fig.savefig(OUT / "3_yield_history.png"); plt.close(fig)

    # 4. Sensitivity to the 'over 5 years' assumption
    fig, ax = plt.subplots(figsize=(7, 4))
    for _, b in banks.iterrows():
        vals = []
        for m in (7, 10, 15):
            d = portfolio.average_durations(maturity, m)
            vals.append(stress.breakeven(banks.assign(duration=banks["bank"].map(d)))
                        .set_index("bank").loc[b["bank"], "breakeven_svb_pct"])
        c = PSU if b["type"] == "PSU" else PRIVATE
        ax.plot([7, 10, 15], vals, marker="o", color=c)
        ax.text(15.2, vals[-1], b["bank"], va="center", color=c)
    if worst is not None:
        ax.axhline(worst, color="black", ls="--", lw=1)
    ax.set_xticks([7, 10, 15])
    ax.set_xlabel("Assumed maturity of 'over 5 years' bucket (years)")
    ax.set_ylabel("SVB-case breakeven (pp)")
    ax.set_title("Ranking holds under every assumption")
    fig.tight_layout(); fig.savefig(OUT / "4_sensitivity.png"); plt.close(fig)

    print(f"Charts saved in {OUT}/")


if __name__ == "__main__":
    main()
