"""Create reproducible monthly and seasonal A&E descriptive summaries."""
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "nhs.db"
CLEAN = ROOT / "data" / "clean"
OUTPUT = ROOT / "images" / "manager_seasonal_waits.png"

ATTENDANCE_COLUMNS = [
    "a_e_attendances_type_1",
    "a_e_attendances_type_2",
    "a_e_attendances_other_a_e_department",
    "a_e_attendances_booked_appointments_type_1",
    "a_e_attendances_booked_appointments_type_2",
    "a_e_attendances_booked_appointments_other_department",
]
OVER_4_HOUR_COLUMNS = [
    "attendances_over_4hrs_type_1",
    "attendances_over_4hrs_type_2",
    "attendances_over_4hrs_other_department",
    "attendances_over_4hrs_booked_appointments_type_1",
    "attendances_over_4hrs_booked_appointments_type_2",
    "attendances_over_4hrs_booked_appointments_other_department",
]
ADMISSION_COLUMNS = [
    "emergency_admissions_via_a_e_type_1",
    "emergency_admissions_via_a_e_type_2",
    "emergency_admissions_via_a_e_other_a_e_department",
]
WAIT_4_12_COLUMN = "patients_who_have_waited_4_12_hs_from_dta_to_admission"
WAIT_12_PLUS_COLUMN = "patients_who_have_waited_12_hrs_from_dta_to_admission"
SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]
SEASON_BY_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
}


def row_sum(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    return frame[columns].sum(axis=1, min_count=1)


def sum_if_reported(values: pd.Series) -> float:
    return values.sum(min_count=1)


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
        data = pd.read_sql_query("SELECT * FROM ae_monthly", conn)

    required = {
        "month", "org_code", "org_name", "parent_org",
        *ATTENDANCE_COLUMNS, *OVER_4_HOUR_COLUMNS, *ADMISSION_COLUMNS,
        WAIT_4_12_COLUMN, WAIT_12_PLUS_COLUMN,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"ae_monthly is missing required columns: {', '.join(missing)}")
    if data.empty:
        print("ae_monthly has no rows to analyze.")
        return 1

    data["month"] = pd.to_datetime(data["month"], errors="coerce")
    invalid_month_rows = int(data["month"].isna().sum())
    data["a_e_attendances"] = row_sum(data, ATTENDANCE_COLUMNS)
    data["attendances_over_4hrs"] = row_sum(data, OVER_4_HOUR_COLUMNS)
    data["emergency_admissions_via_ae"] = row_sum(data, ADMISSION_COLUMNS)
    dated = data.loc[data["month"].notna()].copy()
    if dated.empty:
        print("ae_monthly has no valid month values.")
        return 1

    monthly = (
        data.loc[data["month"].notna()]
        .groupby("month", as_index=False)
        .agg(
            a_e_attendances=("a_e_attendances", sum_if_reported),
            attendances_over_4hrs=("attendances_over_4hrs", sum_if_reported),
            waits_4_to_12_hours=(WAIT_4_12_COLUMN, sum_if_reported),
            waits_12_hours_or_more=(WAIT_12_PLUS_COLUMN, sum_if_reported),
            emergency_admissions_via_ae=("emergency_admissions_via_ae", sum_if_reported),
        )
        .sort_values("month")
    )
    monthly["over_4_hour_attendance_percent"] = (
        100 * monthly["attendances_over_4hrs"]
        / monthly["a_e_attendances"].where(monthly["a_e_attendances"] > 0)
    )
    monthly["waits_12_plus_per_1000_ae_admissions"] = (
        1000 * monthly["waits_12_hours_or_more"]
        / monthly["emergency_admissions_via_ae"].where(
            monthly["emergency_admissions_via_ae"] > 0
        )
    )
    monthly["season"] = monthly["month"].dt.month.map(SEASON_BY_MONTH)
    seasonal_totals = (
        monthly.groupby("season", as_index=False)
        .agg(
            months_observed=("month", "nunique"),
            total_waits_12_hours_or_more=("waits_12_hours_or_more", sum_if_reported),
            mean_monthly_waits_12_hours_or_more=("waits_12_hours_or_more", "mean"),
            median_monthly_waits_12_hours_or_more=("waits_12_hours_or_more", "median"),
            total_emergency_admissions_via_ae=("emergency_admissions_via_ae", sum_if_reported),
            total_a_e_attendances=("a_e_attendances", sum_if_reported),
            total_attendances_over_4hrs=("attendances_over_4hrs", sum_if_reported),
        )
    )
    seasonal_totals["waits_12_plus_per_1000_ae_admissions"] = (
        1000 * seasonal_totals["total_waits_12_hours_or_more"]
        / seasonal_totals["total_emergency_admissions_via_ae"].where(
            seasonal_totals["total_emergency_admissions_via_ae"] > 0
        )
    )
    seasonal_totals["over_4_hour_attendance_percent"] = (
        100 * seasonal_totals["total_attendances_over_4hrs"]
        / seasonal_totals["total_a_e_attendances"].where(
            seasonal_totals["total_a_e_attendances"] > 0
        )
    )

    trust_data = dated.loc[dated["org_code"].notna()].copy()
    trust_labels = (
        trust_data.sort_values("month")
        .drop_duplicates("org_code", keep="last")
        [["org_code", "org_name", "parent_org"]]
    )
    trust_monthly = (
        trust_data.groupby(
            ["org_code", "month"],
            as_index=False,
            dropna=False,
        )
        .agg(
            a_e_attendances=("a_e_attendances", sum_if_reported),
            attendances_over_4hrs=("attendances_over_4hrs", sum_if_reported),
            waits_4_to_12_hours=(WAIT_4_12_COLUMN, sum_if_reported),
            waits_12_hours_or_more=(WAIT_12_PLUS_COLUMN, sum_if_reported),
            emergency_admissions_via_ae=("emergency_admissions_via_ae", sum_if_reported),
        )
        .merge(trust_labels, on="org_code", how="left")
    )
    if trust_monthly.empty:
        print("No dated rows with an organization code are available for trust EDA.")
        return 1

    trust_monthly["season"] = trust_monthly["month"].dt.month.map(SEASON_BY_MONTH)
    seasonal = (
        trust_monthly.groupby(
            ["org_code", "season"],
            as_index=False,
            dropna=False,
        )
        .agg(
            months_observed=("month", "nunique"),
            mean_monthly_attendances=("a_e_attendances", "mean"),
            median_monthly_attendances=("a_e_attendances", "median"),
            mean_monthly_over_4hr_attendances=("attendances_over_4hrs", "mean"),
            mean_monthly_waits_4_to_12_hours=("waits_4_to_12_hours", "mean"),
            median_monthly_waits_4_to_12_hours=("waits_4_to_12_hours", "median"),
            mean_monthly_waits_12_hours_or_more=("waits_12_hours_or_more", "mean"),
            median_monthly_waits_12_hours_or_more=("waits_12_hours_or_more", "median"),
            total_waits_12_hours_or_more=("waits_12_hours_or_more", sum_if_reported),
            total_emergency_admissions_via_ae=("emergency_admissions_via_ae", sum_if_reported),
        )
        .merge(trust_labels, on="org_code", how="left")
    )
    seasonal["waits_12_plus_per_1000_ae_admissions"] = (
        1000 * seasonal["total_waits_12_hours_or_more"]
        / seasonal["total_emergency_admissions_via_ae"].where(
            seasonal["total_emergency_admissions_via_ae"] > 0
        )
    )
    trust_summary = (
        trust_monthly.groupby(
            ["org_code"],
            as_index=False,
            dropna=False,
        )
        .agg(
            months_observed=("month", "nunique"),
            mean_monthly_attendances=("a_e_attendances", "mean"),
            mean_monthly_waits_12_hours_or_more=("waits_12_hours_or_more", "mean"),
            total_waits_12_hours_or_more=("waits_12_hours_or_more", sum_if_reported),
            total_emergency_admissions_via_ae=("emergency_admissions_via_ae", sum_if_reported),
        )
        .merge(trust_labels, on="org_code", how="left")
    )
    trust_summary["waits_12_plus_per_1000_ae_admissions"] = (
        1000 * trust_summary["total_waits_12_hours_or_more"]
        / trust_summary["total_emergency_admissions_via_ae"].where(
            trust_summary["total_emergency_admissions_via_ae"] > 0
        )
    )

    CLEAN.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(CLEAN / "monthly_eda_summary.csv", index=False)
    seasonal_totals.to_csv(CLEAN / "seasonal_eda_summary.csv", index=False)
    seasonal.to_csv(CLEAN / "trust_seasonal_eda.csv", index=False)
    trust_summary.to_csv(CLEAN / "trust_eda_summary.csv", index=False)

    top_trusts = trust_summary.nlargest(10, "total_waits_12_hours_or_more").copy()
    top_trusts["trust_label"] = (
        top_trusts["org_name"].fillna(top_trusts["org_code"]).astype(str)
        + " ("
        + top_trusts["org_code"].astype(str)
        + ")"
    )
    selected = seasonal.merge(
        top_trusts[["org_code", "trust_label"]],
        on="org_code",
        how="inner",
    )
    heatmap = selected.pivot_table(
        index="trust_label",
        columns="season",
        values="waits_12_plus_per_1000_ae_admissions",
        aggfunc="mean",
    ).reindex(columns=SEASON_ORDER)
    heatmap = heatmap.reindex(top_trusts["trust_label"])

    fig, (count_ax, rate_ax) = plt.subplots(
        1, 2, figsize=(15, max(6, len(top_trusts) * 0.48)),
        constrained_layout=True,
    )
    count_plot = top_trusts.sort_values("total_waits_12_hours_or_more")
    count_ax.barh(
        count_plot["trust_label"],
        count_plot["total_waits_12_hours_or_more"],
        color="#b2182b",
    )
    count_ax.set_title("Highest total 12+ hour DTA wait counts")
    count_ax.set_xlabel("Patients waiting 12+ hours")
    count_ax.grid(axis="x", alpha=0.25)

    image = rate_ax.imshow(heatmap.to_numpy(dtype=float), aspect="auto", cmap="YlOrRd")
    rate_ax.set_title("Seasonal rate among the highest-count trusts")
    rate_ax.set_xticks(range(len(SEASON_ORDER)), labels=SEASON_ORDER)
    rate_ax.set_yticks(range(len(heatmap.index)), labels=heatmap.index)
    rate_ax.tick_params(axis="x", labelrotation=20)
    rate_ax.set_xlabel("Meteorological season")
    rate_ax.set_ylabel("Trust")
    fig.colorbar(image, ax=rate_ax, label="Waits per 1,000 A&E admissions")
    fig.suptitle(
        "Manager view (June 2024-March 2026): prioritize local review; "
        "these measures do not identify causes"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(
        f"EDA covered {len(monthly)} months and {len(trust_summary)} organizations; "
        f"excluded {invalid_month_rows} rows with invalid month values."
    )
    print("Mean/median wait fields are monthly patient counts, not wait durations.")
    print(f"National seasonal summary: {CLEAN / 'seasonal_eda_summary.csv'}")
    print(f"Trust seasonal summary: {CLEAN / 'trust_seasonal_eda.csv'}")
    print(f"Manager chart: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
