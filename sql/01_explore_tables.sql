-- 01: First look at the data
-- Run these in SQLite after scripts/load_data.py and the combine step
-- in notebooks/01_explore.ipynb have created ae_monthly.

-- List all tables
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;

-- Inspect the cleaned, combined A&E table
SELECT *
FROM ae_monthly
LIMIT 10;

-- Count the combined rows and months
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT month) AS distinct_months
FROM ae_monthly;

-- Confirm the period parsing
SELECT
    SUM(CASE WHEN month IS NULL THEN 1 ELSE 0 END) AS unparsed_dates,
    MIN(month) AS first_month,
    MAX(month) AS latest_month
FROM ae_monthly;
