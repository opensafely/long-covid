import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
    week_tpp = pd.read_csv(
        "../released_outputs/output/code_use_per_week_long_covid.csv",
        index_col="first_long_covid_date",
        parse_dates=["first_long_covid_date"],
    )
    week_tpp = week_tpp.rename(columns={"long_covid": "TPP"})
    week_emis = pd.read_csv(
        "../released_outputs/emis/code_use_per_week_long_covid.csv",
        index_col="first_long_covid_date",
        parse_dates=["first_long_covid_date"],
    )
    week_emis = week_emis.rename(columns={"long_covid": "EMIS"})
    week_total = pd.concat([week_tpp, week_emis], axis=1)

    to_plot = week_total["2020-11-15":]
    # print(to_plot)

    ax = to_plot.plot(kind="bar", width=0.8)
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
    practice_tpp = pd.read_csv(
        "../released_outputs/output/practice_distribution.csv", index_col="long_covid"
    )
    practice_tpp = practice_tpp.rename(columns={"long_covid.1": "TPP"})
    practice_tpp = (practice_tpp / practice_tpp.sum()) * 100
    practice_emis = pd.read_csv(
        "../released_outputs/emis/practice_distribution.csv", index_col="long_covid"
    )
    practice_emis = practice_emis.rename(columns={"long_covid.1": "EMIS"})
    practice_emis = (practice_emis / practice_emis.sum()) * 100
    practice_total = pd.concat([practice_tpp, practice_emis], axis=1)
    ax = practice_total.plot(kind="bar", width=0.8)
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


def get_percentages(df):
    percent = df.groupby(level=0).apply(lambda x: (x / x.sum()).round(2))
    return pd.concat([df, percent], keys=["Patient count", "%"], axis=1)
