upper_x = 14
upper_y = 14
distance = 0.05

from utils.abaqus_macro_writer import line_writer
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import random, os

points = []
for i in range(0, upper_x):
    # i = i + random.gauss(0,.5)
    for j in range(0, upper_y):
        if i % 2:
            j = j + 0.5
        points.append([i, j])
        plt.plot([i], [j], "b.")

plt.axis("square")
plt.xlim(0, upper_x)
plt.ylim(0, upper_y)
plt.show()

vor = Voronoi(points)

# display original voronoi boundaries
fig = voronoi_plot_2d(vor)
plt.axis("square")
plt.xlim(0, upper_x)
plt.ylim(0, upper_y)
plt.show()

from utils.abaqus_macro_writer import (
    polygon_writer,
    initialize,
    process_lines,
    set_assigner,
)
from utils.bisector_scaling import scale as bisector_scale
from collections import defaultdict

vertex_array = defaultdict(list)  # dict of lists
grain_array = defaultdict(list)
grain_centers = {}
for r_idx, region in enumerate(vor.regions):
    if not -1 in region and len(region) == 6:  # bounded with 6 sides
        for i in range(2, len(region) + 2):
            i = i % len(region)  # wrap around
            vertex_id = region[i - 1]
            p1 = vor.vertices[region[i - 2]]  # neighboring point on the grain
            p2 = vor.vertices[vertex_id]  # point we're interested in
            p3 = vor.vertices[region[i]]  # other neighboring point
            new_point = bisector_scale(p1, p2, p3, distance)
            vertex_array[vertex_id].append(
                new_point
            )  # {vertex_id:{grain_id: [new_point.x, new_point.y]}}
            grain_array[r_idx].append(new_point)  # {grain_id:[point1]}
        centerx = sum([vor.vertices[p][0] for p in region]) / 6
        centery = sum([vor.vertices[p][1] for p in region]) / 6
        grain_centers[r_idx] = [centerx, centery]
        plt.plot(centerx, centery, "b.")

try:
    os.remove("abaqus/output.py")  # remove old version if it exists
except OSError:
    pass

# randomly pick some grains
chosen_centers = []
for g in grain_array:
    if random.random() < 0.33:  # 1/3 chance
        chosen_centers.append(grain_centers[g])
        plt.plot(*grain_centers[g], "r.")

# Finding the cohesive zones relating to each grain would be specific to the
# geometry anyway, so we're going to hardcode it for hexagonal grains
coh_centers = []
offsets = [
    [0, 0.5],
    [0.5, 0.25],
    [0.5, -0.25],
    [0, -0.5],
    [-0.5, -0.25],
    [-0.5, 0.25],
]  # clockwise, starting at the top
for center in grain_centers.values():
    for vector in offsets:
        # applies each offset vector to the grain centerpoint and adds it to the list of cohesive zone centers
        new_point = [a + b for a, b in zip(center, vector)]
        coh_centers.append(new_point)
        plt.plot(*new_point, "b.")


chosen_coh_centers = []
for center in chosen_centers:
    for vector in offsets:
        # applies each offset vector to the grain centerpoint and adds it to the list of cohesive zone centers
        new_point = [a + b for a, b in zip(center, vector)]
        chosen_coh_centers.append(new_point)
        plt.plot(*new_point, "r.")

# Remove instances of chosen cohesive centers from the cohesive centers array
# We don't want to include the same face twice
coh_centers = [p for p in coh_centers if p not in chosen_coh_centers]

with open("abaqus/output.py", "a") as file:
    initialize(file, [upper_x, upper_y])
    for grain in grain_array.values():
        plt.fill(*zip(*grain))
        polygon_writer(file, grain)

    for vertex in vertex_array.values():
        for i in range(1, len(vertex) + 1):
            i = i % len(vertex)  # wrap around
            p1 = vertex[i - 1]
            p2 = vertex[i]
            if (
                ((p1[1] - p2[1]) / (p1[0] - p2[0]) < 0.6)
                and (p1[1] - p2[1]) / (p1[0] - p2[0]) > 0.5
                and len(vertex) == 3
            ):  # slope of section we don't want is ~.6, but only remove it if there's 3 partitions
                pass
            else:
                line_writer(file, p1, p2)
                plt.plot(*zip(p1, p2))
    process_lines(file)
    set_assigner(file, grain_centers.values(), "Grains")
    set_assigner(file, coh_centers, "Cohesive Zones")
    set_assigner(file, chosen_centers, "Chosen Grains")
    set_assigner(file, chosen_coh_centers, "Chosen Cohesive Zones")

plt.axis("square")
plt.xlim(0, upper_x)
plt.ylim(0, upper_y)
plt.show()