import os
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common_variables import demographic_variables, clinical_variables

pd.set_option("display.max_rows", 50)
results_path = "output/practice_summ.txt"
stratifiers = list(demographic_variables.keys()) + ["RGN11NM"]
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
## ONS MSOA to region map from here:
## https://geoportal.statistics.gov.uk/datasets/fe6c55f0924b4734adf1cf7104a0173e_0/data
msoa_to_region = pd.read_csv(
    "analysis/ONS_MSOA_to_region_map.csv",
    usecols=["MSOA11CD", "RGN11NM"],
    dtype={"MSOA11CD": "category", "RGN11NM": "category"},
)


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
    all_cols.index = all_cols.index.astype(str)
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


df = pd.read_feather("output/input_cohort.feather")
for v in ["first_long_covid_date", "first_post_viral_fatigue_date"]:
    df[v] = df[v].astype("datetime64")
## Map region from MSOA
df = df.merge(
    msoa_to_region, how="left", left_on="msoa", right_on="MSOA11CD", copy=False
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
all_codes = df
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
    weekly_counts.loc[weekly_counts.isin([1, 2, 3, 4, 5])] = np.nan
    print(weekly_counts)
    weekly_counts.to_csv(f"output/code_use_per_week_{variable}.csv")


weekly_counts("long_covid")
weekly_counts("post_viral_fatigue")
