from typing import DefaultDict
from scipy.spatial import Voronoi, voronoi_plot_2d, Delaunay
import matplotlib.pyplot as plt
import random, os
import numpy as np
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
from collections import defaultdict

distance = 0.005  # width of the gap between grains


@timeit
def modify(
    name: str,
    cae_filename: str,
    size: int,
    old_seed: int,
    mod_fraction: float,
    seed: int = None,
):
    #########################################################
    # Code to recreate oritinal grain structure with old seed
    #########################################################
    random.seed(old_seed)  # known state

    points = []
    for i in range(0, size):
        x = i + random.gauss(0, 0.25) * 0.5  # use gaussian distribution
        for j in range(0, size):
            if i % 2:
                j = j + 0.5
            y = j + random.gauss(0, 0.25) * 0.5
            points.append([x, y])

    vor = Voronoi(points)

    from utils.bisector_scaling import scale as bisector_scale

    vertex_array = defaultdict(list)  # dict of lists
    grain_array = defaultdict(list)
    grain_centers = {}
    for r_idx, region in enumerate(vor.regions):
        if (
            not -1 in region
            and len(region) == 6
            and region_sanity(region, size, size, vor.vertices)
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
            plt.text(centerx, centery, str(r_idx), size=120 / size)

    #####################################
    # Select chosen grains using new seed
    #####################################

    if not seed:  # no seed specified
        # pick a 4-digit number to be the random seed. The way this is picked doesn't matter.
        # and use that number as the seed for the rest of the randomization functions
        # this allows for reproducible results
        # first need to reset the seed so the different trials generate different new seeds
        random.seed()
        seed = random.randint(1000, 9999)
    random.seed(seed)  # known state
    print(f"New seed: {seed}")

    chosen_grains = []
    for g in grain_array:
        if random.random() < mod_fraction:  # set fraction of modified grains
            if prop_2 < prop_1 and (
                size - grain_centers[g][1] < size / 10
                or grain_centers[g][1] < size / 10
            ):  # Don't add weaker modifiers if the grains are near the top or bottom
                pass
            else:
                plt.plot(*grain_centers[g], "r*")
                chosen_grains.append(g)

    indexed = []
    for i in range(len(vor.regions)):
        c = grain_centers.get(i, [0, 0])  # get the center of grain with id i,
        # and if empty (invalid region, etc), then use a default of [0,0]
        indexed.append(c)
        # and add it to a new array, where the index of the list aligns with the grain id

    indptr, indices = Delaunay(indexed).vertex_neighbor_vertices
    # array of nearest neighbor relations, needed for later

    #####################################
    # write the result to file
    #####################################

    with open(f"{name}.py", "w") as file:
        file.write("from abaqusConstants import *\n")
        file.write(f"openMdb('{cae_filename}')\n")
        colors = iter(plt.cm.tab20(np.linspace(0, 1, len(chosen_grains))))  # type: ignore
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

    title = f"Seed: {seed}, prop_1: {prop_1}"
    if mod_fraction:  # some grains will be modified
        title += f", {mod_fraction:.0%} mod to prop_2: {prop_2}"
    plt.title(title)

    plt.axis("square")
    plt.xlim(0, size)
    plt.ylim(0, size)

    plt.savefig(f"{args.name}.png", dpi=20 * size)


if __name__ == "__main__":  # running standalone, not as a function, so take arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="output name")
    parser.add_argument("cae", help="cae file name to modify")
    parser.add_argument(
        "fraction",
        help="fraction of grains to have modified properties",
        type=float,
    )
    parser.add_argument(
        "-s",
        "--seed",
        help="New seed for the rng",
        type=int,
    )
    args = parser.parse_args()
    name = args.name
    cae_filename = args.cae
    new_seed = args.seed
    if not cae_filename.endswith(".cae"):
        raise ValueError("Cae file must end with .cae")
    # load parameters saved from homogenous run
    previous_data = json.load(open(cae_filename.replace(".cae", ".json")))
    size = previous_data["size"]
    print(f"size: {size}")
    old_seed = previous_data["seed"]
    print(f"seed: {old_seed}")
    prop_1 = previous_data["prop_1"]
    print(f"prop_1: {prop_1}")
    prop_2 = previous_data["prop_2"]
    print(f"prop_2: {prop_2}")

    if new_seed:  # specify a seed
        pass
    else:  # no seed specified
        new_seed = None

    modify(args.name, cae_filename, size, old_seed, args.fraction, seed=new_seed)
