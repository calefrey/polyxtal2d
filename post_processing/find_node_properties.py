import re

# find the surface assigment, this line should be above the node list
surface_assignment_regex = (
    r"^\*Elset, elset=_(?P<surface>Surf-\d+)_\w\d, internal, instance=Part-1-1$"
)

surface2prop_regex = r"Surf-(?:\d+) , Surf-(?:\d+) , (?P<property>Prop-\d)"
strength_regex = r"(?P<strength>\d+.),\d+.,\d+"


def node_toughness(node_id: str, inp_file: str, debug: bool = False) -> float:
    try:
        inp = open(inp_file, "r")
        inp_lines = inp.readlines()
        if debug:
            print(f"Loading inp file with {len(inp_lines)} lines")
        inp.close()
    except FileNotFoundError:
        print("INP file not found")
        exit(1)

    surface_assignment = None
    for i in range(len(inp_lines)):
        if node_id in inp_lines[i]:
            if debug:
                print(inp_lines[i - 1].strip())
                print(inp_lines[i].strip())
            if re.match(
                surface_assignment_regex, inp_lines[i - 1]
            ):  # we see the node and we're in the right section
                surface_assignment = re.match(
                    surface_assignment_regex, inp_lines[i - 1]
                ).group(
                    "surface"
                )  #  get the surface name assigned to the node
                if debug:
                    print(f"Node {node_id} assigned to surface {surface_assignment}")
                    print()
                break

    if surface_assignment is None:
        print(f"Node {node_id} not found")
        exit(1)

    # now try to find the property assigned to the surface
    property = None
    for line in inp_lines:
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
    strength = None
    for i in range(len(inp_lines)):
        if property_header in inp_lines[i]:
            if debug:
                print("".join(inp_lines[i : i + 9]))
            strength_line = inp_lines[i + 5]
            strength = re.match(strength_regex, strength_line).group("strength")
            if debug:
                print(f"Strength of {property} is {strength}")
            displacement_line = inp_lines[i + 7]
            displacement = displacement_line.split(",")[0].strip()
            if debug:
                print(f"Displacement of {property} is {displacement}")
    if strength is None:
        print(f"Property {property} not found")
        print(f"Error occured on node {node_id} \a")
        exit(1)

    # toughness = 0.5 * strength * critical displacement
    toughness = 0.5 * float(strength) * float(displacement)
    if debug:
        print(f"Toughness of {property} is {toughness}")
    return toughness
