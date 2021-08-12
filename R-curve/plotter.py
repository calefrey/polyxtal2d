from matplotlib import pyplot as plt
from sys import argv
import matplotlib.animation as ani

animation = False
name = None
lengthscale = None
# with open(argv[1], "r") as f:
with open("r-curve.txt", "r") as f:
    x_arr = []
    y_arr = []
    for line in f.readlines():
        if line.startswith("#"):
            continue
        elif line.startswith("name"):
            name = line.split("=")[1].strip()  # remove newline
            print(f"Name: {lengthscale}")
        elif line.startswith("lengthscale"):
            lengthscale = line.split("=")[1].strip()  # remove newline
            print(f"Lengthscale: {lengthscale}")
        else:
            x, y = line.split()
            x_arr.append(float(x))
            y_arr.append(float(y))

# delete data points if subsequet points have the same x-value
for i in range(1, len(x_arr) - 1):  # don't want to delete the first point
    if x_arr[i] == x_arr[i + 1]:  # look ahead
        x_arr[i] = None
        y_arr[i] = None
x_arr = [x for x in x_arr if x is not None]
y_arr = [y for y in y_arr if y is not None]

fig = plt.figure()
plt.ylabel("$K$")
plt.xlabel("$\\frac{a}{w}$")
if name and lengthscale:
    plt.title(f"{name}, length scale = {lengthscale}")


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
