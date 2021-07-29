from cohortextractor import categorise, codelist, table

from codelists import long_covid_diagnostic_codes, covid_primary_care_code, covid_codes


pandemic_start = "2020-02-01"

registration_date = "2020-11-01"


class SimplifiedCohort:
    population = (
        table("practice_registrations").date_in_range(registration_date).exists()
    )

    # COVID infection
    sgss_first_positive_test_date = (
        table("sgss_sars_cov_2").filter(positive_result=True).earliest().get("date")
    )

    primary_care_covid_first_date = (
        table("clinical_events")
        .filter("code", is_in=covid_primary_care_code)
        .earliest()
        .get("date")
    )

    hospital_covid_first_date = (
        table("hospitalizations")
        .filter("code", is_in=covid_codes)
        .earliest()
        .get("date")
    )

    # Outcome
    _long_covid_table = table("clinical_events").filter(
        "code", is_in=long_covid_diagnostic_codes
    )
    long_covid = _long_covid_table.exists()
    first_long_covid_date = _long_covid_table.earliest().get("date")

    # Demographics
    # _age = table("patients").age_as_of(registration_date)
    # _age_categories = {
    #     "0-17": _age < 18,
    #     "18-24": _age >= 18 & _age < 25,
    #     "25-34": _age >= 25 & _age < 35,
    #     "35-44": _age >= 35 & _age < 45,
    #     "45-54": _age >= 45 & _age < 55,
    #     "55-69": _age >= 55 & _age < 70,
    #     "70-79": _age >= 70 & _age < 80,
    #     "80+": _age >= 80,
    # }
    # age_group = categorise(_age_categories, default="missing")
    #
    sex = table("patients").get("sex")


# Add the Long covid code count variables
for code in long_covid_diagnostic_codes.codes:
    variable_def = (
        table("clinical_events")
        .filter("code", is_in=codelist([code], long_covid_diagnostic_codes.system))
        .filter("date", on_or_after=pandemic_start)
        .count("code")
    )
    setattr(
        SimplifiedCohort, f"{long_covid_diagnostic_codes.system}_{code}", variable_def
    )