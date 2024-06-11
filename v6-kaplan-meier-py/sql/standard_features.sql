/* death_int
*/
WITH death_query AS (
    SELECT
        c.subject_id,
        DATEDIFF(DAY, cohort_start_date, death_date) AS death_int
    FROM
        @cohort_table c
    LEFT JOIN
        @cdm_database_schema.death T 
	ON T.person_id = c.subject_id
    {@cohort_id != -1} ? {AND cohort_definition_id = @cohort_id}
),

/* gender, year of birth, birth int, age
*/
person_query AS ( 
    SELECT
        c.subject_id,
        T.gender_concept_id AS gender,
		T.year_of_birth,
		DATEDIFF(DAY, birth_datetime, cohort_start_date) AS birth_int,
		DATEDIFF(YEAR, birth_datetime, cohort_start_date) - CASE WHEN (MONTH(birth_datetime) > MONTH(cohort_start_date)) OR (MONTH(birth_datetime) = MONTH(cohort_start_date) AND DAY(birth_datetime) > DAY(cohort_start_date)) THEN 1 ELSE 0 END age
    FROM
        @cohort_table c
    LEFT JOIN
        @cdm_database_schema.person T 
	ON T.person_id = c.subject_id
    {@cohort_id != -1} ? {AND cohort_definition_id = @cohort_id}
),

/* condition_concept_id, condition_occurrence_start, condition_occurrence_end
*/
condition_occurrence_query AS ( 
    SELECT
		c.subject_id,
        T.condition_concept_id,
		DATEDIFF(DAY, cohort_start_date, condition_start_date) AS condition_occurrence_start,
		DATEDIFF(DAY, cohort_start_date, condition_end_date) AS condition_occurrence_end
    FROM
        @cohort_table c
    LEFT JOIN
        @cdm_database_schema.condition_occurrence T 
	ON T.person_id = c.subject_id
    {@cohort_id != -1} ? {AND cohort_definition_id = @cohort_id}
),

/* drug_concept_id, drug_exposure_start, drug_exposure_end
*/
drug_exposure_query AS ( 
    SELECT
		c.subject_id,
        T.drug_concept_id,
		DATEDIFF(DAY, cohort_start_date, drug_exposure_start_date) AS drug_exposure_start,
		DATEDIFF(DAY, cohort_start_date, drug_exposure_end_date) AS drug_exposure_end
    FROM
        @cohort_table c
    LEFT JOIN
        @cdm_database_schema.drug_exposure T 
	ON T.person_id = c.subject_id
    {@cohort_id != -1} ? {AND cohort_definition_id = @cohort_id}
),

/* procedure_concept_id, procedure_occurrence_start, procedure_occurrence_end
*/
procedure_occurrence_query AS ( 
    SELECT
		c.subject_id,
        T.procedure_concept_id,
		DATEDIFF(DAY, cohort_start_date, procedure_date) AS procedure_occurrence_start,
		DATEDIFF(DAY, cohort_start_date, procedure_end_date) AS procedure_occurrence_end
    FROM
        @cohort_table c
    LEFT JOIN
        @cdm_database_schema.procedure_occurrence T 
	ON T.person_id = c.subject_id
    {@cohort_id != -1} ? {AND cohort_definition_id = @cohort_id}
),

/* measurement_concept_id, measurement_start, measurement_unit_concept_id, measurement_vac, 
   measurement_van, measurement_operator_concept_id
*/
measurement_query AS ( 
    SELECT
		c.subject_id,
        T.measurement_concept_id,
		DATEDIFF(DAY, cohort_start_date, measurement_date) AS measurement_start,
		T.unit_concept_id AS measurement_unit_concept_id,
		T.value_as_concept_id AS measurement_vac,
		T.value_as_number AS measurement_van,
		T.operator_concept_id AS measurement_operator_concept_id
    FROM
        @cohort_table c
    LEFT JOIN
        @cdm_database_schema.measurement T 
	ON T.person_id = c.subject_id
    {@cohort_id != -1} ? {AND cohort_definition_id = @cohort_id}
),

/* observation_concept_id, observation_start, observation_unit_concept_id, observation_vac, 
observation_van, observation_vas, observation_qualifier_concept_id
*/
observation_query AS ( 
    SELECT
		c.subject_id,
        T.observation_concept_id,
		DATEDIFF(DAY, cohort_start_date, observation_date) AS observation_start,
		T.unit_concept_id AS observation_unit_concept_id,
		T.value_as_concept_id AS observation_vac,
		T.value_as_number AS observation_van,
		T.value_as_string AS observation_vas,
		T.qualifier_concept_id AS observation_qualifier_concept_id
    FROM
        @cohort_table c
    LEFT JOIN
        @cdm_database_schema.observation T 
	ON T.person_id = c.subject_id
    {@cohort_id != -1} ? {AND cohort_definition_id = @cohort_id}
)


SELECT
    d.subject_id,
    d.death_int,
    p.gender,
	p.year_of_birth,
	p.birth_int,
	p.age,
	c.condition_concept_id,
	c.condition_occurrence_start,
	c.condition_occurrence_end,
	de.drug_concept_id,
	de.drug_exposure_start,
	de.drug_exposure_end,
	po.procedure_concept_id, 
	po.procedure_occurrence_start, 
	po.procedure_occurrence_end,
	m.measurement_concept_id, 
	m.measurement_start, 
	m.measurement_unit_concept_id, 
	m.measurement_vac, 
	m.measurement_van, 
	m.measurement_operator_concept_id,
	o.observation_concept_id, 
	o.observation_start, 
	o.observation_unit_concept_id, 
	o.observation_vac, 
	o.observation_van, 
	o.observation_vas, 
	o.observation_qualifier_concept_id
FROM
    person_query p 
FULL OUTER JOIN
    death_query d
	ON d.subject_id = p.subject_id
FULL OUTER JOIN
	condition_occurrence_query c 
	ON p.subject_id = c.subject_id
FULL OUTER JOIN
	drug_exposure_query de
	ON p.subject_id = de.subject_id
FULL OUTER JOIN
	procedure_occurrence_query po
	ON p.subject_id = po.subject_id
FULL OUTER JOIN
	measurement_query m
	ON p.subject_id = m.subject_id
FULL OUTER JOIN
	observation_query o
	ON p.subject_id = o.subject_id
	
WHERE (condition_concept_id IN (@incl_condition_concept_id) OR (@incl_condition_concept_id) IS NULL)
AND (procedure_concept_id IN (@incl_procedure_concept_id) OR (@incl_procedure_concept_id) IS NULL)
AND (measurement_concept_id IN (@incl_measurement_concept_id) OR (@incl_measurement_concept_id) IS NULL)
AND (drug_concept_id IN (@incl_drug_concept_id) OR (@incl_drug_concept_id) IS NULL)

ORDER BY p.subject_id ASC -- LIMIT 100



