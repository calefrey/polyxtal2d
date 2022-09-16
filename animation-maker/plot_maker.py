from matplotlib import pyplot as plt
from matplotlib import cm
import numpy as np
import json
from sys import argv

label = argv[1]

data = json.load(open("data.json", "r"))
for frame in data.keys():
    print(f"Plotting frame {frame}")
    plt.figure()
    x_arr = data[frame]["x"]
    y_arr = data[frame]["y"]
    values = data[frame]["data"]
    plt.scatter(
        x_arr,
        y_arr,
        s=1,
        c=values,
        cmap=cm.turbo,
    )
    cbar = plt.colorbar()
    cbar.set_label(label, labelpad=10, rotation=270)
    plt.xlim(0, 80)
    plt.ylim(0, 80)
    plt.savefig(f"frame_{frame}.png")
    plt.close()
