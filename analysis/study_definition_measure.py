from cohortextractor import (
    StudyDefinition,
    Measure,
    patients,
    codelist,
    combine_codelists,
    codelist_from_csv,
)

from codelists import *

study = StudyDefinition(
    default_expectations={
        "date": {"earliest": "1900-01-01", "latest": "today"},
        "rate": "uniform",
        "incidence": 0.05,
    },
    index_date="2020-11-02",
    population=patients.satisfying(
        "has_follow_up AND (sex = 'M' OR sex = 'F')",
        has_follow_up=patients.registered_with_one_practice_between(
            "index_date", "index_date"
        ),
    ),
    # Outcome
    long_covid=patients.with_these_clinical_events(
        any_long_covid_code,
        between=["index_date", "index_date + 6 days"],
        return_expectations={"incidence": 0.05},
    ),
    # Stratifiers
    age_group=patients.categorised_as(
        {
            "0-49": "age < 50",
            "50-59": "age >= 50 AND age < 60",
            "60-69": "age >= 60 AND age < 70",
            "70-79": "age >= 70 AND age < 80",
            "80+": "age >= 80",
            "missing": "DEFAULT",
        },
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "0-49": 0.1,
                    "50-59": 0.2,
                    "60-69": 0.3,
                    "70-79": 0.2,
                    "80+": 0.2,
                }
            },
        },
        age=patients.age_as_of(
            "index_date",
        ),
    ),
    sex=patients.sex(
        return_expectations={
            "rate": "universal",
            "category": {"ratios": {"M": 0.49, "F": 0.51}},
        }
    ),
    previous_covid=patients.categorised_as(
        {
            "COVID positive": """
                                (sgss_positive OR primary_care_covid)
                                AND NOT hospital_covid
                                """,
            "COVID hospitalised": "hospital_covid",
            "No previous COVID code": "DEFAULT",
        },
        return_expectations={
            "incidence": 1,
            "category": {
                "ratios": {
                    "COVID positive": 0.4,
                    "COVID hospitalised": 0.4,
                    "No previous COVID code": 0.2,
                }
            },
        },
        sgss_positive=patients.with_test_result_in_sgss(
            pathogen="SARS-CoV-2", test_result="positive", on_or_before="index_date"
        ),
        primary_care_covid=patients.with_these_clinical_events(
            any_primary_care_code,
            on_or_before="index_date",
        ),
        hospital_covid=patients.admitted_to_hospital(
            returning="date_admitted",
            with_these_diagnoses=covid_codes,
            on_or_before="index_date",
        ),
    ),
)


measures = [
    Measure(id="all_rate", numerator="long_covid", denominator="population"),
    Measure(
        id="sex_rate",
        numerator="long_covid",
        denominator="population",
        group_by=["sex"],
    ),
    Measure(
        id="age_group_rate",
        numerator="long_covid",
        denominator="population",
        group_by=["age_group"],
    ),
    Measure(
        id="covid_record_rate",
        numerator="long_covid",
        denominator="population",
        group_by=["previous_covid"],
    ),
]
