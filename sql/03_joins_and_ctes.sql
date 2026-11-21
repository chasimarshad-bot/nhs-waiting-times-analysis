-- Week 4: JOINs, CTEs, CASE WHEN

-- 1. Monthly totals and 12-hour DTA wait rate by parent organisation
WITH trust_monthly AS (
    SELECT
        parent_org,
        month,
        SUM(COALESCE(attendances_over_4hrs_type_1, 0)
            + COALESCE(attendances_over_4hrs_type_2, 0)
            + COALESCE(attendances_over_4hrs_other_department, 0)
            + COALESCE(attendances_over_4hrs_booked_appointments_type_1, 0)
            + COALESCE(attendances_over_4hrs_booked_appointments_type_2, 0)
            + COALESCE(attendances_over_4hrs_booked_appointments_other_department, 0)
        ) AS attendances_over_4hrs,
        SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
            AS patients_waited_12hrs
    FROM ae_monthly
    WHERE month IS NOT NULL
    GROUP BY parent_org, month
)
SELECT
    parent_org,
    month,
    attendances_over_4hrs,
    patients_waited_12hrs,
    CASE
        WHEN attendances_over_4hrs = 0 THEN NULL
        ELSE ROUND(100.0 * patients_waited_12hrs / attendances_over_4hrs, 2)
    END AS wait_12hrs_per_100_over_4hrs
FROM trust_monthly
ORDER BY month, wait_12hrs_per_100_over_4hrs DESC;

-- 2. Latest-month trust ranking with a CTE
WITH latest AS (
    SELECT MAX(month) AS month FROM ae_monthly
),
ranked AS (
    SELECT
        ae.org_code,
        ae.org_name,
        ae.parent_org,
        SUM(COALESCE(ae.patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
            AS patients_waited_12hrs
    FROM ae_monthly AS ae
    JOIN latest AS l ON ae.month = l.month
    GROUP BY ae.org_code, ae.org_name, ae.parent_org
)
SELECT *
FROM ranked
WHERE patients_waited_12hrs > 0
ORDER BY patients_waited_12hrs DESC;
