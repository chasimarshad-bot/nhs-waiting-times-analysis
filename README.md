# NHS Waiting Times Analysis (SQL + Python)

> Work in progress: Phase 1 of my Public Services Data Portfolio.

## Question
Which NHS trusts and regions have the longest waits, and how have they changed over time?

## Data
NHS England statistics: A&E attendances and emergency admissions
https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/

Raw files are not stored in this repo. Download them into `data/raw/` (see below).

## Tools
SQLite, Python (pandas), Jupyter, seaborn / matplotlib

## Project structure
```
data/raw/      original downloaded CSVs (not committed)
data/clean/    cleaned data (not committed)
sql/           SQL queries, numbered in the order I learned them
notebooks/     analysis notebook
scripts/       load_data.py loads CSVs into SQLite
images/        charts used in this README
```

## How to run
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# put CSV files in data/raw/, then:
python scripts/load_data.py
```

## Key findings
_To be added._

## What I learned / next steps
_To be added._
