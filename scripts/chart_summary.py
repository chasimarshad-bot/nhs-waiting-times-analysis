"""Create the README chart summary from data/nhs.db."""
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "nhs.db"
OUTPUT = ROOT / "images" / "waiting_times_summary.png"


def main() -> int:
    if not DB.exists():
        print(f"No database found at {DB}. Run python scripts/load_data.py first.")
        return 1

    with sqlite3.connect(DB) as conn:
        if "ae_monthly" not in set(
            pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type = 'table'",
                conn,
            )["name"]
        ):
            print("ae_monthly is missing. Run python scripts/load_data.py first.")
            return 1

        latest_month = pd.read_sql(
            "SELECT MAX(month) AS month FROM ae_monthly "
            "WHERE month IS NOT NULL",
            conn,
        ).iloc[0, 0]
        if pd.isna(latest_month):
            print("ae_monthly has no parseable month values.")
            return 1

        longest_waits = pd.read_sql(
            """
            SELECT
                org_name,
                SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
                    AS patients_waited_12hrs
            FROM ae_monthly
            WHERE month = ?
            GROUP BY org_name
            ORDER BY patients_waited_12hrs DESC
            LIMIT 15
            """,
            conn,
            params=[latest_month],
        )

        monthly = pd.read_sql(
            """
            WITH monthly_totals AS (
                SELECT
                    month,
                    SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
                        AS patients_waited_12hrs
                FROM ae_monthly
                WHERE month IS NOT NULL
                GROUP BY month
            )
            SELECT
                month,
                patients_waited_12hrs,
                100.0 * (patients_waited_12hrs - LAG(patients_waited_12hrs)
                    OVER (ORDER BY month)) / NULLIF(
                        LAG(patients_waited_12hrs) OVER (ORDER BY month), 0
                    ) AS percentage_change
            FROM monthly_totals
            ORDER BY month
            """,
            conn,
        )

    monthly["month"] = pd.to_datetime(monthly["month"])
    latest_label = pd.to_datetime(latest_month).strftime("%B %Y")

    fig, (wait_ax, change_ax) = plt.subplots(
        2, 1, figsize=(12, 10), constrained_layout=True
    )

    longest_waits = longest_waits.sort_values("patients_waited_12hrs")
    wait_ax.barh(
        longest_waits["org_name"].fillna("Unknown"),
        longest_waits["patients_waited_12hrs"],
        color="#b2182b",
    )
    wait_ax.set_title(f"Longest 12-hour DTA waits - {latest_label}")
    wait_ax.set_xlabel("Patients who waited 12+ hours")
    wait_ax.grid(axis="x", alpha=0.25)

    colors = ["#2c7bb6" if pd.isna(v) or v >= 0 else "#d7191c"
              for v in monthly["percentage_change"]]
    change_ax.bar(
        monthly["month"],
        monthly["percentage_change"].fillna(0),
        width=20,
        color=colors,
    )
    change_ax.axhline(0, color="#333333", linewidth=1)
    change_ax.set_title("Month-over-month change in 12-hour DTA waits")
    change_ax.set_ylabel("Change (%)")
    change_ax.grid(axis="y", alpha=0.25)
    fig.autofmt_xdate()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved chart summary to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
