from io import TextIOWrapper
import re, time
from functools import lru_cache

# find the surface assigment, this line should be above the node list
surface_assignment_regex = (
    r"\*Elset, elset=_(?P<surface>Surf-\d+)_(?P<face>S\d), internal, instance=Part-1-1"
)

surface2prop_regex = r"Surf-(?:\d+) , Surf-(?:\d+) , (?P<property>Prop-\d)"
strength_regex = r"(?P<strength>\d+.),\d+.,\d+"


def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Time taken: {end - start}")
        return result

    return wrapper


# @lru_cache(maxsize=None)
def node_toughness(
    node_id: str, inp_file: str = None, inp_lines: list = None, debug: bool = False
):
    node_elements = {}
    surface_assignment = None
    property = None
    strength = None
    displacement = None
    if inp_lines:
        inp_data = inp_lines
    elif inp_file:  # a filename was passed, need to open it
        try:
            inp = open(inp_file, "r")
            inp_data = inp.readlines()
            if debug:
                print(f"Loading inp file with {len(inp_data)} lines")
            inp.close()
        except FileNotFoundError:
            raise FileNotFoundError(f"INP file {inp_file} not found")
    else:
        raise ValueError("No input data was passed")

    # Find the element the node belongs to
    for i, line in enumerate(inp_data):
        if node_id in line:
            if re.match(r"^\s?(?:\d*,\s*)+\d*$", line):
                if debug:
                    print(line)
                element_id = line.split(",")[0].strip()
                # now we need to find what side of the element the node is on
                # S1 is the first two nodes, S2 is the 2nd and third nodes, S3 is the last two nodes, and S4 is the last and first node
                # source: "Node ordering and face numbering on elements" on https://abaqus-docs.mit.edu/2017/English/SIMACAEELMRefMap/simaelm-r-2delem.htm
                # each node could be on two surfaces, so using a tuple
                nodes = [_.strip() for _ in line.split(",")][1:]
                if node_id not in nodes:
                    # make sure it's an acutual node id and not part of a longer node id
                    continue
                element_index = nodes.index(node_id)
                if len(nodes) == 4:  # quad
                    index2face = {
                        0: ("S4", "S1"),
                        1: ("S1", "S2"),
                        2: ("S2", "S3"),
                        3: ("S3", "S4"),
                    }
                elif len(nodes) == 3:  # tri
                    index2face = {0: ("S3", "S1"), 1: ("S1", "S2"), 2: ("S2", "S3")}
                else:
                    raise ValueError(
                        f"Element with {len(nodes)} nodes not supported, error on node {node_id}"
                    )

                node_elements[element_id] = index2face[element_index]

        if line.startswith("*Elset"):  # we went too far, abort
            break
    if not node_elements:
        raise ValueError(f"Node {node_id} not found in inp file")

    # Find the surface assignment
    for element, faces in node_elements.items():
        for i in range(len(inp_data)):
            if element in inp_data[i]:
                if debug:
                    print(inp_data[i - 1].strip())
                    print(inp_data[i].strip())
                if re.match(surface_assignment_regex, inp_data[i - 1]):
                    # we see the node and we're in the right section
                    match = re.match(surface_assignment_regex, inp_data[i - 1])
                    surface_assignment = match.group("surface")
                    face = match.group("face")
                    if face not in faces:  # the node is not on that face
                        continue

                    if debug:
                        print(
                            f"Element {element} assigned to surface {surface_assignment}_{face}"
                        )
                        print()

    if surface_assignment is None:

        # raise ValueError(f"No surface found matching node {node_id}: {node_elements}")
        print(f"No surface found matching node {node_id}: {node_elements}")
        surface_assignment = "Surf-undefined"

    # now try to find the property assigned to the surface
    for line in inp_data:
        if surface_assignment in line:
            if debug:
                print(line.strip())
            if re.match(surface2prop_regex, line):
                property = re.match(surface2prop_regex, line).group("property")
                if debug:
                    print(
                        f"Surface {surface_assignment} assigned to property {property}"
                    )
                break
    if property is None:
        if debug:
            print(
                f"Surface {surface_assignment} not found, so it must be the default property"
            )
        property = "Prop-1"  # default property

    # now find the property associated with that surface
    property_header = f"*Surface Interaction, name={property}"
    for i in range(len(inp_data)):
        if property_header in inp_data[i]:
            if debug:
                print("".join(inp_data[i : i + 9]))
            strength_line = inp_data[i + 5]
            strength = re.match(strength_regex, strength_line).group("strength")
            if debug:
                print(f"Strength of {property} is {strength}")
            displacement_line = inp_data[i + 7]
            displacement = displacement_line.split(",")[0].strip()
            if debug:
                print(f"Displacement of {property} is {displacement}")
    if strength is None or displacement is None:
        print(f"Property {property} not found")
        print(f"Error occured on node {node_id} \a")
        exit(1)

    # toughness = 0.5 * strength * critical displacement
    toughness = 0.5 * float(strength) * float(displacement)
    if debug:
        print(f"Toughness of {property} is {toughness}")
    return round(toughness, 5)  # round to remove floating point errors


if __name__ == "__main__":
    import json
    from sys import argv as args

    # if len(args) < 3:
    #     print("Usage: find_node_properties.py <json_file> <inp_file> [debug]")
    #     exit(1)

    if len(args) == 4:
        debug = True
    else:
        debug = False

    # json_file = args[1]
    # inp_file = args[2]
    json_file = "job_data.json"
    inp_file = "test.inp"
    debug = False

    node_ids = json.load(open(json_file, "r"))["node_ids"]
    print(f"Found {len(node_ids)} nodes")
    for node_id in node_ids:
        try:
            toughness = node_toughness(node_id, inp_file, debug=debug)
            print(f"Toughness of node {node_id} is {toughness:.2f}")
        except ValueError as e:
            print(f"{e} \a")
