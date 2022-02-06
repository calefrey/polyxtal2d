# For batches with multiple varying paramters, grsphs that show all r-curves are too messy to illustrate results
# This code should go through and combine all r-curves for each replicate set

# regular expression to extract simulation parameters from name and sort them appropriately
from collections import defaultdict
from matplotlib import pyplot as plt
import numpy as np
import os, re

sorting_func = lambda s: [float(x) for x in re.findall(r"(\d*\.?\d*e[+-]?\d+)", s)]

extrat_base_name = lambda s: re.findall(r"(.*\/)?(.*)(_seed_\d{4})", s)[-1][1]
# this splits the folder name into 3 parts: the parent directory, the base name, and the seed ID.
# We want the base name so take the [1] elemeent of the finall result


all_data = {}  # {sim_name: (x_array, y_array)}
replocate_data = defaultdict(dict)  # {sim_base_name: {sim_name: (x_array, y_array)}}
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
                all_data[root.strip("./\\")] = (x_arr, y_arr)  # save data for later
                print(root)
                sim_base_name = extrat_base_name(root)
                replocate_data[sim_base_name][root.strip("./\\")] = (
                    x_arr,
                    y_arr,
                )  # replicate sets

# make an average plot using "binning" technique
bins = np.linspace(0, 1, 50)

# need to interpolate the data first
interpolated_data = {}
for base_name, data in replocate_data.items():
    for sim_name, (x_arr, y_arr) in data.items():
        try:
            interp_y_arr = [np.interp(x, x_arr, y_arr) for x in bins]
        except ValueError:
            print(f"{sim_name}: {x_arr}, {y_arr}")
        interpolated_data[sim_name] = (bins, interp_y_arr)

    mean_y_arr = []
    for i in range(len(bins)):
        bin_y_arr = []
        for sim_name, (x_arr, y_arr) in interpolated_data.items():
            bin_y_arr.append(y_arr[i])  # get the values for each simulation in the bin
        mean_y_arr.append(np.mean(bin_y_arr))
    plt.plot(bins, mean_y_arr, label=base_name)

plt.ylabel("$K$")
plt.xlabel("$\\frac{a}{w}$")
plt.ylim(bottom=0)
plt.legend(fontsize=8)
plt.savefig("r-curves.png")
