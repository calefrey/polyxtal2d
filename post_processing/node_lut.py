# given an input file and a list of nodes,
# find the properties of all nodes in the list
# using a top-down approach

from collections import defaultdict
import re, json
import numpy as np

element_def_regex = re.compile(r"^\s?(?:\d*,\s*)+\d*$")

surf_def_regex = re.compile(
    r"^\*Elset, elset=_(?P<surface>Surf-\d+)_(?P<face>S\d), internal, instance=Part-1-1$"
)
surf_def_generate_regex = re.compile(
    r"^\*Elset, elset=_(?P<surface>Surf-\d+)_(?P<face>S\d), internal, instance=Part-1-1, generate$"
)
prop_def_regex = re.compile(r"\*Surface Interaction, name=(?P<mame>Prop-\d)")

surf_prop_regex = re.compile(r"Surf-(?:\d+) , Surf-(?:\d+) , (?P<property>Prop-\d)")


class Section:
    def __init__(self, name):
        self.name = name


element_section = Section("elements")
surface_section = Section("surfaces")
interaction_property_section = Section("interaction_properties")
prop_assignment = Section("properties")


def find_node_properties(inp_file, debug=False):
    property_dict = defaultdict(list)  # {property_name:[surf_id,...]}
    surface_dict = defaultdict(dict)  # {surf_id:{face:element_list}}
    element_dict = defaultdict(dict)  # {element_id:{face:node_list}}
    interactions_dict = defaultdict(list)  # {property_name:[strength,displacement]}
    try:
        with open(inp_file, "r") as f:
            inp_data = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"INP file {inp_file} not found")

    state = element_section  # we start here

    for i, line in enumerate(inp_data):
        if state is element_section:
            if element_def_regex.match(line):
                element_id = line.split(",")[0].strip()
                nodes = [_.strip() for _ in line.split(",")][1:]
                if len(nodes) == 4:  # quad
                    face2index = {
                        "S1": [0, 1],
                        "S2": [1, 2],
                        "S3": [2, 3],
                        "S4": [3, 0],
                    }
                elif len(nodes) == 3:  # tri
                    face2index = {"S1": [0, 1], "S2": [1, 2], "S3": [2, 0]}
                else:
                    raise ValueError(
                        f"Element with {len(nodes)} nodes not supported, see line {i+1}"
                    )
                for face, indexs in face2index.items():
                    element_dict[element_id][face] = [nodes[i] for i in indexs]

            elif line.startswith("*Nset"):  # move on
                state = surface_section
                print("Moving to surface assignments")

        elif state is surface_section:
            data_line = inp_data[i + 1]
            if surf_def_regex.match(line):
                match = surf_def_regex.match(line)
                surface_id = match.group("surface")
                face = match.group("face")
                elements = [_.strip() for _ in data_line.split(",")]
                surface_dict[surface_id][face] = list(
                    filter(None, elements)
                )  # remove empty strings

            elif surf_def_generate_regex.match(line):
                match = surf_def_generate_regex.match(line)
                surface_id = match.group("surface")
                face = match.group("face")
                start, end, step = [int(_.strip(" ,")) for _ in data_line.split() if _]
                elements = np.arange(start, end + 1, step)  # inclusive
                surface_dict[surface_id][face] = [str(_) for _ in elements if _]
            elif line.startswith("*End Assembly"):  # move on
                state = interaction_property_section
                print("Moving to interaction properties")

        elif state is interaction_property_section:
            if prop_def_regex.match(line):
                name = prop_def_regex.match(line).group("mame")
                strength_line = inp_data[i + 5]
                strength = strength_line.split(",")[0].strip()
                displacement_line = inp_data[i + 7]
                displacement = displacement_line.split(",")[0].strip()
                interactions_dict[name] = [strength, displacement]

            elif line.startswith("*Contact Property Assignment"):  # move on
                state = prop_assignment
                print("Moving to property assignments")

        elif state is prop_assignment:
            if surf_prop_regex.match(line):
                property = surf_prop_regex.match(line).group("property")
                surfaces = [_.strip() for _ in line.split(",") if _][:-1]
                property_dict[property].extend(surfaces)

    print("Data collection finished, saving...")
    if debug:
        json.dump(
            (property_dict, surface_dict, element_dict, interactions_dict),
            open("data.json", "w"),
        )

    # recomine all data to get node properties
    node_props = {}
    for property, surfaces in property_dict.items():
        for surface in surfaces:
            for face, elements in surface_dict[surface].items():
                for element in elements:
                    for node in element_dict[element][face]:
                        if face in element_dict[element]:
                            node_props[node] = interactions_dict[property]
    node_props["default"] = interactions_dict["Prop-1"]

    json.dump(node_props, open("node_lut.json", "w"), indent=4)


if __name__ == "__main__":
    from sys import argv

    # find_node_properties("post_processing/test.inp", debug=True)
    find_node_properties(argv[1])
