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
from utils import length_scale, midpoints, region_sanity, timeit, add_crack
from matplotlib.patches import Rectangle
from utils.shared_config import grain_color, distance

warnings.filterwarnings("ignore", category=RuntimeWarning)
# suppress divide-by-zero warning when calculating a slope

plastic_displacement = 1e-5


@timeit
def generate(
    name: str,
    size: int,
    prop_1: float,
    prop_2: float,
    mesh_size: float = 0.11,
    seed=None,
    coh_stiffness=1e9,
    check_ls: bool = False,
    standalone: bool = False,
):

    if not seed:  # no seed specified
        # pick a 4-digit number to be the random seed. The way this is picked doesn't matter.
        # and use that number as the seed for the rest of the randomization functions
        # this allows for reproducible results
        seed = random.randint(1000, 9999)
    random.seed(seed)  # known state
    print(f"Seed: {seed}")

    points = []
    for i in range(0, size):
        x = i + random.gauss(0, 0.25) * 0.5  # use gaussian distribution
        for j in range(0, size):
            if i % 2:
                j = j + 0.5
            y = j + random.gauss(0, 0.25) * 0.5
            points.append([x, y])
            # plt.plot(x, y, "b.")

    # plt.axis("square")
    # plt.xlim(0, size)
    # plt.ylim(0, size)
    # plt.show()

    vor = Voronoi(points)

    # display original voronoi boundaries
    # fig = voronoi_plot_2d(vor)
    # plt.axis("square")
    # plt.xlim(0, size)
    # plt.ylim(0, size)
    # plt.show()

    from utils.bisector_scaling import scale as bisector_scale
    from collections import defaultdict

    vertex_array = defaultdict(list)  # dict of lists
    grain_array = defaultdict(list)
    grain_centers = {}
    for r_idx, region in enumerate(vor.regions):
        if (
            not -1 in region
            # and len(region) == 6 # only want hexagons
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
            # plt.fill(*zip(*grain_array[r_idx]))  # draw the scaled polygons
            centerx = sum([vor.vertices[p][0] for p in region]) / 6
            centery = sum([vor.vertices[p][1] for p in region]) / 6
            grain_centers[r_idx] = [centerx, centery]
            # plt.plot(centerx, centery, "b.")
            # plt.text(centerx, centery, str(r_idx), size=120 / size)
            # label the grain, shrink text size as the sim size grows

    print(f"Number of Grains: {len(grain_array)}")
    area_per_grain = size * size / len(grain_array)
    print(f"Average area per grain: {area_per_grain}")
    # average grain diameter, treating grains as spheres
    grain_size = 2 * np.sqrt(area_per_grain / np.pi)
    print(f"Average grain size: {grain_size}")

    # add crack
    x_max = size / 6
    # bounds of crack should be one grain in size, centered around the middle.
    halfway = size / 2
    y_min = halfway - grain_size / 2
    y_max = halfway + grain_size / 2
    # Plot the bounding box
    rect = Rectangle(
        (0, y_min),  # lower left corner of box
        x_max,
        y_max - y_min,
        linestyle="dashed",
        linewidth=0.1,
        fill=False,
    )  # type: ignore
    # plt.gca().add_patch(rect)

    grain_array, grain_centers = add_crack(
        grain_array, grain_centers, x_max, y_min, y_max
    )

    with open(f"{name}.py", "w") as file:
        header(file)
        for grain in grain_array.values():
            polygon_writer(file, grain)

        process_lines(file)
        section(file, "Alumina", 370e9, 0.25)
        mesh(file, seed_size=mesh_size)
        make_instance(file)
        for g in grain_array:
            mps = midpoints(grain_array[g])
            surface_maker(file, f"Surf-{g}", mps)
        interaction_property(
            file,
            "Prop-1",
            damagevalue=prop_1,
            plastic_displacement=plastic_displacement,
            viscosity=1e-3,
            coh_stiffness=coh_stiffness,
        )
        ls_1 = length_scale(
            strength=prop_1,
            mesh_size=mesh_size,
            crack_length=x_max,
            crit_displacement=plastic_displacement,
            stiffness=coh_stiffness,
            scientific=True,
            check=check_ls,
        )
        interaction_property(
            file,
            "Prop-2",
            damagevalue=prop_2,
            plastic_displacement=plastic_displacement,
            viscosity=1e-3,
            coh_stiffness=coh_stiffness,
        )
        ls_2 = length_scale(
            strength=prop_2,
            crit_displacement=plastic_displacement,
            stiffness=coh_stiffness,
            scientific=True,
        )
        effective_ls = 370e9 / (2 * (coh_stiffness))
        print(f"Effective length scale: {effective_ls}")
        general_interaction(file, "General", "Prop-1")
        encastre(file, "BC-1", threshold=2)
        top_displacement(file, "BC-2", u2=0.001, threshold=size - 2)
        if standalone:
            write_inp(file, name)
        file.write(f"mdb.saveAs('{name}')")  # save cae

    # title = f"Seed: {seed}, Prop-1: {prop_1},  Prop-2: {prop_2}"
    # plt.title(title)
    plt.axis("square")
    plt.xlim(0, size)
    plt.ylim(0, size)
    notetext = (
        f"Seed: {seed}\n"
        + "Strengths:\n"
        + f"  Prop-1: {prop_1:.2E}\n"
        + f"  Prop-2: {prop_2:.2E}\n"
        + "Length Scales:\n"
        + f"  Prop-1: {ls_1}\n"
        + f"  Prop-2: {ls_2}\n"
        + f"Grain Size: {grain_size:.3}\n"
    )

    plt.gcf().text(0.05, 0.4, notetext, fontsize=8)
    for key, value in grain_array.items():
        plt.fill(  # plot the grains
            color=grain_color,
            *zip(*value),
            ls="",  # no line
        )
        plt.text(
            grain_centers[key][0], grain_centers[key][1], str(key), size=120 / size
        )
    plt.gca().set_axis_off()  # hide the axes

    # plt.show()
    plt.savefig(f"{name}.png", bbox_inches="tight", dpi=20 * size)
    # dpi scale with the size of the image

    # save the grain array to a file
    data = {}
    data["size"] = size
    data["seed"] = seed
    data["prop_1"] = prop_1
    data["prop_2"] = prop_2
    data["plastic_displacement"] = plastic_displacement
    data["mesh_size"] = mesh_size
    data["coh_stiffness"] = coh_stiffness
    data["lengthscale1"] = ls_1
    data["lengthscale2"] = ls_2
    data["grain_array"] = grain_array
    data["grain_centers"] = grain_centers
    data["vor_regions_length"] = len(vor.regions)
    json.dump(data, open(f"{name}.json", "w"))


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
    name = args.name
    size = args.size
    prop_1 = args.prop_1
    prop_2 = args.prop_2

    if args.seed:  # specify a seed
        seed = args.seed
    else:  # no seed specified
        seed = None

    generate(name, size, prop_1, prop_2, seed=seed)
