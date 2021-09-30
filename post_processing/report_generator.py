# Generates a markdown report of the simulation results
# Run in root directory of simulations (where batch template script was called)
# convert into PDF using Pandoc

from sys import argv
import datetime, os
import matplotlib.pyplot as plt
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
                plt.plot(x_arr, y_arr, label=root.strip("./\\"))
plt.ylabel("$K$")
plt.xlabel("$\\frac{a}{w}$")
plt.legend(fontsize=8)
plt.savefig("r-curves.png")

report.write("![](r-curves.png)\n\n")  # add r-curves to report


# individual run sections
for (root, dirs, files) in os.walk("."):  # loop through directories in root folder
    if root == ".":
        continue  # skip root folder
    for file in files:
        if file.endswith("job_data.json"):
            plt.figure()  # new figure for a clean slate
            data = json.load(open(os.path.join(root, file)))
            runtime = datetime.timedelta(seconds=data["runtime"])
            jobname = data["title"]
            plt.scatter(data["x_values"], data["y_values"], s=1, c="tab:red")
            plt.xlim(0, 80)
            plt.ylim(0, 80)
            plt.savefig(f"{jobname}/crack_path.png")
            report.write(
                f"""
\\newpage
Job {jobname} ran for 18:50:36

![]({jobname}/{jobname}.png){{height=4in}}

![]({jobname}/crack_path.png){{height=4in}}

Total crack length: {data["crack_path_length"]}

"""
            )

f.close()
