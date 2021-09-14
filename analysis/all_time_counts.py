import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common_variables import demographic_variables, clinical_variables

pd.set_option("display.max_rows", 50)
results_path = "output/practice_summ.txt"
stratifiers = list(demographic_variables.keys())
long_covid_codelists = [
    "opensafely-nice-managing-the-long-term-effects-of-covid-19",
    "opensafely-referral-and-signposting-for-long-covid",
    "opensafely-assessment-instruments-and-outcome-measures-for-long-covid",
    "user-alex-walker-post-viral-syndrome",
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


def custom_round(x, base=5):
    return int(base * round(float(x) / base))


df = pd.read_csv(
    "output/input_cohort.csv",
    index_col="patient_id",
    parse_dates=[
        "first_long_covid_date",
        "first_post_viral_fatigue_date",
        "sgss_positive",
        "primary_care_covid",
        "hospital_covid",
    ]
    + individual_code_dates,
)

# Surface missing values
df["ethnicity"] = df["ethnicity"].fillna(0)
df["region"] = df["region"].fillna("AaMissing")

# Find first COVID date
first_covid_date = df[["sgss_positive", "primary_care_covid", "hospital_covid"]].min(
    axis=1
)

## Crosstabs
crosstabs = [crosstab(df[v]) for v in stratifiers]
all_together = pd.concat(
    crosstabs, axis=0, keys=stratifiers + ["imd"], names=["Attribute", "Category"]
)
print(all_together)
redact_small_numbers(all_together, "Long COVID").to_csv("output/counts_table.csv")

## All long-covid codes table
codes = [str(code) for code in combined_codelists.index]
all_codes = df.copy()
all_codes.columns = all_codes.columns.str.lstrip("snomed_")
all_codes = all_codes[codes].sum().T
all_codes = all_codes.rename("Total records")
all_codes.index = all_codes.index.astype("int64")
all_codes = combined_codelists.join(all_codes)
all_codes["%"] = (all_codes["Total records"] / all_codes["Total records"].sum()) * 100
redact_small_numbers(all_codes, "Total records").to_csv(
    "output/all_long_covid_codes.csv"
)
print(all_codes.columns)

## Descriptives by practice
by_practice = (
    df[["long_covid", "practice_id"]].groupby("practice_id").sum()["long_covid"]
)
write_to_file(f"Total patients coded: {by_practice.sum()}", erase=True)
top_10_count = by_practice.sort_values().tail(10).sum()
write_to_file(f"Patients coded in the highest 10 practices: {top_10_count}")
practice_summ = by_practice.describe()
write_to_file(f"Summary stats by practice:\n{practice_summ}")
ranges = [-1, 0, 1, 2, 3, 4, 5, 10, 10000]
practice_distribution = by_practice.groupby(pd.cut(by_practice, ranges)).count()
write_to_file(f"Distribution of coding within practices: {practice_distribution}")
practice_distribution.to_csv("output/practice_distribution.csv")


def weekly_counts(variable):
    weekly_counts = df.set_index(f"first_{variable}_date")[variable]
    weekly_counts = weekly_counts.resample("W").count()
    weekly_counts = weekly_counts.loc["2020-01-01":]
    weekly_counts = weekly_counts.apply(lambda x: custom_round(x, base=5))
    print(weekly_counts)
    weekly_counts.to_csv(f"output/code_use_per_week_{variable}.csv")


weekly_counts("long_covid")
weekly_counts("post_viral_fatigue")

## COVID to long COVID interval
def interval_until(col):
    interval = (df[col] - first_covid_date).dt.days.dropna()
    bins = [-1000, -1, 0, 28, 56, 84, 112, 140, 168, 196, 1000]
    interval = interval.groupby(pd.cut(interval, bins)).count()
    interval.loc[interval.isin([1, 2, 3, 4, 5])] = np.nan
    write_to_file(f"Timing of {col} relative to COVID:\n{interval}")
    interval.to_csv(f"output/interval_{col}.csv")


for col in ["first_long_covid_date"] + individual_code_dates[0:5]:
    interval_until(col)
