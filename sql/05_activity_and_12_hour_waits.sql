-- Week 5: Does higher A&E activity correspond to more 12-hour DTA waits?
-- One row per trust and month. Activity counts all recorded A&E attendance
-- categories; emergency admissions via A&E provide context for a normalized
-- 12-hour-wait rate.
WITH trust_monthly AS (
    SELECT
        month,
        org_code,
        org_name,
        parent_org,
        SUM(
            COALESCE(a_e_attendances_type_1, 0)
            + COALESCE(a_e_attendances_type_2, 0)
            + COALESCE(a_e_attendances_other_a_e_department, 0)
            + COALESCE(a_e_attendances_booked_appointments_type_1, 0)
            + COALESCE(a_e_attendances_booked_appointments_type_2, 0)
            + COALESCE(a_e_attendances_booked_appointments_other_department, 0)
        ) AS a_e_attendances,
        SUM(COALESCE(patients_who_have_waited_12_hrs_from_dta_to_admission, 0))
            AS patients_waited_12hrs,
        SUM(
            COALESCE(emergency_admissions_via_a_e_type_1, 0)
            + COALESCE(emergency_admissions_via_a_e_type_2, 0)
            + COALESCE(emergency_admissions_via_a_e_other_a_e_department, 0)
        ) AS emergency_admissions_via_ae
    FROM ae_monthly
    WHERE month IS NOT NULL
      AND org_code IS NOT NULL
    GROUP BY month, org_code, org_name, parent_org
)
SELECT
    month,
    org_code,
    org_name,
    parent_org,
    a_e_attendances,
    patients_waited_12hrs,
    emergency_admissions_via_ae,
    CASE
        WHEN emergency_admissions_via_ae = 0 THEN NULL
        ELSE ROUND(1000.0 * patients_waited_12hrs / emergency_admissions_via_ae, 2)
    END AS waits_12hrs_per_1000_ae_admissions
FROM trust_monthly
ORDER BY month, org_name;
