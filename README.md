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

## First milestone: September 2025

Start with [NHS England's 2025–26 monthly release page](https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2025-26/). Under September 2025, download **Monthly A&E September 2025 (revised 13.11.25) (CSV)**. Save it as `data/raw/ae_2025_09.csv` and run the loader above. The filename gives the SQLite table its name, `ae_2025_09`.

**First question:** Among reporting providers with Type 1 (major A&E) activity, which had the highest share of attendances lasting more than four hours from arrival?

1. Inspect the imported columns and a few rows. Identify the provider code, the Type 1 attendance count and the Type 1 count over four hours.
2. Check for summary rows, duplicate provider codes, missing counts and counts over four hours that exceed total attendances.
3. For provider rows with valid counts and at least one Type 1 attendance, divide the Type 1 count over four hours by total Type 1 attendances. Multiply by 100 and display the attendance count alongside the percentage so readers can see the effect of small denominators.

This measure starts at arrival and ends at admission, transfer or discharge. NHS England also publishes a separate measure that starts at the decision to admit.

## Key findings
_To be added._

## What I learned / next steps
_To be added._
