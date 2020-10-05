lower_x = 0
lower_y = 0
upper_x = 10
upper_y = 10
distance = 0.05

from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import random

points = []
for i in range(lower_x, upper_x):
    # i = i + random.gauss(0,.5)
    for j in range(lower_y, upper_y):
        if i % 2:
            j = j + 0.5
        points.append([i, j])
        plt.plot([i],[j],'b.')

plt.axis("square")
plt.xlim(lower_x, upper_x)
plt.ylim(lower_y, upper_y)
plt.show()

vor = Voronoi(points)

#display original voronoi boundaries
fig = voronoi_plot_2d(vor)
plt.axis("square")
plt.xlim(lower_x, upper_x)
plt.ylim(lower_y, upper_y)
plt.show()

from utils import grain

grains = []
for idx, region in enumerate(vor.regions):
    if not -1 in region:
        corners = [
            vor.vertices[i] for i in region
        ]  # gets the vertices referenced by the region values
        if len(corners) == 6:  # only hexagons
            plt.fill(*zip(*corners)) #useful illustration to demonstrate the selected regions
            # center = vor.points[idx]
            grains.append(grain(corners, region, idx))
            # grains[region] = grain(corners)

plt.axis("square")
plt.xlim(lower_x, upper_x)
plt.ylim(lower_y, upper_y)
plt.show()

scaled = [g.scaled(distance=distance) for g in grains]


for grain in scaled:
    plt.fill(*zip(*grain.vertices))
    


plt.axis("square")
plt.xlim(lower_x, upper_x)
plt.ylim(lower_y, upper_y)
plt.show()