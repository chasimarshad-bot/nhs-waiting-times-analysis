"""Load, standardize, validate, and combine monthly A&E source CSVs."""
from pathlib import Path
import re
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
DB = ROOT / "data" / "nhs.db"

IDENTIFIER_COLUMNS = ["period", "org_code", "parent_org", "org_name"]
COUNT_COLUMNS = [
    "a_e_attendances_type_1",
    "a_e_attendances_type_2",
    "a_e_attendances_other_a_e_department",
    "a_e_attendances_booked_appointments_type_1",
    "a_e_attendances_booked_appointments_type_2",
    "a_e_attendances_booked_appointments_other_department",
    "attendances_over_4hrs_type_1",
    "attendances_over_4hrs_type_2",
    "attendances_over_4hrs_other_department",
    "attendances_over_4hrs_booked_appointments_type_1",
    "attendances_over_4hrs_booked_appointments_type_2",
    "attendances_over_4hrs_booked_appointments_other_department",
    "patients_who_have_waited_4_12_hs_from_dta_to_admission",
    "patients_who_have_waited_12_hrs_from_dta_to_admission",
    "emergency_admissions_via_a_e_type_1",
    "emergency_admissions_via_a_e_type_2",
    "emergency_admissions_via_a_e_other_a_e_department",
    "other_emergency_admissions",
]
SOURCE_COLUMNS = IDENTIFIER_COLUMNS + COUNT_COLUMNS


def clean_name(name: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower())
    return name.strip("_") or "col"


def read_source(path: Path) -> tuple[str, pd.DataFrame]:
    table = clean_name(path.stem)
    if table == "ae_monthly":
        raise ValueError(f"{path.name} conflicts with the generated ae_monthly table")

    df = pd.read_csv(path, encoding="latin-1", dtype="string")
    df.columns = [clean_name(column) for column in df.columns]
    if not df.columns.is_unique:
        raise ValueError(f"{path.name} has duplicate column names after normalization")
    return table, df


def clean_sources(
    sources: list[tuple[str, pd.DataFrame]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    extras_by_table = {}
    invalid_numeric = {column: 0 for column in COUNT_COLUMNS}
    raw_rows = 0
    total_rows = 0
    total_period_rows = 0
    total_organization_rows = 0

    for table, source in sources:
        missing = sorted(set(SOURCE_COLUMNS) - set(source.columns))
        if missing:
            raise ValueError(f"{table} is missing required columns: {', '.join(missing)}")

        extras_by_table[table] = sorted(set(source.columns) - set(SOURCE_COLUMNS))
        raw_rows += len(source)
        total_period_mask = (
            source["period"].astype("string").str.strip().str.casefold().eq("total")
        )
        total_organization_mask = (
            source[["org_code", "parent_org", "org_name"]]
            .apply(lambda column: column.astype("string").str.strip().str.casefold().eq("total"))
            .fillna(False)
            .all(axis=1)
        )
        total_mask = total_period_mask | total_organization_mask
        total_period_rows += int(total_period_mask.sum())
        total_organization_rows += int(total_organization_mask.sum())
        total_rows += int(total_mask.sum())
        frame = source.loc[~total_mask, SOURCE_COLUMNS].copy()
        for column in COUNT_COLUMNS:
            raw = frame[column].astype("string").str.strip()
            normalized = raw.str.replace(",", "", regex=False).replace("", pd.NA)
            values = pd.to_numeric(normalized, errors="coerce")
            present = raw.notna() & raw.ne("")
            invalid_numeric[column] += int((present & values.isna()).sum())
            frame[column] = values

        period_parts = frame["period"].astype("string").str.extract(
            r"^[^-]+-([A-Za-z]+)-([0-9]{4})$"
        )
        frame["month"] = pd.to_datetime(
            period_parts[0] + " " + period_parts[1],
            format="%B %Y",
            errors="coerce",
        )
        frame["source_table"] = table
        frames.append(frame)

    if not frames:
        raise ValueError("No monthly A&E source tables were provided")

    ae = pd.concat(frames, ignore_index=True)
    valid_keys = ae["month"].notna() & ae["org_code"].notna()
    duplicate_rows = int(
        ae.loc[valid_keys].duplicated(["month", "org_code"], keep=False).sum()
    )
    dated_orgs = ae.loc[valid_keys]
    name_changes = int(
        dated_orgs.groupby("org_code")["org_name"].nunique().gt(1).sum()
    )
    parent_changes = int(
        dated_orgs.groupby("org_code")["parent_org"].nunique().gt(1).sum()
    )
    negative_counts = int((ae[COUNT_COLUMNS] < 0).sum().sum())
    quality = [
        ("source_files", len(sources)),
        ("raw_source_rows", raw_rows),
        ("excluded_total_rows", total_rows),
        ("rows_marked_total_by_period", total_period_rows),
        ("rows_marked_total_by_organization", total_organization_rows),
        ("rows", len(ae)),
        ("months", int(ae["month"].nunique())),
        ("first_month", ae["month"].min()),
        ("latest_month", ae["month"].max()),
        ("unparsed_period_rows", int(ae["month"].isna().sum())),
        ("missing_org_code_rows", int(ae["org_code"].isna().sum())),
        ("duplicate_month_org_code_rows", duplicate_rows),
        ("organization_codes_with_name_changes", name_changes),
        ("organization_codes_with_parent_changes", parent_changes),
        ("negative_count_values", negative_counts),
    ]
    quality.extend(
        (f"missing_values:{column}", int(ae[column].isna().sum()))
        for column in SOURCE_COLUMNS
    )
    quality.extend(
        (f"invalid_numeric_values:{column}", count)
        for column, count in invalid_numeric.items()
    )
    quality.extend(
        (f"extra_columns:{table}", ", ".join(columns) or "none")
        for table, columns in extras_by_table.items()
    )
    return ae, pd.DataFrame(quality, columns=["check", "value"])


def main() -> None:
    files = sorted(RAW.glob("*.csv"))
    if not files:
        print(f"No CSV files found in {RAW}. Download monthly A&E extracts first.")
        return

    sources = [read_source(path) for path in files]
    table_names = [table for table, _ in sources]
    if len(table_names) != len(set(table_names)):
        raise ValueError("Multiple source filenames normalize to the same table name")

    ae, quality = clean_sources(sources)
    CLEAN.mkdir(parents=True, exist_ok=True)
    DB.parent.mkdir(parents=True, exist_ok=True)
    ae.to_csv(CLEAN / "ae_monthly.csv", index=False)
    quality.to_csv(CLEAN / "data_quality_report.csv", index=False)

    with sqlite3.connect(DB) as conn:
        for table, df in sources:
            df.to_sql(table, conn, if_exists="replace", index=False)
        ae.to_sql("ae_monthly", conn, if_exists="replace", index=False)

    print(
        f"Loaded and cleaned {len(files)} source files: {len(ae)} rows, "
        f"{ae['month'].nunique()} months"
    )
    print(f"Cleaned CSV: {CLEAN / 'ae_monthly.csv'}")
    print(f"Data quality checks: {CLEAN / 'data_quality_report.csv'}")
    print(f"SQLite database: {DB}")


if __name__ == "__main__":
    main()
