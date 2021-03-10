import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.max_rows", 50)

stratifiers = ["sex", "age_group", "previous_covid", "region"]
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

df = pd.read_csv(
    "output/input_cohort.csv",
    index_col="patient_id",
    parse_dates=["first_long_covid_date"],
)


def crosstab(idx):
    cols = ["No long-covid", "Long-covid", "Rate per 100,000", "%"]
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


crosstabs = [crosstab(df[v]) for v in stratifiers]
imd = crosstab((pd.qcut(df["imd"], 5)))
crosstabs = crosstabs + [imd]
all_together = pd.concat(
    crosstabs, axis=0, keys=stratifiers + ["imd"], names=["Attribute", "Category"]
)
print(all_together)
all_together.to_csv("output/counts_table.csv")

practice_summ = (
    df[["long_covid", "practice_id"]].groupby("practice_id").sum().describe()
)
print(practice_summ)
practice_summ.to_csv("output/practice_summ.csv")

first_long_covid_code = crosstab(df["first_long_covid_code"])
first_long_covid_code = combined_codelists.join(first_long_covid_code)
first_long_covid_code.to_csv("output/first_long_covid_code.csv")
print(first_long_covid_code)
