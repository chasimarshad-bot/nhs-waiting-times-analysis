-- Week 4: RANK, LAG, rolling averages

-- 1. Rank trusts within each month by 12-hour DTA waits
WITH monthly_totals AS (
    SELECT
        month,
        org_code,
        org_name,
        parent_org,
        SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
            AS patients_waited_12hrs
    FROM ae_monthly
    WHERE month IS NOT NULL
    GROUP BY month, org_code, org_name, parent_org
),
ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY month
            ORDER BY patients_waited_12hrs DESC
        ) AS wait_rank
    FROM monthly_totals
)
SELECT *
FROM ranked
WHERE wait_rank <= 10
ORDER BY month DESC, wait_rank;

-- 2. Month-over-month change and rolling three-month average
WITH monthly_totals AS (
    SELECT
        org_code,
        org_name,
        month,
        SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
            AS patients_waited_12hrs
    FROM ae_monthly
    WHERE month IS NOT NULL
    GROUP BY org_code, org_name, month
),
changes AS (
    SELECT
        *,
        LAG(patients_waited_12hrs) OVER (
            PARTITION BY org_code
            ORDER BY month
        ) AS previous_month_waits,
        AVG(patients_waited_12hrs) OVER (
            PARTITION BY org_code
            ORDER BY month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_3_month_average
    FROM monthly_totals
)
SELECT
    org_code,
    org_name,
    month,
    patients_waited_12hrs,
    previous_month_waits,
    patients_waited_12hrs - previous_month_waits AS absolute_change,
    CASE
        WHEN previous_month_waits IS NULL OR previous_month_waits = 0 THEN NULL
        ELSE ROUND(100.0 * (patients_waited_12hrs - previous_month_waits)
            / previous_month_waits, 2)
    END AS percentage_change,
    ROUND(rolling_3_month_average, 1) AS rolling_3_month_average
FROM changes
ORDER BY month DESC, absolute_change DESC;
