# Generates a markdown report of the simulation results
# Run in root directory of simulations (where batch template script was called)
# convert into PDF using Pandoc

from sys import argv
import datetime, os
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import json


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
for (root, dirs, files) in os.walk("."):
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
                plt.plot(x_arr, y_arr, marker=".", label=root.strip("./\\"))
plt.ylabel("$K$")
plt.xlabel("$\\frac{a}{w}$")
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
    if root == ".":
        continue  # skip root folder
    for file in files:
        if file.endswith("job_data.json"):
            print(root)
            data = json.load(open(os.path.join(root, file)))
            jobname = data["title"]
            runtime = datetime.timedelta(seconds=data["runtime"])
            report.write(
                f"""
\\newpage
Job {jobname} ran for {runtime}

![]({jobname}/{jobname}.png){{height=4in}}\n
"""
            )
            if not data["x_values"]:
                report.write("No data to plot\n\n")
                continue  # skip to next job
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
            plt.savefig(f"{jobname}/crack_path.png")
            report.write(f"![]({jobname}/crack_path.png){{height=4in}}\n\n")

            plt.figure()
            # R curve toughening plot
            a_values = []
            area_vals = []
            prev_area = 0
            for a in np.arange(0, 80, 1):
                node_damage = 0  # total damage normalized to node size
                for i in range(len(data["x_values"])):
                    if data["x_values"][i] <= a:
                        node_damage += data["dmg_values"][i]

                cracked_area = node_damage * data["mesh_size"] * 2
                # number of failed nodes times node length times 2 sides of the crack
                if cracked_area > 0 and cracked_area != prev_area:
                    # there is a cracked area and it's different than the last one
                    a_values.append(a)
                    area_vals.append(cracked_area)
                    prev_area = cracked_area
            plt.scatter(a_values, area_vals, s=10)
            # np.polynomial.set_default_printstyle("unicode")
            plt.plot(
                a_values,
                [2 * a for a in a_values],
                "r--",
                label="No toughening (y=2x)",
            )  # area double the length if no toughening

            # do some curve fitting
            fit = np.poly1d(np.polyfit(a_values, area_vals, 1))
            fity = [fit(x) for x in a_values]
            plt.plot(a_values, fity, "--", label="Curve fit")
            plt.text(25, 10, poly2latex(fit))
            dA_da = fit.deriv()(40)  # toughness at midpoint
            toughness_R = dA_da * data["toughness"]  # effective toughness

            plt.legend()
            plt.savefig(f"{jobname}/toughening.png")
            report.write(f"![]({jobname}/toughening.png){{height=4in}}\n\n")
            report.write(f"* Total damage: {cracked_area}\n\n")
            report.write(f"* Effective toughness: {toughness_R}\n\n")

report.close()
