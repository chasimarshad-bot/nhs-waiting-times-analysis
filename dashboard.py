"""Interactive manager dashboard for aggregate NHS A&E waiting-time indicators."""
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "nhs.db"
CLEAN_CSV = ROOT / "data" / "clean" / "ae_monthly.csv"
SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]
SEASON_BY_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
}
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
WAIT_COLUMN = "patients_who_have_waited_12_hrs_from_dta_to_admission"


@st.cache_data(show_spinner="Loading validated monthly aggregates...")
def load_trust_months(data_path: str, modified_at: float) -> pd.DataFrame:
    del modified_at
    if Path(data_path).suffix.casefold() == ".db":
        with sqlite3.connect(data_path) as conn:
            data = pd.read_sql_query("SELECT * FROM ae_monthly", conn)
    else:
        data = pd.read_csv(data_path)

    required = {
        "month", "org_code", "org_name", "parent_org", WAIT_COLUMN,
        *ATTENDANCE_COLUMNS, *OVER_4_HOUR_COLUMNS, *ADMISSION_COLUMNS,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"ae_monthly is missing required columns: {', '.join(missing)}")

    data["month"] = pd.to_datetime(data["month"], errors="coerce")
    for column in [
        *ATTENDANCE_COLUMNS,
        *OVER_4_HOUR_COLUMNS,
        *ADMISSION_COLUMNS,
        WAIT_COLUMN,
    ]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.loc[data["month"].notna() & data["org_code"].notna()].copy()
    data["attendances"] = data[ATTENDANCE_COLUMNS].sum(axis=1, min_count=1)
    data["attendances_over_4hrs"] = data[OVER_4_HOUR_COLUMNS].sum(
        axis=1, min_count=1
    )
    data["emergency_admissions_via_ae"] = data[ADMISSION_COLUMNS].sum(
        axis=1, min_count=1
    )

    labels = (
        data.sort_values("month")
        .drop_duplicates("org_code", keep="last")
        [["org_code", "org_name", "parent_org"]]
    )
    trust_months = (
        data.groupby(["org_code", "month"], as_index=False)
        .agg(
            attendances=("attendances", "sum"),
            attendances_over_4hrs=("attendances_over_4hrs", "sum"),
            emergency_admissions_via_ae=("emergency_admissions_via_ae", "sum"),
            waits_12_plus=(WAIT_COLUMN, "sum"),
        )
        .merge(labels, on="org_code", how="left")
    )
    trust_months["season"] = trust_months["month"].dt.month.map(SEASON_BY_MONTH)
    trust_months["over_4_hour_percent"] = (
        100
        * trust_months["attendances_over_4hrs"]
        / trust_months["attendances"].where(trust_months["attendances"] > 0)
    )
    trust_months["waits_per_1000_admissions"] = (
        1000
        * trust_months["waits_12_plus"]
        / trust_months["emergency_admissions_via_ae"].where(
            trust_months["emergency_admissions_via_ae"] > 0
        )
    )
    return trust_months


def summarize_trusts(data: pd.DataFrame) -> pd.DataFrame:
    trusts = (
        data.groupby(["org_code", "org_name", "parent_org"], as_index=False)
        .agg(
            months_observed=("month", "nunique"),
            mean_monthly_attendances=("attendances", "mean"),
            mean_monthly_wait_counts=("waits_12_plus", "mean"),
            total_wait_counts=("waits_12_plus", "sum"),
            total_admissions=("emergency_admissions_via_ae", "sum"),
        )
    )
    trusts["waits_per_1000_admissions"] = (
        1000
        * trusts["total_wait_counts"]
        / trusts["total_admissions"].where(trusts["total_admissions"] > 0)
    )
    return trusts


st.set_page_config(
    page_title="NHS A&E long-wait signals",
    layout="wide",
)

st.title("NHS A&E long-wait signals")
st.markdown(
    "**Business question:** How do 12+ hour waits from decision to admit (DTA) "
    "vary by trust and season, and how do admission-normalized counts relate "
    "to A&E activity?"
)
st.markdown(
    "**Purpose:** Help hospital managers identify where and when to investigate "
    "operational pressure using trust-level aggregate signals."
)
st.warning(
    "These are threshold counts and counts per 1,000 A&E emergency admissions, "
    "not actual wait durations. They do not provide mean/median minutes, identify "
    "causes, or establish which intervention will work."
)

DATA_SOURCE = DB if DB.is_file() else CLEAN_CSV
if not DATA_SOURCE.is_file():
    st.error(
        "The cleaned data is missing. Run `python scripts/load_data.py` with the "
        "monthly CSVs in `data/raw/`, or restore `data/clean/ae_monthly.csv`."
    )
    st.stop()

data = load_trust_months(str(DATA_SOURCE), DATA_SOURCE.stat().st_mtime)
if data.empty:
    st.error("The ae_monthly table has no valid trust-month records.")
    st.stop()

min_month = data["month"].min().date()
max_month = data["month"].max().date()
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Reporting period",
    value=(min_month, max_month),
    min_value=min_month,
    max_value=max_month,
)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = (
        date_range[0] if isinstance(date_range, (tuple, list)) else date_range
    )

filtered = data.loc[
    data["month"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
].copy()
selected_seasons = st.sidebar.multiselect(
    "Meteorological season",
    options=SEASON_ORDER,
    default=SEASON_ORDER,
)
if selected_seasons:
    filtered = filtered.loc[filtered["season"].isin(selected_seasons)]

region_options = sorted(filtered["parent_org"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect(
    "Parent organization / region",
    options=region_options,
    default=region_options,
)
if selected_regions:
    filtered = filtered.loc[filtered["parent_org"].isin(selected_regions)]

trust_options = (
    filtered[["org_code", "org_name"]]
    .drop_duplicates("org_code")
    .sort_values("org_name")
)
trust_labels = {
    row.org_code: f"{row.org_name} [{row.org_code}]"
    for row in trust_options.itertuples(index=False)
}
trust_choices = list(trust_labels.values())
selected_trust_labels = st.sidebar.multiselect(
    "Trust (leave blank for all)",
    options=trust_choices,
    default=[],
)
if selected_trust_labels:
    selected_codes = [
        code for code, label in trust_labels.items()
        if label in selected_trust_labels
    ]
    filtered = filtered.loc[filtered["org_code"].isin(selected_codes)]

rank_by = st.sidebar.selectbox(
    "Rank trusts by",
    ["12+ hour DTA wait counts", "Counts per 1,000 A&E emergency admissions"],
)

if filtered.empty:
    st.info("No records match these filters. Broaden the date, season, or region selection.")
    st.stop()

trust_summary = summarize_trusts(filtered)
total_waits = filtered["waits_12_plus"].sum()
total_admissions = filtered["emergency_admissions_via_ae"].sum()
waits_per_1000 = (
    1000 * total_waits / total_admissions if total_admissions > 0 else float("nan")
)
total_attendances = filtered["attendances"].sum()
over_4_percent = (
    100 * filtered["attendances_over_4hrs"].sum() / total_attendances
    if total_attendances > 0
    else float("nan")
)

metric_columns = st.columns(4)
metric_columns[0].metric("12+ hour DTA wait counts", f"{total_waits:,.0f}")
metric_columns[1].metric(
    "Counts per 1,000 A&E admissions",
    f"{waits_per_1000:,.1f}" if pd.notna(waits_per_1000) else "N/A",
)
metric_columns[2].metric(
    "Attendances over 4 hours",
    f"{over_4_percent:.1f}%" if pd.notna(over_4_percent) else "N/A",
)
metric_columns[3].metric(
    "Trusts / months",
    f"{trust_summary['org_code'].nunique()} / {filtered['month'].nunique()}",
)

st.caption(
    f"Showing {filtered['month'].min():%B %Y} to {filtered['month'].max():%B %Y}. "
    "Meteorological seasons are DJF, MAM, JJA, and SON."
)

seasonal = (
    filtered.groupby("season", as_index=False)
    .agg(
        waits_12_plus=("waits_12_plus", "sum"),
        admissions=("emergency_admissions_via_ae", "sum"),
        months=("month", "nunique"),
    )
    .set_index("season")
    .reindex(SEASON_ORDER)
    .dropna(how="all")
    .reset_index()
)
seasonal["waits_per_1000_admissions"] = (
    1000 * seasonal["waits_12_plus"]
    / seasonal["admissions"].where(seasonal["admissions"] > 0)
)
season_columns = st.columns(2)
with season_columns[0]:
    st.subheader("Seasonal 12+ hour DTA wait counts")
    st.bar_chart(seasonal.set_index("season")[["waits_12_plus"]])
with season_columns[1]:
    st.subheader("Seasonal counts per 1,000 A&E admissions")
    st.bar_chart(seasonal.set_index("season")[["waits_per_1000_admissions"]])

st.subheader("Trust comparison")
rank_column = (
    "total_wait_counts"
    if rank_by == "12+ hour DTA wait counts"
    else "waits_per_1000_admissions"
)
top_trusts = trust_summary.nlargest(15, rank_column).copy()
top_trusts["label"] = (
    top_trusts["org_name"].fillna(top_trusts["org_code"]).astype(str)
    + " ("
    + top_trusts["org_code"].astype(str)
    + ")"
)
top_trusts = top_trusts.sort_values(rank_column)
fig, ax = plt.subplots(figsize=(11, max(5, len(top_trusts) * 0.38)))
ax.barh(top_trusts["label"], top_trusts[rank_column], color="#b2182b")
ax.set_xlabel(
    "12+ hour DTA wait counts"
    if rank_column == "total_wait_counts"
    else "Counts per 1,000 A&E emergency admissions"
)
ax.set_title(f"Top trusts by {rank_by.lower()}")
ax.grid(axis="x", alpha=0.25)
st.pyplot(fig, clear_figure=True)

st.subheader("A&E activity and normalized 12+ hour DTA counts")
correlation = trust_summary[
    ["mean_monthly_attendances", "waits_per_1000_admissions"]
].corr(method="pearson").iloc[0, 1]
st.caption(
    "Each point is a trust. The Pearson correlation compares mean monthly "
    "attendances with the trust's aggregate 12+ hour count per 1,000 admissions; "
    "it is descriptive, not causal. "
    + (
        f"Current filtered correlation: {correlation:.2f}."
        if pd.notna(correlation)
        else "Correlation is unavailable for this selection."
    )
)
fig, ax = plt.subplots(figsize=(10, 5))
ax.scatter(
    trust_summary["mean_monthly_attendances"],
    trust_summary["waits_per_1000_admissions"],
    alpha=0.75,
    color="#2c7bb6",
)
for row in trust_summary.nlargest(5, "waits_per_1000_admissions").itertuples():
    ax.annotate(
        row.org_code,
        (row.mean_monthly_attendances, row.waits_per_1000_admissions),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=8,
    )
ax.set_xlabel("Mean monthly A&E attendances")
ax.set_ylabel("12+ hour DTA counts per 1,000 A&E emergency admissions")
ax.grid(alpha=0.25)
st.pyplot(fig, clear_figure=True)

with st.expander("Definitions and limitations"):
    st.markdown(
        "- **12+ hour DTA wait count:** patients reported as waiting 12 or more "
        "hours from decision to admit to admission.\n"
        "- **Normalized value:** that count divided by emergency admissions via "
        "A&E, multiplied by 1,000. It is a scale comparison, not a duration.\n"
        "- **Over-four-hour attendance percentage:** reported over-four-hour "
        "attendance counts divided by recorded A&E attendances.\n"
        "- This aggregate dataset does not include exact elapsed wait durations, "
        "staffing, capacity, patient mix, or intervention outcomes. It cannot "
        "support mean/median wait minutes, causal conclusions, or model-based "
        "improvement recommendations."
    )
    st.dataframe(
        trust_summary.sort_values(rank_column, ascending=False).head(20),
        hide_index=True,
        width="stretch",
    )
    st.download_button(
        "Download filtered trust summary",
        trust_summary.sort_values(rank_column, ascending=False).to_csv(index=False),
        file_name="nhs_trust_wait_summary.csv",
        mime="text/csv",
    )

st.caption(
    "Source: NHS England A&E attendances and emergency admissions monthly "
    "aggregate files. Review high signals with local operational and case-mix "
    "information before deciding on an intervention."
)
