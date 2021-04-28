from cohortextractor import (
    StudyDefinition,
    Measure,
    patients,
    codelist,
    combine_codelists,
    codelist_from_csv,
)

from codelists import *
from common_variables import demographic_variables, clinical_variables

pandemic_start = "2020-02-01"


def make_variable(code):
    return {
        f"snomed_{code}": (
            patients.with_these_clinical_events(
                codelist([code], system="snomed"),
                on_or_after=pandemic_start,
                returning="number_of_matches_in_period",
                include_date_of_match=True,
                date_format="YYYY-MM-DD",
                return_expectations={
                    "incidence": 0.1,
                    "int": {"distribution": "normal", "mean": 3, "stddev": 1},
                },
            )
        )
    }


def loop_over_codes(code_list):
    variables = {}
    for code in code_list:
        variables.update(make_variable(code))
    return variables


study = StudyDefinition(
    default_expectations={
        "date": {"earliest": "index_date", "latest": "today"},
        "rate": "uniform",
        "incidence": 0.05,
        "int": {"distribution": "normal", "mean": 25, "stddev": 5},
        "float": {"distribution": "normal", "mean": 25, "stddev": 5},
    },
    index_date="2020-11-01",
    population=patients.satisfying(
        "registered AND (sex = 'M' OR sex = 'F')",
        registered=patients.registered_as_of("index_date"),
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
        return_expectations={"incidence": 0.1, "date": {"earliest": "index_date"}},
    ),
    **loop_over_codes(any_long_covid_code),
    first_long_covid_code=patients.with_these_clinical_events(
        any_long_covid_code,
        returning="code",
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
    post_viral_fatigue=patients.with_these_clinical_events(
        post_viral_fatigue_codes,
        on_or_after=pandemic_start,
        return_expectations={"incidence": 0.05},
    ),
    first_post_viral_fatigue_date=patients.with_these_clinical_events(
        post_viral_fatigue_codes,
        on_or_after=pandemic_start,
        returning="date",
        date_format="YYYY-MM-DD",
        find_first_match_in_period=True,
        return_expectations={"incidence": 0.1, "date": {"earliest": "index_date"}},
    ),
    **loop_over_codes(post_viral_fatigue_codes),
    practice_id=patients.registered_practice_as_of(
        "index_date",
        returning="pseudo_id",
        return_expectations={
            "int": {"distribution": "normal", "mean": 1000, "stddev": 100},
            "incidence": 1,
        },
    ),
    **demographic_variables,
    msoa=patients.registered_practice_as_of(
        "index_date",
        returning="msoa_code",
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "E02002488": 0.1,
                    "E02002586": 0.1,
                    "E02002677": 0.1,
                    "E02002814": 0.1,
                    "E02002915": 0.1,
                    "E02003251": 0.1,
                    "E02000003": 0.2,
                    "E02003334": 0.1,
                    "E02002986": 0.1,
                },
            },
        },
    ),
    # **clinical_variables,
)
