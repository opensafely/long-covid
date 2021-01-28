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
    index_date="2020-02-01",
    population=patients.satisfying(
        "has_follow_up AND (sex = 'M' OR sex = 'F')",
        has_follow_up=patients.registered_with_one_practice_between(
            "index_date", "index_date - 1 year"
        ),
    ),
    # Outcome
    long_covid=patients.with_these_clinical_events(
        any_long_covid_code,
        return_expectations={"incidence": 0.05},
    ),
    first_long_covid_date=patients.with_these_clinical_events(
        any_long_covid_code,
        returning="date",
        date_format="YYYY-MM-DD",
        find_first_match_in_period=True,
        return_expectations={"incidence": 0.05, "date": {"earliest": "index_date"}},
    ),
    first_long_covid_code=patients.with_these_clinical_events(
        any_long_covid_code,
        returning="date",
        find_first_match_in_period=True,
        return_expectations={
            "incidence": 0.05,
            "category": {
                "ratios": {
                    "1325161000000102": 0.2,
                    "1325181000000106": 0.2,
                    "1325021000000106": 0.3,
                    "1325051000000101": 0.2,
                    "1325061000000103": 0.1,
                }
            },
        },
    ),
    # Stratifiers
    age_group=patients.categorised_as(
        {
            "<18": "age < 18",
            "18-49": "age >= 18 AND age < 50",
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
                    "<18": 0.1,
                    "0-49": 0.1,
                    "50-59": 0.2,
                    "60-69": 0.3,
                    "70-79": 0.2,
                    "80+": 0.1,
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
