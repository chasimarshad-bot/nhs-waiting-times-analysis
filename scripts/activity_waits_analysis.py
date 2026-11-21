"""Summarize the association between trust activity and 12-hour waits."""
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "nhs.db"
QUERY = ROOT / "sql" / "05_activity_and_12_hour_waits.sql"
OUTPUT = ROOT / "images" / "activity_vs_12_hour_waits.png"


def main() -> int:
    if not DB.exists():
        print(f"No database found at {DB}. Run python scripts/load_data.py first.")
        return 1

    with sqlite3.connect(DB) as conn:
        tables = set(
            pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type = 'table'",
                conn,
            )["name"]
        )
        if "ae_monthly" not in tables:
            print("ae_monthly is missing. Run python scripts/load_data.py first.")
            return 1
        monthly = pd.read_sql_query(QUERY.read_text(encoding="utf-8"), conn)

    if monthly.empty:
        print("The analysis query returned no trust-month observations.")
        return 1

    trust_labels = (
        monthly.sort_values("month")
        .drop_duplicates("org_code", keep="last")
        [["org_code", "org_name", "parent_org"]]
    )
    trusts = (
        monthly.groupby("org_code", dropna=False)
        .agg(
            months_observed=("month", "nunique"),
            mean_monthly_attendances=("a_e_attendances", "mean"),
            mean_monthly_12hr_waits=("patients_waited_12hrs", "mean"),
            total_12hr_waits=("patients_waited_12hrs", "sum"),
            total_ae_admissions=("emergency_admissions_via_ae", "sum"),
        )
        .reset_index()
        .merge(trust_labels, on="org_code", how="left")
    )
    trusts["waits_12hrs_per_1000_ae_admissions"] = (
        1000 * trusts["total_12hr_waits"] / trusts["total_ae_admissions"].where(
            trusts["total_ae_admissions"] > 0
        )
    )

    correlations = trusts[
        ["mean_monthly_attendances", "mean_monthly_12hr_waits"]
    ].corr(method="pearson")
    correlation = correlations.iloc[0, 1]
    if pd.isna(correlation):
        print(
            f"Pearson correlation is undefined across {len(trusts)} trusts "
            "(insufficient observations or no variation)."
        )
    else:
        print(
            "Pearson correlation across trust-level monthly averages "
            f"({len(trusts)} trusts): r={correlation:.3f}"
        )
    print(
        "Each trust is averaged over its observed months. Correlation is "
        "descriptive and does not establish causation."
    )

    fig, (count_ax, rate_ax) = plt.subplots(
        1, 2, figsize=(13, 5.5), constrained_layout=True
    )
    count_ax.scatter(
        trusts["mean_monthly_attendances"],
        trusts["mean_monthly_12hr_waits"],
        alpha=0.75,
        color="#2c7bb6",
    )
    count_ax.set_title("Activity and average monthly 12-hour waits")
    count_ax.set_xlabel("Mean monthly A&E attendances per trust")
    count_ax.set_ylabel("Mean monthly patients waiting 12+ hours")
    if not pd.isna(correlation):
        count_ax.text(
            0.04,
            0.96,
            f"Pearson r = {correlation:.2f}",
            transform=count_ax.transAxes,
            va="top",
        )
    count_ax.grid(alpha=0.25)

    rate_ax.scatter(
        trusts["mean_monthly_attendances"],
        trusts["waits_12hrs_per_1000_ae_admissions"],
        alpha=0.75,
        color="#b2182b",
    )
    rate_ax.set_title("Activity and normalized 12-hour wait rate")
    rate_ax.set_xlabel("Mean monthly A&E attendances per trust")
    rate_ax.set_ylabel("12-hour waits per 1,000 A&E admissions")
    rate_ax.grid(alpha=0.25)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved chart to {OUTPUT}")
    print("\nTrust-level summary, highest mean monthly 12-hour waits first:")
    print(
        trusts.sort_values("mean_monthly_12hr_waits", ascending=False)
        .head(10)
        .to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
