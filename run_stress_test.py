"""Run the full stress test and write results to Excel.

Examples:
    python run_stress_test.py                          # all banks, Mar 2026
    python run_stress_test.py --bank SBI
    python run_stress_test.py --year "Mar 2025"
    python run_stress_test.py --input templates/my_bank.csv
"""
import argparse
from pathlib import Path

import pandas as pd

from rateshock import data, history, portfolio, stress


def main():
    p = argparse.ArgumentParser(description="RateShock-India stress test")
    p.add_argument("--year", default="Mar 2026")
    p.add_argument("--bank", help="run one bank only")
    p.add_argument("--input", help="filled one-bank template CSV")
    p.add_argument("--threshold", type=float, default=0.20,
                   help="share of CET1 for the breakeven (default 0.20)")
    p.add_argument("--over5", type=float, default=10,
                   help="assumed maturity of the 'over 5 years' bucket")
    p.add_argument("--yields", default="Data/india_10y_yield.csv")
    p.add_argument("--out", default="outputs/stress_results.xlsx")
    a = p.parse_args()

    if a.input:
        summary, maturity = data.load_template(a.input)
    else:
        summary, maturity = data.load_multi("Data/bank_summary.csv",
                                            "Data/investments_maturity.csv")
        summary = summary[summary["year"] == a.year]
        if a.bank:
            summary = summary[summary["bank"] == a.bank]
    if summary.empty:
        raise SystemExit("No matching bank/year found in the data.")

    data.check(summary, maturity)
    dur = portfolio.average_durations(maturity, a.over5)
    banks = summary.copy()
    banks["duration"] = banks["bank"].map(dur)

    hidden = stress.htm_hidden_loss(banks)
    losses = stress.stress_losses(banks)
    be = stress.breakeven(banks, a.threshold)
    sens = pd.concat([
        stress.breakeven(banks.assign(duration=banks["bank"].map(
            portfolio.average_durations(maturity, m))), a.threshold)
        .assign(over5_assumed=m) for m in (7, 10, 15)
    ]).pivot(index="bank", columns="over5_assumed", values="breakeven_svb_pct")

    sheets = {"Breakeven": be, "Losses": losses, "Hidden HTM loss": hidden,
              "Sensitivity": sens.reset_index()}
    if Path(a.yields).exists():
        sheets["Historical likelihood"] = history.likelihood(
            history.load_yields(a.yields), be)

    pd.set_option("display.width", 140)
    for name, df in sheets.items():
        print(f"\n=== {name} ===\n{df.to_string(index=False)}")

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(a.out) as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
    print(f"\nSaved {a.out}")


if __name__ == "__main__":
    main()
