from matplotlib import pyplot as plt
from sys import argv
import matplotlib.animation as ani


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

fig = plt.figure()
plt.ylabel("$K_I$")
plt.xlabel("$\\frac{a}{w}$")
axes = plt.gca()

axes.xaxis.label.set_size(14)

axes.yaxis.label.set_size(14)


def builddata(i):
    p = plt.plot(x_arr[:i], y_arr[:i], marker=".", color="tab:blue")
    print(f"x={x_arr[i]:.2E}, y={y_arr[i]:.2E}")
    return p


animator = ani.FuncAnimation(fig, builddata, frames=len(x_arr), repeat=False)
plt.show()
fig.savefig(f"r-curve.png")  # saves final r-curve to file
