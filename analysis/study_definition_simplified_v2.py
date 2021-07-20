from cohortextractor import categorise, codelist, table

from codelists import long_covid_diagnostic_codes, covid_primary_care_code, covid_codes

pandemic_start = "2020-02-01"

registration_date = "2020-11-01"


class Cohort:

    # Patients registered on 2020-11-01
    population = (
        table("practice_registrations").date_in_range(registration_date).exists()
    )

    # COVID infection
    _sgss_positives = table("sgss_sars_cov_2").filter(positive_result=True)
    sgss_first_positive_test_date = _sgss_positives.earliest().get("date")

    _primary_care_covid = table("clinical_events").filter(
        "code", is_in=covid_primary_care_code
    )
    primary_care_covid_first_date = _primary_care_covid.earliest().get("date")

    _hospital_covid = table("hospitalisation").filter("code", is_in=covid_codes)
    hospital_covid_first_date = _hospital_covid.earliest().get("date")

    # Outcome
    _long_covid_table = table("clinical_events").filter(
        "code", is_in=long_covid_diagnostic_codes
    )
    long_covid = _long_covid_table.exists()
    first_long_covid_date = _long_covid_table.earliest().get("code")

    # Demographics
    _age = table("patients").age_as_of(registration_date)
    _age_categories = {
        "0-17": _age < 18,
        "18-24": _age >= 18 & _age < 25,
        "25-34": _age >= 25 & _age < 35,
        "35-44": _age >= 35 & _age < 45,
        "45-54": _age >= 45 & _age < 55,
        "55-69": _age >= 55 & _age < 70,
        "70-79": _age >= 70 & _age < 80,
        "80+": _age >= 80,
    }
    age_group = categorise(_age_categories, default="missing")

    # Sex
    sex = table("patients").get("sex")


# Add the Long covid code count variables
for code in long_covid_diagnostic_codes:
    variable_def = (
        table("clinical_events")
        .filter(code=codelist([code]))
        .filter("date", on_or_before=pandemic_start)
        .count("code")
    )
    setattr(Cohort, f"snomed_{code}", variable_def)
