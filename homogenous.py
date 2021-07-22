from typing import DefaultDict
from scipy.spatial import Voronoi, voronoi_plot_2d, Delaunay
import matplotlib.pyplot as plt
import random, os
import numpy as np
import warnings
import json
import argparse
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
from utils import midpoints, region_sanity, timeit

warnings.filterwarnings("ignore", category=RuntimeWarning)
# suppress divide-by-zero warning when calculating a slope


distance = 0.005  # width of the gap between grains


@timeit
def generate(upper_x, upper_y, prop_1, prop_2, seed=None):

    if not seed:  # no seed specified
        # pick a 4-digit number to be the random seed. The way this is picked doesn't matter.
        # and use that number as the seed for the rest of the randomization functions
        # this allows for reproducible results
        seed = random.randint(1000, 9999)
    random.seed(seed)  # known state
    print(f"Seed: {seed}")

    points = []
    for i in range(0, upper_x):
        x = i + random.gauss(0, 0.25) * 0.5  # use gaussian distribution
        for j in range(0, upper_y):
            if i % 2:
                j = j + 0.5
            y = j + random.gauss(0, 0.25) * 0.5
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
            plt.text(centerx, centery, str(r_idx), size=120 / upper_y)
            # label the grain, shrink text size as the sim size grows

    with open(f"{args.name}.py", "w") as file:
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
        interaction_property(
            file,
            "Prop-1",
            damagevalue=prop_1,
            plastic_displacement=1e-5,
            viscosity=1e-3,
        )
        interaction_property(
            file,
            "Prop-2",
            damagevalue=prop_2,
            plastic_displacement=1e-5,
            viscosity=1e-3,
        )
        general_interaction(file, "General", "Prop-1")
        encastre(file, "BC-1")
        top_displacement(file, "BC-2", u2=0.001, threshold=upper_y - 1.5)
        file.write(f"mdb.saveAs('{args.name}')")  # save cae

    title = f"Seed: {seed}, prop_1: {prop_1},  prop_2: {prop_2}"
    plt.title(title)

    plt.axis("square")
    plt.xlim(0, upper_x)
    plt.ylim(0, upper_y)

    plt.savefig(f"{args.name}.png", dpi=20 * upper_y)
    # scale with the size of the image

    json.dump(  # save generation paramters to file
        {"size": upper_y, "seed": seed, "prop_1": prop_1, "prop_2": prop_2},
        open(f"{args.name}.json", "w"),
    )

    # plt.show()


if __name__ == "__main__":  # running standalone, not as a function, so take arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="filename for the output script and plot")
    parser.add_argument(
        "size",
        help="Size of the simulation",
        type=int,
    )
    parser.add_argument(
        "prop_1", help="Strength of the primary contact interactions", type=float
    )
    parser.add_argument(
        "prop_2", help="Stength of the secondary contact interactions", type=float
    )
    parser.add_argument(
        "-s",
        "--seed",
        help="Specify the seed value used to initialize the rng",
        type=int,
    )
    args = parser.parse_args()
    upper_x = args.size
    upper_y = args.size
    prop_1 = args.prop_1
    prop_2 = args.prop_2

    if args.seed:  # specify a seed
        seed = args.seed
    else:  # no seed specified
        seed = None

    generate(upper_x, upper_y, prop_1, prop_2, seed=seed)
