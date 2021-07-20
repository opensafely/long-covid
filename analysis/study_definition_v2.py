from datetime import datetime
from dateutil.relativedelta import relativedelta

from cohortextractor import Codelist, c, categorise, table

from codelists import (
    any_long_covid_code,
    any_primary_care_code,
    ethnicity_codes,
    long_covid_diagnostic_codes,
    covid_codes,
    post_viral_fatigue_codes,
)


pandemic_start = "2020-02-01"

index_date = "2020-11-01"


class Cohort:

    # COVID infection
    _sgss_positives = table("sgss_sars_cov_2").filter(positive_result=True)
    sgss_first_positive_test_date = _sgss_positives.earliest().get("date")

    _primary_care_covid = table("clinical_events").filter(
        "code", is_in=any_primary_care_code
    )
    primary_care_covid_first_date = _primary_care_covid.earliest().get("date")

    _hospital_covid = table("hospitalisation").filter("code", is_in=covid_codes)
    hospital_covid_first_date = _hospital_covid.earliest().get("date")

    # Outcome
    _long_covid_table = table("clinical_events").filter(
        "code", is_in=any_long_covid_code
    )
    long_covid = _long_covid_table.exists()
    first_long_covid_code = _long_covid_table.earliest().get("code")

    # Population
    # Patients registered on 2020-11-01
    _registrations = table("practice_registrations").date_in_range(index_date)
    population = _registrations.exists()
    practice_id = _registrations.latest().get("pseudo_id")

    # Demographics
    # Age
    _age = table("patients").age_as_of(index_date)
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

    # Region
    region = _registrations.latest().get("nuts1_region_name")

    # IMD
    _imd_value = (
        table("patient_address")
        .date_in_range(index_date)
        .get("index_of_multiple_deprivation")
        .round_to_nearest(100)
    )
    _imd_groups = {
        "1": (_imd_value >= 1) & (_imd_value < (32844 * 1 / 5)),
        "2": (_imd_value >= 32844 * 1 / 5) & (_imd_value < (32844 * 2 / 5)),
        "3": (_imd_value >= 32844 * 2 / 5) & (_imd_value < (32844 * 3 / 5)),
        "4": (_imd_value >= 32844 * 3 / 5) & (_imd_value < (32844 * 4 / 5)),
        "5": (_imd_value >= 32844 * 4 / 5) & (_imd_value < 32844),
    }
    imd = categorise(_imd_groups, default="0")

    # Ethnicity
    ethnicity = table("patients").filter("code", is_in=ethnicity_codes).exists()

    # Clinical variables
    # BMI
    _bmi_date = datetime.strptime(index_date, "%Y-%M-%d") - relativedelta(months=60)
    _bmi_date = _bmi_date.strftime("%Y-%M-%d")
    _bmi_value = table("patients").bmi_as_of(_bmi_date, minimum_age_at_measurement=16)
    _bmi_groups = {
        "Obese I (30-34.9)": (_bmi_value >= 30) & (_bmi_value < 35),
        "Obese II (35-39.9)": (_bmi_value >= 35) & (_bmi_value < 40),
        "Obese III (40+)": (_bmi_value >= 40) & (_bmi_value < 100)
        # set maximum to avoid any impossibly extreme values being classified as obese
    }
    bmi = categorise(_bmi_groups, default="Not obese")

    # Previous COVID
    _previous_covid_categories = {
        "COVID positive": (
            c(sgss_first_positive_test_date) | c(primary_care_covid_first_date)
        )
        & ~c(hospital_covid_first_date),
        "COVID hospitalised": c(hospital_covid_first_date),
    }
    previous_covid = categorise(_previous_covid_categories, default="No COVID code")


# Add the long covid and post viral code count variables
for code in [*long_covid_diagnostic_codes, *post_viral_fatigue_codes]:
    variable_def = (
        table("clinical_events")
        .filter(code=Codelist([code], system="snomed"))
        .filter("date", on_or_before=pandemic_start)
        .count("code")
    )
    setattr(Cohort, f"snomed_{code}", variable_def)
