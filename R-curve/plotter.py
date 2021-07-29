from matplotlib import pyplot as plt
from sys import argv
import addcopyfighandler  # so we can copy figure to clipboard

# with open(argv[1], "r") as f:
with open("r-curve.txt", "r") as f:
    x_arr = []
    y_arr = []
    for line in f.readlines():
        if line.startswith("#"):
            continue
        else:
            x, y = line.split()
            x_arr.append(float(x))
            y_arr.append(float(y))
            print(f"x={x}, y={y}")

    plt.plot(x_arr, y_arr)
    plt.ylabel("$K_I$")
    plt.xlabel("$\\frac{a}{w}$")
    axes = plt.gca()

    axes.xaxis.label.set_size(14)

    axes.yaxis.label.set_size(14)
plt.show()
