import json, random, argparse
from utils import timeit
from matplotlib import pyplot as plt
from scipy.spatial import Delaunay
from utils import *
from utils.coh_surf_macros import *
import numpy as np
from matplotlib import cm
from utils.shared_config import grain_color, modifier_color


@timeit
def modify(
    cae_filename: str,
    name: str,
    mod_fraction: float,
    seed: int = None,
    new_prop_1: float = None,
    new_prop_2: float = None,
    new_crit_disp_1: float = None,
    new_crit_disp_2: float = None,
    viscosity: float = 1e-3,
    check_ls: bool = False,
):
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
        old_crit_disp = json_data["plastic_displacement"]  # type: float
        mesh_size = json_data["mesh_size"]  # type: float
        coh_stiffness = json_data["coh_stiffness"]  # type: float
        grain_array = json_data["grain_array"]
        grain_array = keyint(grain_array)  # type: dict[int, list[list[float]]]
        grain_centers = json_data["grain_centers"]
        grain_centers = keyint(grain_centers)  # type: dict[int, list[float]]
        vor_regions_length = json_data["vor_regions_length"]  # type:int
    ##############################
    # Plot all grains first
    ##############################
    for value in grain_array.values():
        plt.fill(*zip(*value), color=grain_color, ls="")  # plot the grains

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
                plt.fill(
                    *zip(*grain_array[g]), color=modifier_color, fill=False
                )  # plot border of modified gran

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

        # modify critical displacement
        if new_crit_disp_1:
            crit_disp_1 = new_crit_disp_1
        else:
            crit_disp_1 = old_crit_disp
        if new_crit_disp_2:
            crit_disp_2 = new_crit_disp_2
        else:
            crit_disp_2 = old_crit_disp

        if new_prop_1:  # override property from json file
            prop_1 = new_prop_1
            if new_crit_disp_1:  # override critical displacement from json file
                crit_disp_1 = new_crit_disp_1
            interaction_property(  # edit the interaction property
                file,
                "Prop-1",
                damagevalue=prop_1,
                plastic_displacement=crit_disp_1,
                coh_stiffness=coh_stiffness,
                viscosity=viscosity,
            )
        if new_prop_2:  # override property from json file
            prop_2 = new_prop_2
            interaction_property(  # edit the interaction property
                file,
                "Prop-2",
                damagevalue=prop_2,
                plastic_displacement=crit_disp_2,
                coh_stiffness=coh_stiffness,
                viscosity=viscosity,
            )
        ls_1 = length_scale(
            strength=prop_1,
            mesh_size=mesh_size,
            crit_displacement=crit_disp_1,
            stiffness=coh_stiffness,
            scientific=True,
            check=check_ls,
        )
        ls_2 = length_scale(
            strength=prop_2,
            crit_displacement=crit_disp_2,
            stiffness=coh_stiffness,
            scientific=True,
        )
        for c_idx in chosen_grains:
            neighbors = indices[indptr[c_idx] : indptr[c_idx + 1]]
            for neighbor in neighbors:
                if neighbor != 0:
                    property_assignment(
                        file, "General", "Prop-2", f"Surf-{c_idx}", f"Surf-{neighbor}"
                    )
        write_inp(file, name)

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
        + f"  Prop-2: {ls_2}"
    )
    plt.gcf().text(0.05, 0.4, notetext, fontsize=8)
    plt.gca().set_axis_off()  # hide the axes
    plt.savefig(f"{name}.png", bbox_inches="tight", dpi=20 * size)

    data = {
        "prop_1": prop_1,
        "prop_2": prop_2,
        "seed": seed,
        "mod_fraction": mod_fraction,
        "plastic_displacement": crit_disp_1,
        "coh_stiffness": coh_stiffness,
        "mesh_size": mesh_size,
    }
    json.dump(data, open(f"{name}.json", "w"))


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
