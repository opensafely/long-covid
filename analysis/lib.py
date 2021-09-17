import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from IPython.display import display


# Counts over time graph
def line_format(label):
    return label.strftime("%Y-%m-%d")


def generic_graph_settings(ax, title):
    xlim = ax.get_xlim()
    ax.grid(b=False)
    ax.set_title(title, loc="left")
    ax.set_xlim(xlim)
    ax.set_ylim(ymin=0)
    plt.tight_layout()


def code_use_per_week_graph():
    week_df = pd.read_csv(
        "../released_outputs/output/code_use_per_week_long_covid.csv",
        index_col="first_long_covid_date",
        parse_dates=["first_long_covid_date"],
    )
    week_df = week_df.rename(columns={"long_covid": "TPP"})
    week_emis = pd.read_csv(
        "../released_outputs/emis/code_use_per_week_long_covid.csv",
        index_col="first_long_covid_date",
        parse_dates=["first_long_covid_date"],
    )
    week_emis = week_emis.rename(columns={"long_covid": "EMIS"})
    week_total = pd.concat([week_df, week_emis], axis=1)

    to_plot = week_total["2020-11-15":]
    to_plot = to_plot.loc[: "2021-09-04"] # datetime.today()]
    # print(to_plot)

    ax = to_plot.plot(kind="bar", width=0.8, figsize=(10, 6))
    title = "Code use per week"
    ax.set_xticklabels(map(line_format, to_plot.index))
    ax.xaxis.label.set_visible(False)
    ax.set_ylabel("Count")
    generic_graph_settings(ax, title)
    plt.savefig("../output/code_use_per_week.svg")
    plt.show()
    plt.close()


def practice_distribution_graph():
    ## Practice
    practice_df = pd.read_csv(
        "../released_outputs/output/practice_distribution.csv", index_col="long_covid"
    )
    practice_df = practice_df.rename(columns={"long_covid.1": "TPP"})
    practice_df = (practice_df / practice_df.sum()) * 100
    practice_emis = pd.read_csv(
        "../released_outputs/emis/practice_distribution.csv", index_col="long_covid"
    )
    practice_emis = practice_emis.rename(columns={"long_covid.1": "EMIS"})
    practice_emis = (practice_emis / practice_emis.sum()) * 100
    practice_total = pd.concat([practice_df, practice_emis], axis=1)
    ax = practice_total.plot(kind="bar", width=0.8, figsize=(8, 6))
    title = "Distribution of code use amongst practices"
    ax.set_xlabel("Total number of long COVID codes recorded in each practice")
    ax.set_xticklabels(["0", "1", "2", "3", "4", "5", "6-10", "11+"])
    ax.set_ylabel("Percentage of practices")
    generic_graph_settings(ax, title)
    plt.savefig("../output/practice_distribution.svg")
    plt.show()
    plt.close()
    # print(practice_total)


def counts_table_read(folder):
    df = pd.read_csv(
        f"../released_outputs/{folder}/counts_table.csv",
        index_col=["Attribute", "Category"],
    )
    return df


def add_cols(df):
    return df["No long COVID"] + df["Long COVID"]


def get_percentages(df, col_name):
    percent = df.groupby(level=0).apply(lambda x: ((x / x.sum()) * 100).round(1))
    return pd.concat([df, percent], keys=[col_name, "%"], axis=1)


def rename_index_categories(df, attribute, replacement_dict):
    index = df.index.values
    for old, new in replacement_dict.items():
        for i, item in enumerate(index):
            if item == (attribute, old):
                index[i] = (attribute, new)
    df.index = pd.MultiIndex.from_tuples(index)
    return df


def tpp_emis_table_format(folder, renaming):
    df = counts_table_read(folder)
    df = df.rename(index=renaming)
    high_level_ethnicities = {
        "1": "White",
        "2": "Mixed",
        "3": "South Asian",
        "4": "Black",
        "5": "Other",
    }
    imd_categories = {"1": "Most deprived 1", "5": "Least deprived 5"}
    region_categories = {"East": "East of England"}
    df = rename_index_categories(df, "ethnicity", high_level_ethnicities)
    df = rename_index_categories(df, "imd", imd_categories)
    df = rename_index_categories(df, "region", region_categories)
    return df


def get_table_1(table_list):
    all_patients = [add_cols(df) for df in table_list]
    table_1 = [get_percentages(df, "Patient count") for df in all_patients]
    table_1[0]["sort_col"] = range(0, len(table_1[0]))
    table_1 = pd.concat(table_1, keys=["TPP", "EMIS", "Totals"], axis=1, join="inner")
    table_1 = table_1.sort_values(by=[("TPP", "sort_col")])
    table_1 = table_1.drop(columns=("TPP", "sort_col"))
    # .swaplevel(0,1,axis=1).sort_index(level=0, axis=1)
    table_1.loc[:, (slice(None), "Patient count")] = table_1.loc[
        :, (slice(None), "Patient count")
    ].astype(int)
    total = table_1.loc["sex"].sum(numeric_only=True)
    return total, table_1


def get_table_2(table_list):
    all_patients = [add_cols(df) for df in table_list]
    table_2 = [df.drop(columns="No long COVID") for df in table_list]
    table_2[2] = get_percentages(table_2[2], "Long COVID")
    table_2[2].columns = table_2[2].columns.droplevel(1)
    table_2[2]["Rate per 100,000"] = (
        (table_2[2]["Long COVID"] / all_patients[2]) * 100000
    ).round(1)
    table_2[0]["sort_col"] = range(0, len(table_2[0]))
    table_2 = pd.concat(table_2, keys=["TPP", "EMIS", "Totals"], axis=1, join="inner")
    table_2 = table_2.sort_values(by=[("TPP", "sort_col")])
    table_2 = table_2.drop(columns=("TPP", "sort_col"))
    # .swaplevel(0,1,axis=1).sort_index(level=0, axis=1)
    table_2.loc[:, (slice(None), "Long COVID")] = table_2.loc[
        :, (slice(None), "Long COVID")
    ].astype(int)
    total = table_2.loc["sex"].sum(numeric_only=True)
    return total, table_2  # .style.format('{:,}')


def read_codes_table(folder):
    df = pd.read_csv(
        f"../released_outputs/{folder}/all_long_covid_codes.csv", index_col="code"
    )
    return df


def smoosh_codes_tables():
    tpp = read_codes_table("output")
    emis = read_codes_table("emis")
    tpp["term"].update(emis["term"])
    terms = tpp["term"]
    tpp = tpp[["Total records"]]
    emis = emis[["Total records"]]
    total = tpp + emis
    table_list = [tpp, emis, total]
    tables = []
    for table in table_list:
        table = table.drop(table.tail(3).index)
        table["%"] = (table["Total records"] / table["Total records"].sum()) * 100
        tables.append(table)
    combined = pd.concat(
        [terms] + tables,
        keys=["", "TPP", "EMIS", "Total"],
        axis=1,
        join="inner",
    )
    total = combined.sum(numeric_only=True)
    return total, combined  # .set_index(pd.Index(combined["term"]))
