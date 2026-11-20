"""Load every CSV in data/raw/ into a SQLite database (data/nhs.db).

Each file becomes one table, named after the file.
Column names are cleaned to lowercase_with_underscores.
"""
from pathlib import Path
import re
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "nhs.db"


def clean_name(name: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower())
    return name.strip("_") or "col"


def build_ae_monthly(conn: sqlite3.Connection) -> int:
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name != 'ae_monthly'",
        conn,
    )["name"].tolist()
    if not tables:
        return 0

    reference_cols = pd.read_sql(
        f'SELECT * FROM "{tables[0]}" LIMIT 0', conn
    ).columns.tolist()
    frames = []
    for table in tables:
        df = pd.read_sql(f'SELECT * FROM "{table}"', conn)
        df = df[[c for c in reference_cols if c in df.columns]].copy()
        df["source_table"] = table
        frames.append(df)

    ae = pd.concat(frames, ignore_index=True)
    parts = ae["period"].astype("string").str.split("-", expand=True)
    ae["month"] = pd.to_datetime(
        parts[1].fillna("") + " " + parts[2].fillna(""),
        format="%B %Y",
        errors="coerce",
    )
    ae.to_sql("ae_monthly", conn, if_exists="replace", index=False)
    return len(ae)


def main() -> None:
    files = sorted(RAW.glob("*.csv"))
    if not files:
        print(f"No CSV files found in {RAW}. Download some first (see README).")
        return

    with sqlite3.connect(DB) as conn:
        for f in files:
            df = pd.read_csv(f, encoding="latin-1")
            df.columns = [clean_name(c) for c in df.columns]
            table = clean_name(f.stem)
            df.to_sql(table, conn, if_exists="replace", index=False)
            print(f"Loaded {f.name} -> table '{table}' ({len(df)} rows, {len(df.columns)} columns)")
        ae_rows = build_ae_monthly(conn)
        if ae_rows:
            ae_months = pd.read_sql(
                "SELECT COUNT(DISTINCT month) AS months FROM ae_monthly", conn
            ).iloc[0, 0]
            print(f"Built ae_monthly ({ae_rows} rows, {ae_months} months)")
    print(f"\nDatabase saved to {DB}")


if __name__ == "__main__":
    main()
