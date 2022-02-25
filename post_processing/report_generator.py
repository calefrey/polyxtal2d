# Generates a markdown report of the simulation results
# Run in root directory of simulations (where batch template script was called)
# convert into PDF using Pandoc

from sys import argv
import datetime, os
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import json
import re
import time

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
# all r-curves in one plot
all_data = {}  # {sim_name: (x_array, y_array)}
for (root, dirs, files) in os.walk("."):
    dirs.sort(key=sorting_func)  # sort the directories
    for file in files:
        if file.endswith("r-curve.txt"):  # only want r-curve files
            filepath = os.path.join(root, file)
            with open(filepath, "r") as f:
                x_arr = []
                y_arr = []
                for line in f.readlines():
                    try:
                        x, y = line.split()
                        x_arr.append(float(x))
                        y_arr.append(float(y))
                    except ValueError:
                        continue
                plt.plot(x_arr, y_arr, marker=".", label=root.strip("./\\"), alpha=0.5)
                all_data[root.strip("./\\")] = (x_arr, y_arr)  # save data for later
# make an average plot using "binning" technique
bins = np.linspace(0, 1, 50)

# need to interpolate the data first
interpolated_data = {}
for sim_name, (x_arr, y_arr) in all_data.items():
    try:
        interp_y_arr = [np.interp(x, x_arr, y_arr) for x in bins]
        interpolated_data[sim_name] = (bins, interp_y_arr)
    except ValueError:
        print(f"{sim_name} has no data for interpolation")

mean_y_arr = []
for i in range(len(bins)):
    bin_y_arr = []
    for sim_name, (x_arr, y_arr) in interpolated_data.items():
        bin_y_arr.append(y_arr[i])  # get the values for each simulation in the bin
    mean_y_arr.append(np.mean(bin_y_arr))

plt.plot(bins, mean_y_arr, label="Average", color="black")
plt.ylabel("$K$")
plt.xlabel("$\\frac{a}{w}$")
plt.ylim(bottom=0)
plt.legend(fontsize=8)
plt.savefig("r-curves.png")

report.write("![](r-curves.png)\n\n")  # add r-curves to report


def poly2latex(poly: np.poly1d):
    poly_str = ""
    for i in range(len(poly.coeffs)):
        if poly.order - i == 0:
            poly_str += f"{poly.coeffs[i]:.3f}"
        elif poly.order - i == 1:
            poly_str += f"{poly.coeffs[i]:.3f}x + "
        else:
            poly_str += f"{poly.coeffs[i]:.3f}x^{poly.order - i} + "
    return "$" + poly_str + "$"


# individual run sections
for (root, dirs, files) in os.walk("."):  # loop through directories in root folder
    dirs.sort(key=sorting_func)  # sort the directories
    if root == ".":
        continue  # skip root folder
    for file in files:
        if file.endswith("job_data.json"):
            print(root)
            data = json.load(open(os.path.join(root, file)))
            jobname = data["title"]
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
            plt.figure()  # new figure for a clean slate
            try:  # plot all nodes with any damage, with color corresponding to damage
                plt.scatter(
                    data["x_values"],
                    data["y_values"],
                    s=1,
                    c=data["dmg_values"],
                    cmap=cm.turbo,
                )
                cbar = plt.colorbar()
                cbar.set_label("CSDMG", labelpad=10, rotation=270)
            except KeyError:  # if there is no damage data saved - only fully damaged nodes saved
                plt.scatter(data["x_values"], data["y_values"], s=1, c="tab:red")
            plt.xlim(0, 80)
            plt.ylim(0, 80)
            plt.savefig(f"{root}/crack_path.png")
            report.write(f"![]({root}/crack_path.png){{height=4in}}\n\n")

            plt.figure()
            # R curve toughening plot
            a_values = []
            a_min = min(data["x_values"])
            toughness_vals = []
            prev_area = 0
            break_flag = False
            try:
                node_lut = json.load(open(os.path.join(root, "node_lut.json")))

            except FileNotFoundError:
                print("No node_lut.json found")
                continue

            for a in np.arange(0, 80, 1):
                # print(f"Toughness at a={a} of 80")
                total_node_toughness = 0
                for i in range(len(data["x_values"])):
                    if data["x_values"][i] <= a:
                        if (
                            data["dmg_values"][i] > 0.95
                        ):  # only include significantly damaged nodes
                            node_id = data["node_ids"][i]
                            try:
                                strength, displacement = node_lut[node_id]
                                total_node_toughness += (
                                    0.5 * float(strength) * float(displacement)
                                )
                            except KeyError:  # default property
                                strength, displacement = node_lut["default"]
                                total_node_toughness += (
                                    0.5 * float(strength) * float(displacement)
                                )
                if total_node_toughness > 0:  # only plot if there is any damage
                    a_values.append(a)
                    toughness = total_node_toughness * data["mesh_size"]
                    toughness_vals.append(total_node_toughness / (a - a_min))
            plt.scatter(a_values, toughness_vals, s=10)

            # do some curve fitting
            try:
                fit = np.poly1d(np.polyfit(a_values, toughness_vals, 1))
                fity = [fit(x) for x in a_values]
                plt.plot(a_values, fity, "--", label="Curve fit")
                plt.text(25, 10, poly2latex(fit))
            except TypeError as e:
                print(e)
                plt.text(25, 10, "No data")
            plt.legend()
            plt.savefig(f"{root}/toughening.png")
            report.write(f"![]({root}/toughening.png){{height=4in}}\n\n")

report.close()
