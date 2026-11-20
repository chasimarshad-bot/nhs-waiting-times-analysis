-- Week 3: SELECT, WHERE, GROUP BY, ORDER BY

-- 1. Monthly national A&E attendance and 12-hour DTA wait totals
SELECT
    month,
    SUM(COALESCE(attendances_over_4hrs_type_1, 0)
        + COALESCE(attendances_over_4hrs_type_2, 0)
        + COALESCE(attendances_over_4hrs_other_department, 0)
        + COALESCE(attendances_over_4hrs_booked_appointments_type_1, 0)
        + COALESCE(attendances_over_4hrs_booked_appointments_type_2, 0)
        + COALESCE(attendances_over_4hrs_booked_appointments_other_department, 0)
    ) AS attendances_over_4hrs,
    SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0)) AS patients_waited_12hrs
FROM ae_monthly
WHERE month IS NOT NULL
GROUP BY month
ORDER BY month;

-- 2. Trusts with the longest 12-hour DTA waits in the latest month
WITH latest_month AS (
    SELECT MAX(month) AS month
    FROM ae_monthly
)
SELECT
    ae.org_code,
    ae.org_name,
    ae.parent_org,
    SUM(COALESCE(ae.patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
        AS patients_waited_12hrs
FROM ae_monthly AS ae
JOIN latest_month AS lm ON ae.month = lm.month
GROUP BY ae.org_code, ae.org_name, ae.parent_org
ORDER BY patients_waited_12hrs DESC
LIMIT 15;

-- 3. Trusts with the largest month-over-month change in 12-hour waits
WITH monthly_totals AS (
    SELECT
        org_code,
        org_name,
        parent_org,
        month,
        SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
            AS patients_waited_12hrs
    FROM ae_monthly
    WHERE month IS NOT NULL
    GROUP BY org_code, org_name, parent_org, month
),
month_pairs AS (
    SELECT
        *,
        LAG(patients_waited_12hrs) OVER (
            PARTITION BY org_code
            ORDER BY month
        ) AS previous_month_waits
    FROM monthly_totals
)
SELECT
    org_code,
    org_name,
    parent_org,
    month,
    patients_waited_12hrs,
    previous_month_waits,
    patients_waited_12hrs - previous_month_waits AS change_in_waits
FROM month_pairs
WHERE previous_month_waits IS NOT NULL
ORDER BY change_in_waits DESC
LIMIT 15;
