import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from measures import measures_dict
from types import SimpleNamespace

measures = [SimpleNamespace(**measure) for measure in measures_dict]
color_cycle = ["#377eb8", "#ff7f00", "#4daf4a", "#f781bf", "#a65628", "#984ea3"]


def get_data():
    p = f"output/measure_{m.id}.csv"
    counts = pd.read_csv(p, usecols=["date", m.numerator, m.denominator] + m.group_by)
    counts["date"] = pd.to_datetime(counts["date"])
    if m.id == "all_rate":
        m.group_by = ["all"]
        counts["all"] = "All patients"
        counts = counts.groupby(["date", "all"]).sum()
    else:
        counts = counts.set_index(["date"] + m.group_by)
    return counts


def calculate_rates(df):
    rates = (df[m.numerator] / df[m.denominator]) * 100000
    return rates


def redact_small_numbers(df):
    mask_n = df[m.numerator].isin([1, 2, 3, 4, 5])
    mask_d = df[m.denominator].isin([1, 2, 3, 4, 5])
    mask = mask_n | mask_d
    df.loc[mask, :] = np.nan
    return df


def make_table():
    counts = get_data()
    rates = calculate_rates(counts)
    rates.name = "Crude rate per 100,000 population"
    df = pd.concat([counts, rates], axis=1)
    df = redact_small_numbers(df)
    df = df.unstack()
    return df


time_series = []
for m in measures:
    df = make_table()
    df.to_csv(f"output/{m.id}.csv")
    df = df.drop(columns=[m.numerator, m.denominator])
    df.columns = df.columns.droplevel()
    time_series.append(df)

fig, axes = plt.subplots(ncols=1, nrows=4, sharex=True, figsize=[10, 12])
for i, ax in enumerate(axes.flat):
    df = time_series[i]
    df.plot(ax=ax, color=color_cycle)
    ax.grid(which="both", axis="y", color="#666666", linestyle="-", alpha=0.2)
    name = "stratified by " + measures[i].group_by[0].replace("_", " ")
    title = f"{chr(97 + i)}) Long-COVID rates {name}"
    ax.set_title(title, loc="left")
    ax.xaxis.label.set_visible(False)
    ax.legend(loc=3, prop={"size": 9})
    ax.set_ylabel("Rate per 100,000 people")
    ax.set_ylim(ymin=0)
    plt.tight_layout()
plt.savefig("output/time_series_plot.svg")
