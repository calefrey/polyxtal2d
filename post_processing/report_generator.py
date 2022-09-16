# Generates a markdown report of the simulation results
# Run in root directory of simulations (where batch template script was called)
# convert into PDF using Pandoc

from sys import argv
import datetime, os
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json, re, time

# regular expression to extract simulation parameters from name and sort them appropriately
sorting_func = lambda s: [float(x) for x in re.findall(r"(\d*\.?\d*e[+-]?\d+)", s)]

report_name = argv[1]

report = open(report_name + ".md", "w")
report.write(
    f"""
---
title: {report_name}
date: {datetime.date.today()}
author: Caleb Frey
geometry: margin=2cm
---
"""
)

report.write("![](quantified.png\n\n")

# individual run sections


def atof(text):
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


bigdf = pd.DataFrame()  # big dataframe for all data
sorting_func = lambda s: [float(x) for x in re.findall(r"\/(\d+.\d+)", s)]
for (root, dirs, files) in os.walk("."):  # loop through directories in root folder
    dirs.sort(
        key=lambda s: [
            atof(c) for c in re.split(r"[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)", s)
        ]
    )
    if root == ".":
        continue  # skip root folder

    for file in files:
        if file.endswith("job_data.json"):
            print(root)
            data = json.load(open(os.path.join(root, file)))
            node_lut = json.load(open(os.path.join(root, "node_lut.json")))
            jobname = data["title"]
            fig = go.Figure()
            runtime = datetime.timedelta(seconds=data["runtime"])
            if not data["x_values"]:
                report.write(f"{jobname} ran for {runtime} but yielded no results\n\n")
                print("Skipping")
                continue  # skip to next job
            report.write(
                f"""
\\newpage
Job {jobname} ran for {runtime}

"""
            )
            df = pd.DataFrame()
            a_min = min(data["x_values"])
            df["y"] = data["y_values"]
            df["a"] = [x - a_min for x in data["x_values"]]
            df["Node ID"] = data["node_ids"]
            toughness = []
            for node_id in data["node_ids"]:
                strength, displacement = node_lut.get(node_id, node_lut["default"])
                toughness.append(0.5 * float(strength) * float(displacement))
            df["toughness"] = toughness
            df["CSDMG"] = data["dmg_values"]
            df["mesh_size"] = data["mesh_size"]
            df["weighted_toughness"] = np.where(
                df["CSDMG"] > 0.95, df["toughness"] * df["CSDMG"] * df["mesh_size"], 0
            )
            df.sort_values(by=["a"], inplace=True)
            df["sum_tough"] = df["weighted_toughness"].cumsum()
            df["approx_tough"] = df["sum_tough"] / np.where(df["a"] > 1, df["a"], 1)
            default_toughness = (
                0.5 * float(node_lut["default"][0]) * float(node_lut["default"][1])
            )
            df["normalized_tough"] = [t / default_toughness for t in df["approx_tough"]]

            plt.figure()
            plt.scatter(
                data["x_values"],
                data["y_values"],
                s=1,
                c=data["dmg_values"],
                cmap=cm.turbo,
            )
            cbar = plt.colorbar()
            cbar.set_label("CSDMG", labelpad=10, rotation=270)
            plt.xlim(0, 80)
            plt.ylim(0, 80)
            plt.savefig(os.path.join(root, "crack.png"))
            plt.close()
            report.write(f"![]({root}/crack.png){{height=4in}}\n\n")

            fig = go.Figure()
            group_name = "_".join(data["title"].split("_")[:-2])
            fig.add_trace(
                go.Scatter(
                    x=df["a"],
                    y=df["normalized_tough"],
                    mode="lines",
                    legendgroup=group_name,
                    legendgrouptitle_text=group_name,
                    name=jobname,
                    hovertext=jobname
                    # hovertemplate="Job: %{customdata[0]}<br>" + "%{x:.3f}<br>%{y:.3f}",
                )
            )
            fig.update_xaxes(title_text="Crack length")
            fig.update_yaxes(title_text="Normalized Toughness")

            jobname = data["title"]

            df = df.assign(group=group_name)
            bigdf = bigdf.append(
                df[["a", "normalized_tough", "group"]], ignore_index=True
            )
            fig.write_image(os.path.join(root, "toughening.png"))
            report.write(f"![]({root}/toughening.png){{height=4in}}\n\n")

avgdf = pd.DataFrame()
c = dict(
    zip(
        bigdf["group"].unique(),
        px.colors.qualitative.Plotly + px.colors.qualitative.Alphabet,
    )
)  # map
text = ["<br>".join(group.split("_")) for group in bigdf["group"].unique()]
for group in bigdf["group"].unique():
    groupdata = bigdf[bigdf["group"] == group]
    bins = np.linspace(0, 80, 20)
    for bin in bins:
        binned = groupdata[(bin <= groupdata["a"]) & (groupdata["a"] < bin + 4)]
        if len(binned) == 0:
            continue

        avgdf = avgdf.append(
            {
                "a": bin,
                "group": group,
                "avg": binned["normalized_tough"].mean(),
                "max": binned["normalized_tough"].max(),
                "min": binned["normalized_tough"].min(),
            },
            ignore_index=True,
        )

bigdf.to_csv("bigdf.csv")
avgdf.to_csv("avgdf.csv")

avgdf = pd.DataFrame()

re_str = (
    r"mod_(?P<mod>(?:\d+_)*\d+e[+-]\d+)"
    r"_str_ratio_(?P<strength>(?:\d+_)*\d+e[+-]\d+)"
    r"(?:_tough_ratio_(?P<toughness>(?:\d+_)*\d+e[+-]\d+))*"
)

for group in bigdf["group"].unique():
    groupdata = bigdf[bigdf["group"] == group]
    bins = np.linspace(0, 80, 20)
    for bin in bins:
        binned = groupdata[(bin < groupdata["a"]) & (groupdata["a"] < bin + 4)]
        if len(binned) == 0:
            continue

        avgdf = avgdf.append(
            {
                "a": bin,
                "group": group,
                "avg": binned["normalized_tough"].mean(),
                "max": binned["normalized_tough"].max(),
                "min": binned["normalized_tough"].min(),
            },
            ignore_index=True,
        )

    # plot filled area lines
avgdf["mod"] = avgdf.group.apply(lambda s: re.match(re_str, s).group("mod"))
avgdf["strength"] = avgdf.group.apply(lambda s: re.match(re_str, s).group("strength"))
avgdf["toughness"] = avgdf.group.apply(lambda s: re.match(re_str, s).group("toughness"))
avgdf.strength = avgdf.strength.apply(lambda s: float(re.sub("_", ".", s)))
avgdf.toughness = avgdf.toughness.apply(lambda s: float(re.sub("_", ".", s)))
avgdf["mod"] = avgdf["mod"].apply(lambda s: float(re.sub("_", ".", s)))

fig = px.line(
    avgdf,
    x="a",
    y="avg",
    facet_col="toughness",
    facet_col_wrap=2,
    color="group",
    labels={
        "a": "Crack Length",
        "avg": "Normalized Toughness",
        "toughness": "Toughness Ratio",
        "strength": "Strength Ratio",
    },
)
fig.update_layout(showlegend=False)
fig.write_html("curves.html")
fig.write_image("curves.png", scale=5)


quantified = pd.DataFrame()
quantified["group"] = avgdf["group"].unique()
quantified["mod"] = [
    float(re.match(re_str, group).group("mod")) for group in avgdf["group"].unique()
]
quantified["strength"] = [
    re.match(re_str, group).group("strength") for group in avgdf["group"].unique()
]
quantified.strength = quantified.strength.apply(lambda s: float(re.sub("_", ".", s)))
quantified["toughness"] = [
    re.match(re_str, group).group("toughness") for group in avgdf["group"].unique()
]
quantified.toughness = quantified.toughness.apply(lambda s: float(re.sub("_", ".", s)))
quantified["avg"] = [
    avgdf[(avgdf.group == group) & (20 < avgdf.a) & (avgdf.a < 50)]["avg"].mean()
    for group in avgdf["group"].unique()
]
quantified["stdev"] = [
    avgdf[(avgdf.group == group) & (20 < avgdf.a) & (avgdf.a < 50)]["avg"].std()
    for group in avgdf["group"].unique()
]

quantified.sort_values("mod", inplace=True)
quantified["mod"] = quantified["mod"].astype(str)  # categorical
fig = px.scatter(
    quantified,
    x="toughness",
    y="avg",
    error_y="stdev",  # error bars
    # facet_row="strength",
    facet_col="strength",
    hover_name="group",
    hover_data=["mod", "strength", "toughness"],
    color="mod",
    symbol="mod",
    symbol_sequence=[
        "circle",
        "square",
        "diamond",
        "star",
        "triangle-up",
        "triangle-down",
        "cross",
        "x",
    ],
    labels={
        "strength": "Strength Ratio",
        "toughness": "Toughness Ratio",
        "avg": "Average Toughness",
        "mod": "Modifier Probability",
    },
)
fig.update_traces(marker={"size": 10, "opacity": 0.8})

fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        # y=-0.25,
        y=1.05,
        xanchor="left",
        x=0.3,
    )
)


fig.write_html("quantified.html")
fig.write_image("quantified.png", scale=5, width=1000)


report.close()
