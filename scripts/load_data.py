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
    print(f"\nDatabase saved to {DB}")


if __name__ == "__main__":
    main()
