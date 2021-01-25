from cohortextractor import StudyDefinition, patients, codelist, codelist_from_csv


study = StudyDefinition(
    default_expectations={
        "date": {"earliest": "1900-01-01", "latest": "today"},
        "rate": "exponential_increase",
    },
    population=patients.registered_with_one_practice_between(
        "2019-02-01", "2020-02-01"
    ),
)
