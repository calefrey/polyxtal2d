from matplotlib import pyplot as plt
from sys import argv
import matplotlib.animation as ani

animation = False

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


def builddata(i):
    p = plt.plot(x_arr[:i], y_arr[:i], marker=".", color="tab:blue")
    print(f"x={x_arr[i]:.2E}, y={y_arr[i]:.2E}")
    return p


if animation:
    animator = ani.FuncAnimation(fig, builddata, frames=len(x_arr), repeat=False)
    plt.show()
else:
    plt.plot(x_arr, y_arr, marker=".", color="tab:blue")
    plt.show()
fig.savefig(f"r-curve.png")  # saves final r-curve to file
