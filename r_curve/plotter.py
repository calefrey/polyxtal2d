from matplotlib import pyplot as plt
from sys import argv
import matplotlib.animation as ani

name = None
# with open(argv[1], "r") as f:
with open("r-curve.txt", "r") as f:
    x_arr = []
    y_arr = []
    for line in f.readlines():
        if line.startswith("#"):
            continue
        elif line.startswith("name"):
            name = line.split("=")[1].strip()  # remove newline
        else:
            x, y = line.split()
            x_arr.append(float(x))
            y_arr.append(float(y))

# # delete data points if subsequet points have the same x-value
# for i in range(1, len(x_arr) - 1):  # don't want to delete the first point
#     if x_arr[i] == x_arr[i + 1]:  # look ahead
#         x_arr[i] = None
#         y_arr[i] = None
# x_arr = [x for x in x_arr if x is not None]
# y_arr = [y for y in y_arr if y is not None]

fig = plt.figure()
plt.ylabel("$K$")
plt.xlabel("$\\frac{a}{w}$")
if name is not None:
    plt.title(name)
plt.plot(x_arr, y_arr, marker=".", color="tab:blue")
plt.show()
fig.savefig(f"r-curve.png", bbox_inches="tight")  # saves final r-curve to file
