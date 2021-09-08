import os
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common_variables import demographic_variables, clinical_variables

pd.set_option("display.max_rows", 50)
results_path = "output/practice_summ.txt"
stratifiers = list(demographic_variables.keys()) + ["RGN11NM"]

# drop "other" ethnicity variables from stratifiers
for i in [
    "non_eth2001_dat",
    "eth_notgiptref_dat",
    "eth_notstated_dat",
    "eth_norecord_dat",
]:
    stratifiers.remove(i)

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


def add_ethnicity(cohort):
    """Add ethnicity using bandings from PRIMIS spec."""

    # eth2001 already indicates whether a patient is in any of bands 1-16
    s = cohort["ethnicity"].copy()
    s = s.cat.add_categories(6)

    # Add band 17 (Patients with any other ethnicity code)
    s.mask(s.isna() & cohort["non_eth2001_dat"].notna(), 6, inplace=True)

    # Add band 18 (Ethnicity not given - patient refused)
    s.mask(s.isna() & cohort["eth_notgiptref_dat"].notna(), 6, inplace=True)

    # Add band 19 (Ethnicity not stated)
    s.mask(s.isna() & cohort["eth_notstated_dat"].notna(), 6, inplace=True)

    # Add band 20 (Ethnicity not recorded)
    s.mask(s.isna(), 6, inplace=True)

    cohort["ethnicity"] = s.astype("int8")


df = pd.read_feather("output/input_cohort.feather")

# Add "unknown" ethnicities
add_ethnicity(df)
df = df.drop(
    ["non_eth2001_dat", "eth_notgiptref_dat", "eth_notstated_dat", "eth_norecord_dat"],
    axis=1,
)


for v in ["first_long_covid_date", "first_post_viral_fatigue_date"]:
    df[v] = df[v].astype("datetime64")
## Map region from MSOA
df = df.merge(
    msoa_to_region, how="left", left_on="msoa", right_on="MSOA11CD", copy=False
)
if df["long_covid"].nunique() == 1:
    df["long_covid"][0] = False
# Surface missing values
# df["ethnicity"] = df["ethnicity"].cat.add_categories(0)
# df["ethnicity"] = df["ethnicity"].fillna(0)
df["RGN11NM"] = df["RGN11NM"].cat.add_categories("Missing")
df["RGN11NM"] = df["RGN11NM"].fillna("Missing")
df.loc[df["RGN11NM"] == "Scotland", "RGN11NM"] = "Missing"
df.loc[df["RGN11NM"] == "Wales", "RGN11NM"] = "Missing"

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
