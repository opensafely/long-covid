import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common_variables import demographic_variables, clinical_variables

pd.set_option("display.max_rows", 50)
results_path = "output/practice_summ.txt"
long_covid_codelists = [
    "opensafely-nice-managing-the-long-term-effects-of-covid-19",
    "opensafely-referral-and-signposting-for-long-covid",
    "opensafely-assessment-instruments-and-outcome-measures-for-long-covid",
]
combined_codelists = [
    pd.read_csv(f"codelists/{path}.csv", index_col="code")
    for path in long_covid_codelists
]
combined_codelists = pd.concat(combined_codelists)
individual_code_dates = [f"snomed_{c}_date" for c in combined_codelists.index]


def crosstab(idx):
    cols = ["No long COVID", "Long COVID", "Rate per 100,000", "%"]
    counts = pd.crosstab(idx, df["long_covid"], normalize=False, dropna=False)
    rates = (
        pd.crosstab(idx, df["long_covid"], normalize="index", dropna=False)[1] * 100000
    ).round(1)
    percentages = (
        pd.crosstab(idx, df["long_covid"], normalize="columns", dropna=False)[1] * 100
    ).round(1)
    all_cols = pd.concat([counts, rates, percentages], axis=1)
    all_cols.columns = cols
    return all_cols


def redact_small_numbers(df, column):
    mask = df[column].isin([1, 2, 3, 4, 5])
    df.loc[mask, :] = np.nan
    return df


def write_to_file(text_to_write, erase=False):
    if erase and os.path.isfile(results_path):
        os.remove(results_path)
    with open(results_path, "a") as txt:
        txt.writelines(f"{text_to_write}\n")
        print(text_to_write)
        txt.writelines("\n")
        print("\n")


df = pd.read_csv(
    "output/input_cohort.csv",
    index_col="patient_id",
    parse_dates=[
        "first_long_covid_date",
        "sgss_positive",
        "primary_care_covid",
        "hospital_covid",
    ],
)

# Find first COVID date
first_covid_date = df[["sgss_positive", "primary_care_covid", "hospital_covid"]].min(
    axis=1
)

## Crosstabs
df["comorbidities"] = df[
    [
        "diabetes",
        "cancer",
        "haem_cancer",
        "asthma",
        "chronic_respiratory_disease",
        "chronic_cardiac_disease",
        "chronic_liver_disease",
        "stroke_or_dementia",
        "other_neuro",
        "organ_transplant",
        "dysplenia",
        "ra_sle_psoriasis",
        "other_immunosup_cond",
    ]
].sum(axis=1)
df.loc[df["comorbidities"] > 2, "comorbidities"] = 2
stratifiers = list(demographic_variables.keys()) + [
    "bmi",
    "comorbidities",
    "mental_health",
]
crosstabs = [crosstab(df[v]) for v in stratifiers]
all_together = pd.concat(
    crosstabs, axis=0, keys=stratifiers + ["imd"], names=["Attribute", "Category"]
)
print(all_together)
redact_small_numbers(all_together, "Long COVID").to_csv("output/counts_table.csv")
