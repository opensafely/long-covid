from cohortextractor import categorise, codelist, table

from codelists import (
    any_long_covid_code,
    any_primary_care_code,
    long_covid_diagnostic_codes,
    covid_codes,
    post_viral_fatigue_codes,
)
from codelists_v2 import ethnicity_codes


pandemic_start = "2020-02-01"
index_date = "2020-11-01"
bmi_code = "22K.."


class Cohort:

    # Population
    # Patients registered on 2020-11-01
    _registrations = table("practice_registrations").date_in_range(index_date)
    _current_registrations = _registrations.latest("date_end")
    population = _registrations.exists()
    practice_id = _current_registrations.get("pseudo_id")

    # COVID infection
    sgss_positive = (
        table("sgss_sars_cov_2").filter(positive_result=True).earliest().get("date")
    )

    primary_care_covid = (
        table("clinical_events")
        .filter("code", is_in=any_primary_care_code)
        .earliest()
        .get("date")
    )

    hospital_covid = (
        table("hospitalizations")
        .filter("code", is_in=covid_codes)
        .earliest()
        .get("date")
    )

    # Outcome
    _long_covid_table = table("clinical_events").filter(
        "code", is_in=any_long_covid_code
    )
    long_covid = _long_covid_table.exists()
    first_long_covid_date = _long_covid_table.earliest().get("date")
    first_long_covid_code = _long_covid_table.earliest().get("code")

    _post_viral_fatigue_table = table("clinical_events").filter(
        "code", is_in=post_viral_fatigue_codes
    )
    post_viral_fatigue = _post_viral_fatigue_table.exists()
    first_post_viral_fatigue_date = _post_viral_fatigue_table.earliest().get("date")

    # Demographics
    # Age
    _age = table("patients").age_as_of(index_date)
    _age_categories = {
        "0-17": _age < 18,
        "18-24": (_age >= 18) & (_age < 25),
        "25-34": (_age >= 25) & (_age < 35),
        "35-44": (_age >= 35) & (_age < 45),
        "45-54": (_age >= 45) & (_age < 55),
        "55-69": (_age >= 55) & (_age < 70),
        "70-79": (_age >= 70) & (_age < 80),
        "80+": _age >= 80,
    }
    age_group = categorise(_age_categories, default="missing")

    # Sex
    sex = table("patients").get("sex")

    # Region
    region = _current_registrations.get("nuts1_region_name")

    # IMD
    _imd_value = table("patient_address").imd_rounded_as_of(index_date)
    _imd_groups = {
        "1": (_imd_value >= 1) & (_imd_value < (32844 * 1 / 5)),
        "2": (_imd_value >= 32844 * 1 / 5) & (_imd_value < (32844 * 2 / 5)),
        "3": (_imd_value >= 32844 * 2 / 5) & (_imd_value < (32844 * 3 / 5)),
        "4": (_imd_value >= 32844 * 3 / 5) & (_imd_value < (32844 * 4 / 5)),
        "5": (_imd_value >= 32844 * 4 / 5) & (_imd_value < 32844),
    }
    imd = categorise(_imd_groups, default="0")

    # Ethnicity
    ethnicity = (
        table("clinical_events")
        .filter("code", is_in=ethnicity_codes)
        .filter("date", on_or_before=index_date)
        .latest()
        .get("code")
    )

    # Previous COVID
    _previous_covid_categories = {
        "COVID positive": (sgss_positive | primary_care_covid) & ~hospital_covid,
        "COVID hospitalised": hospital_covid,
    }
    previous_covid = categorise(_previous_covid_categories, default="No COVID code")


# Add the long covid and post viral code count variables
for target_codelist in [any_long_covid_code, post_viral_fatigue_codes]:
    for code in target_codelist.codes:
        filtered_to_code = (
            table("clinical_events")
            .filter("code", is_in=codelist([code], target_codelist.system))
            .filter("date", on_or_after=pandemic_start)
        )
        count_variable_def = filtered_to_code.count("code")
        date_variable_def = filtered_to_code.earliest().get("date")
        setattr(Cohort, f"{target_codelist.system}_{code}", count_variable_def)
        setattr(Cohort, f"{target_codelist.system}_{code}_date", date_variable_def)
