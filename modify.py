import json, random, argparse
from utils import timeit
from matplotlib import pyplot as plt
from scipy.spatial import Delaunay
from utils import *
from utils.coh_surf_macros import *
import numpy as np


@timeit
def modify(cae_filename: str, name: str, mod_fraction: float, seed: int = None):
    """
    Creates a python script to modify the homogenous CAE file,
    using microstructure information from a json file
    """
    if mod_fraction < 0 or mod_fraction > 1:
        raise ValueError("Mod fraction must be between 0 and 1")
    #####################################
    # Load the data from the json file #
    #####################################
    json_filename = cae_filename.replace(".cae", ".json")
    with open(json_filename, "r") as json_file:
        json_data = json.load(json_file)
        size = json_data["size"]  # type: float
        prop_1 = json_data["prop_1"]  # type: float
        prop_2 = json_data["prop_2"]  # type: float
        keyint = lambda dict_: {
            int(k): v for k, v in dict_.items()
        }  # turns all keys into ints since the json process turns everything into strings
        grain_array = json_data["grain_array"]
        grain_array = keyint(grain_array)  # type: dict[int, list[list[float]]]
        grain_centers = json_data["grain_centers"]
        grain_centers = keyint(grain_centers)  # type: dict[int, list[float]]
        vor_regions_length = json_data["vor_regions_length"]  # type:int

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
    for i in range(vor_regions_length):
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
        write_inp(file, name)

    title = f"Seed: {seed}, Prop-1: {prop_1}"
    if mod_fraction:  # some grains will be modified
        title += f", {mod_fraction:.0%} mod to Prop-2: {prop_2}"
    plt.title(title)

    plt.axis("square")
    plt.xlim(0, size)
    plt.ylim(0, size)
    for value in grain_array.values():
        plt.fill(*zip(*value))  # plot the grains
    plt.savefig(f"{name}.png", dpi=20 * size)


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
    fraction = args.fraction
    new_seed = args.seed
    if not cae_filename.endswith(".cae"):
        raise ValueError("Cae file must end with .cae")

    if new_seed:  # specify a seed
        pass
    else:  # no seed specified
        new_seed = None

    modify(cae_filename, name, fraction, new_seed)
