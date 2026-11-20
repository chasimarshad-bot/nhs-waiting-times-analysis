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
The checked-out repository does not contain the raw CSV files or `data/nhs.db`,
so it is not possible to report trust names or numeric waiting-time totals without
fabricating them. The executed exploration notebook shows the available analysis
process:

- It loaded 22 monthly A&E source tables into a combined `ae_monthly` table.
- The combined table contains 4,386 rows across 22 months.
- The first month with a parseable date and the latest month are determined by
  the 22 source periods, not by hard-coded assumptions.
- The 12-hour wait measures use
  `patients_who_have_waited_12_hrs_from_dta_to_admission`.
- “Longest waits” is reported as the sum of that measure for a trust in the latest
  month. Month-over-month change is the absolute change or percentage change
  from the previous month for the same trust.

After the raw CSVs are placed in `data/raw/`, run
`python scripts/load_data.py` and `python scripts/chart_summary.py` to calculate
and reproduce these findings. The chart script saves
`images/waiting_times_summary.png`.

## What I learned / next steps
I learned that NHS monthly exports can have inconsistent extra columns even when
the core schema is stable, so combining tables requires a reference column set
and explicit removal of stray columns. I also learned to convert the coded
`MSitAE-MONTH-YEAR` period field into a real date before ranking or comparing
months.

Next steps are to add the missing raw data locally, run the completed SQL and
chart scripts, and replace this evidence-bounded draft with named trusts,
month-by-month values, and a short interpretation of the largest increases.
