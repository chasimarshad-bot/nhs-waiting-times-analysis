# NHS A&E waiting times in England

**Muhammad Asim Arshad · Data analytics portfolio**

[Open the Streamlit dashboard](https://nhs-waiting-times-analysis-qdjsfpjiujjt4ym74pigt4.streamlit.app/) · [View the analysis and reproduction steps on GitHub](https://github.com/chasimarshad-bot/nhs-waiting-times-analysis)

## Business question

How did long waits after a decision to admit vary by trust and season, and how did those patterns change when I accounted for differences in admission volume? I built an interactive dashboard to help users spot patterns worth investigating with local operational data.

## Data and approach

I used 22 monthly extracts from NHS England’s A&E attendances and emergency admissions statistics, covering June 2024 to March 2026. The cleaned dataset contains 4,364 organisation-month records across 207 organisation codes. The main measure counts patients who waited at least 12 hours between the decision to admit and admission. [NHS England data source](https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/)

I used Python and pandas to standardise columns, parse reporting months and remove national total rows before aggregating. I used SQL and SQLite to compare monthly and seasonal patterns, report both raw counts and counts per 1,000 emergency admissions via A&E, and examine how long-wait counts varied with attendance volume. The Streamlit dashboard lets users filter by period, season, parent organisation and trust, then download the filtered trust summary. [Project README](https://github.com/chasimarshad-bot/nhs-waiting-times-analysis/blob/main/README.md)

## Key findings

| Finding | Result |
|---|---|
| Seasonal comparison | Winter recorded **144.19** long waits per 1,000 emergency admissions via A&E, the highest of the four observed seasons. Summer recorded the lowest at **87.75**. |
| Raw counts and admission-adjusted comparisons | University Hospitals Birmingham recorded the highest total at **39,231**. Among trusts with at least 18 months of data, Croydon Health Services had the highest count per 1,000 emergency admissions via A&E at **492.63**. |
| Attendance and long waits | Across 207 organisations, average monthly attendances and average monthly long-wait counts had a Pearson correlation of **0.667**. Larger attendance volumes tended to coincide with higher long-wait counts. |

[Findings and charts](https://github.com/chasimarshad-bot/nhs-waiting-times-analysis/blob/main/README.md#findings)

## Validation and reproducibility

The loader records checks for missing values, duplicate month–organisation keys and negative count values. The pull requests report successful dataset and SQL checks, Python compilation, and Streamlit AppTest runs with both SQLite and CSV-only loading. The documentation pull request also records an HTTP 200 response from the hosted dashboard during its smoke check. [Analysis and dashboard PR](https://github.com/chasimarshad-bot/nhs-waiting-times-analysis/pull/1) · [Documentation and deployment check PR](https://github.com/chasimarshad-bot/nhs-waiting-times-analysis/pull/2)

The interactive dashboard runs from the cleaned CSV committed to GitHub. The repository also contains the notebooks, SQL queries and processing scripts. Rebuilding the full pipeline requires downloading the original monthly extracts and generating the SQLite database locally. [Reproduction steps](https://github.com/chasimarshad-bot/nhs-waiting-times-analysis#run-locally)

## Limitations

The 22-month window covers fewer than two annual cycles and includes four spring months. The seasonal differences are exploratory. Counts per 1,000 emergency admissions provide context for comparing volumes. A patient-level probability would require linked records, and average elapsed waits would require individual wait durations. The aggregate data omits staffing, capacity and patient mix, which limits what can be said about the causes of the observed patterns. [Interpretation and limitations](https://github.com/chasimarshad-bot/nhs-waiting-times-analysis/blob/main/README.md#interpretation-and-limitations)

**Tools** · Python, pandas, SQL, SQLite, Jupyter, Matplotlib, seaborn and Streamlit. This was an individual portfolio project with GitHub Copilot assistance during implementation and documentation.

## CV or LinkedIn project entry

**NHS A&E Waiting Times Analysis**  
Analysed 4,364 organisation-month records across 22 months of NHS England A&E data using Python, pandas and SQL. Built an interactive Streamlit dashboard to compare 12+ hour waits after the decision to admit by trust and season, using counts per 1,000 emergency admissions to put volumes in context. Documented data quality checks and reproducible analysis steps. [Live dashboard](https://nhs-waiting-times-analysis-qdjsfpjiujjt4ym74pigt4.streamlit.app/)
