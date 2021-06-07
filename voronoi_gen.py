from typing import DefaultDict
from scipy.spatial import Voronoi, voronoi_plot_2d, Delaunay
import matplotlib.pyplot as plt
import random, os
import numpy as np
import warnings
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("name", help="filename for the output script and plot")
parser.add_argument("size", help="Size of the simulation", type=int)
parser.add_argument(
    "prop_1", help="Strength of the primary contact interactions", type=float
)
parser.add_argument(
    "prop_2", help="Stength of the secondary contact interactions", type=float
)
parser.add_argument("-s", "--seed", help="Specify the seed value", type=int)
args = parser.parse_args()

from utils.coh_surf_macros import (
    encastre,
    header,
    make_instance,
    property_assignment,
    section,
    mesh,
    polygon_writer,
    section,
    set_maker,
    surface_maker,
    process_lines,
    interaction_property,
    general_interaction,
    top_displacement,
    write_inp,
)
from utils import midpoints, region_sanity

warnings.filterwarnings("ignore", category=RuntimeWarning)
# suppress divide-by-zero warning when calculating a slope

upper_x = args.size
upper_y = args.size
distance = 0.005  # width of the gap between grains

if args.seed:  # specified a seed
    seed = args.seed
    print(f"Specified seed: {seed}")
else:
    # pick a 4-digit number to be the random seed. The way this is picked doesn't matter.
    # and use that number as the seed for the rest of the randomization functions
    # this allows for reproducible results
    seed = random.randint(1000, 9999)
    print(f"Seed for this run: {seed}")
random.seed(seed)  # known state


# pick a 4-digit number to be the random seed. The way this is picked doesn't matter.
# and use that number as the seed for the rest of the randomization functions
# this allows for reproducible results
seed = random.randint(1000, 9999)
random.seed(
    seed
)  # the rest of the calls to random will use this seed. To reproduce results, change its value

points = []
for i in range(0, upper_x):
    x = i + random.random() * 0.5
    for j in range(0, upper_y):
        if i % 2:
            j = j + 0.5
        y = j + random.random() * 0.5
        points.append([x, y])
        # plt.plot(x, y, "b.")

# plt.axis("square")
# plt.xlim(0, upper_x)
# plt.ylim(0, upper_y)
# plt.show()


vor = Voronoi(points)

# display original voronoi boundaries
# fig = voronoi_plot_2d(vor)
# plt.axis("square")
# plt.xlim(0, upper_x)
# plt.ylim(0, upper_y)
# plt.show()


from utils.bisector_scaling import scale as bisector_scale
from collections import defaultdict

vertex_array = defaultdict(list)  # dict of lists
grain_array = defaultdict(list)
grain_centers = {}
for r_idx, region in enumerate(vor.regions):
    if (
        not -1 in region
        and len(region) == 6
        and region_sanity(region, upper_x, upper_y, vor.vertices)
    ):  # bounded with 6 sides
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
        plt.fill(*zip(*grain_array[r_idx]))  # draw the scaled polygons
        centerx = sum([vor.vertices[p][0] for p in region]) / 6
        centery = sum([vor.vertices[p][1] for p in region]) / 6
        grain_centers[r_idx] = [centerx, centery]
        plt.plot(centerx, centery, "b.")
        plt.text(centerx, centery, str(r_idx), size="x-small")


# randomly pick some grains

chosen_grains = []
for g in grain_array:
    if random.random() < 0.33:  # 1/3 chance
        plt.plot(*grain_centers[g], "r*")
        chosen_grains.append(g)

# plt.axis("square")
# plt.xlim(0, upper_x)
# plt.ylim(0, upper_y)
# plt.show()


indexed = []
for i in range(len(vor.regions)):
    c = grain_centers.get(i, [0, 0])  # get the center of grain with id i,
    # and if empty (invalid region, etc), then use a default of [0,0]
    indexed.append(c)
    # and add it to a new array, where the index of the list aligns with the grain id

indptr, indices = Delaunay(indexed).vertex_neighbor_vertices
# array of nearest neighbor relations, needed for later


with open(f"{args.name}.py", "a") as file:
    header(file)
    for grain in grain_array.values():
        polygon_writer(file, grain)

    process_lines(file)
    section(file, "Alumina", 370e9, 0.25)
    mesh(file)
    make_instance(file)
    for g in grain_array:
        mps = midpoints(grain_array[g])
        surface_maker(file, f"Surf-{g}", mps)
    interaction_property(file, "Prop-1", args.prop_1, 0.01, 0.00001)
    interaction_property(file, "Prop-2", args.prop_2, 0.01, 0.00001)
    general_interaction(file, "General", "Prop-1")
    encastre(file, "BC-1")
    top_displacement(file, "BC-2", u2=0.1, threshold=upper_y - 1.5)
    colors = iter(plt.cm.tab20(np.linspace(0, 1, len(chosen_grains))))
    for c_idx in chosen_grains:
        color = next(colors)
        neighbors = indices[indptr[c_idx] : indptr[c_idx + 1]]
        for neighbor in neighbors:
            if neighbor != 0:
                plt.plot(
                    [grain_centers[c_idx][0], grain_centers[neighbor][0]],
                    [grain_centers[c_idx][1], grain_centers[neighbor][1]],
                    color=color,
                )
                property_assignment(
                    file, "General", "Prop-2", f"Surf-{c_idx}", f"Surf-{neighbor}"
                )
    write_inp(file, args.name)


plt.title(f"Seed: {seed}")
plt.axis("square")
plt.xlim(0, upper_x)
plt.ylim(0, upper_y)
plt.savefig(f"{args.name}.png", dpi=400)
# plt.show()