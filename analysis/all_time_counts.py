import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.max_rows", 50)

stratifiers = ["first_long_covid_code", "sex", "age_group", "previous_covid", "region"]

df = pd.read_csv(
    "output/input_cohort.csv",
    index_col="patient_id",
    parse_dates=["first_long_covid_date"],
    # dtype={
    #     "first_long_covid_code": "category",
    #     "sex": "category",
    #     "age_group": "category",
    #     "previous_covid": "category",
    #     "practice_id": "category",
    #     "region": "category",
    # },
)


def crosstab(idx):
    cols = ["No long-covid", "Long-covid", "Rate per 100,000", "%"]
    counts = pd.crosstab(idx, df["long_covid"], normalize=False)
    rates = (pd.crosstab(idx, df["long_covid"], normalize="index")[1] * 100000).round(1)
    percentages = (
        pd.crosstab(idx, df["long_covid"], normalize="columns")[1] * 100
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
