from cohortextractor import patients
from codelists import *


demographic_variables = dict(
    age_group=patients.categorised_as(
        {
            "0-17": "age < 18",
            "18-24": "age >= 18 AND age < 25",
            "25-34": "age >= 25 AND age < 35",
            "35-44": "age >= 35 AND age < 45",
            "45-54": "age >= 45 AND age < 55",
            "55-69": "age >= 55 AND age < 70",
            "70-79": "age >= 70 AND age < 80",
            "80+": "age >= 80",
            "missing": "DEFAULT",
        },
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "0-17": 0.1,
                    "18-24": 0.1,
                    "25-34": 0.1,
                    "35-44": 0.1,
                    "45-54": 0.2,
                    "55-69": 0.2,
                    "70-79": 0.1,
                    "80+": 0.1,
                }
            },
        },
        age=patients.age_as_of("index_date"),
    ),
    sex=patients.sex(
        return_expectations={
            "rate": "universal",
            "category": {"ratios": {"M": 0.49, "F": 0.51}},
        }
    ),
    region=patients.registered_practice_as_of(
        "index_date",
        returning="nuts1_region_name",
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "North East": 0.1,
                    "North West": 0.1,
                    "Yorkshire and The Humber": 0.1,
                    "East Midlands": 0.1,
                    "West Midlands": 0.1,
                    "East": 0.1,
                    "London": 0.2,
                    "South East": 0.1,
                    "South West": 0.1,
                },
            },
        },
    ),
    imd=patients.categorised_as(
        {
            "0": "DEFAULT",
            "1": """index_of_multiple_deprivation >=1 AND index_of_multiple_deprivation < 32844*1/5""",
            "2": """index_of_multiple_deprivation >= 32844*1/5 AND index_of_multiple_deprivation < 32844*2/5""",
            "3": """index_of_multiple_deprivation >= 32844*2/5 AND index_of_multiple_deprivation < 32844*3/5""",
            "4": """index_of_multiple_deprivation >= 32844*3/5 AND index_of_multiple_deprivation < 32844*4/5""",
            "5": """index_of_multiple_deprivation >= 32844*4/5 AND index_of_multiple_deprivation < 32844""",
        },
        index_of_multiple_deprivation=patients.address_as_of(
            "index_date",
            returning="index_of_multiple_deprivation",
            round_to_nearest=100,
        ),
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "0": 0.05,
                    "1": 0.19,
                    "2": 0.19,
                    "3": 0.19,
                    "4": 0.19,
                    "5": 0.19,
                }
            },
        },
    ),
    ethnicity=patients.with_these_clinical_events(
        ethnicity_codes,
        returning="category",
        find_last_match_in_period=True,
        on_or_before="index_date",
        return_expectations={
            "category": {"ratios": {"1": 0.8, "5": 0.1, "3": 0.1}},
            "incidence": 0.75,
        },
    ),
    previous_covid=patients.categorised_as(
        {
            "COVID positive": """
                                (sgss_positive OR primary_care_covid)
                                AND NOT hospital_covid
                                """,
            "COVID hospitalised": "hospital_covid",
            "No COVID code": "DEFAULT",
        },
        return_expectations={
            "incidence": 1,
            "category": {
                "ratios": {
                    "COVID positive": 0.4,
                    "COVID hospitalised": 0.4,
                    "No COVID code": 0.2,
                }
            },
        },
    ),
)

clinical_variables = dict(
    bmi=patients.categorised_as(
        {
            "Not obese": "DEFAULT",
            "Obese I (30-34.9)": """ bmi_value >= 30 AND bmi_value < 35""",
            "Obese II (35-39.9)": """ bmi_value >= 35 AND bmi_value < 40""",
            "Obese III (40+)": """ bmi_value >= 40 AND bmi_value < 100""",
            # set maximum to avoid any impossibly extreme values being classified as obese
        },
        bmi_value=patients.most_recent_bmi(
            on_or_after="index_date - 60 months", minimum_age_at_measurement=16
        ),
        return_expectations={
            "rate": "universal",
            "category": {
                "ratios": {
                    "Not obese": 0.7,
                    "Obese I (30-34.9)": 0.1,
                    "Obese II (35-39.9)": 0.1,
                    "Obese III (40+)": 0.1,
                }
            },
        },
    ),
    diabetes=patients.with_these_clinical_events(
        diabetes_codes, on_or_before="index_date - 1 day"
    ),
    cancer=patients.satisfying(
        "other_cancer OR lung_cancer",
        other_cancer=patients.with_these_clinical_events(
            other_cancer_codes, on_or_before="index_date - 1 day"
        ),
        lung_cancer=patients.with_these_clinical_events(
            lung_cancer_codes, on_or_before="index_date - 1 day"
        ),
    ),
    haem_cancer=patients.with_these_clinical_events(
        haem_cancer_codes, on_or_before="index_date - 1 day"
    ),
    # egfr
    asthma=patients.categorised_as(
        {
            "0": "DEFAULT",
            "1": """
            (
              recent_asthma_code OR (
                asthma_code_ever AND NOT
                copd_code_ever
              )
            ) AND (
              prednisolone_last_year = 0 OR 
              prednisolone_last_year > 4
            )
        """,
            "2": """
            (
              recent_asthma_code OR (
                asthma_code_ever AND NOT
                copd_code_ever
              )
            ) AND
            prednisolone_last_year > 0 AND
            prednisolone_last_year < 5
            
        """,
        },
        return_expectations={
            "category": {"ratios": {"0": 0.8, "1": 0.1, "2": 0.1}},
            "incidence": 1,
        },
        recent_asthma_code=patients.with_these_clinical_events(
            asthma_codes,
            between=["index_date - 3 years", "index_date - 1 day"],
        ),
        asthma_code_ever=patients.with_these_clinical_events(asthma_codes),
        copd_code_ever=patients.with_these_clinical_events(
            chronic_respiratory_disease_codes
        ),
        prednisolone_last_year=patients.with_these_medications(
            prednisolone_codes,
            between=["index_date - 1 years", "index_date - 1 day"],
            returning="number_of_matches_in_period",
        ),
    ),
    chronic_respiratory_disease=patients.with_these_clinical_events(
        chronic_respiratory_disease_codes, on_or_before="index_date - 1 day"
    ),
    chronic_cardiac_disease=patients.with_these_clinical_events(
        chronic_cardiac_disease_codes, on_or_before="index_date - 1 day"
    ),
    # hypertension/highBP
    chronic_liver_disease=patients.with_these_clinical_events(
        chronic_liver_disease_codes, on_or_before="index_date - 1 day"
    ),
    stroke_or_dementia=patients.satisfying(
        "stroke OR dementia",
        stroke=patients.with_these_clinical_events(
            stroke_gp_codes, on_or_before="index_date - 1 day"
        ),
        dementia=patients.with_these_clinical_events(
            dementia_codes, on_or_before="index_date - 1 day"
        ),
    ),
    other_neuro=patients.with_these_clinical_events(
        other_neuro_codes, on_or_before="index_date - 1 day"
    ),
    organ_transplant=patients.with_these_clinical_events(
        organ_transplant_codes, on_or_before="index_date - 1 day"
    ),
    dysplenia=patients.with_these_clinical_events(
        spleen_codes, on_or_before="index_date - 1 day"
    ),
    ra_sle_psoriasis=patients.with_these_clinical_events(
        ra_sle_psoriasis_codes, on_or_before="index_date - 1 day"
    ),
    other_immunosuppressive_condition=patients.satisfying(
        """
           sickle_cell
        OR aplastic_anaemia
        OR hiv
        OR permanent_immunodeficiency
        OR temporary_immunodeficiency
        """,
        sickle_cell=patients.with_these_clinical_events(
            sickle_cell_codes, on_or_before="index_date - 1 day"
        ),
        aplastic_anaemia=patients.with_these_clinical_events(
            aplastic_codes, on_or_before="index_date - 1 day"
        ),
        hiv=patients.with_these_clinical_events(
            hiv_codes, on_or_before="index_date - 1 day"
        ),
        permanent_immunodeficiency=patients.with_these_clinical_events(
            permanent_immune_codes, on_or_before="index_date - 1 day"
        ),
        temporary_immunodeficiency=patients.with_these_clinical_events(
            temp_immune_codes, on_or_before="index_date - 1 day"
        ),
    ),
)
