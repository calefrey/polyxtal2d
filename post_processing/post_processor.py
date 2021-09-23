# Run with abaqus python .\post_processor.py .\precrack.odb

import math, os
from odbAccess import *
from sys import argv
import json

# PROPERTIES TO CHANGE ========================
a0 = 5  # initial crack depth, be conservative
max_delta_a = 10  # max crack length increase per increment
# ==============================================

odb_filename = argv[1]
dmg_thresh = 0.999
# Load strength from the json file
json_filename = odb_filename.replace(".odb", ".json")
with open(json_filename, "r") as json_file:
    data = json.load(json_file)
    strength = int(data["prop_1"])
    modulus = float(data["coh_stiffness"])
    critical_displacement = float(data["plastic_displacement"])
    mesh_size = float(data["mesh_size"])


def stress_intensity_factor(stress, a, width):
    """
    Returns K_I for an edge crack of length a in a sample of given width under uniaxial stress
    """
    return (
        stress
        * math.sqrt(math.pi * a)
        * (
            1.12
            - 0.231 * a / width
            + 10.55 * a / width ** 2
            - 21.71 * a / width ** 3
            + 30.382 * a / width ** 4
        )
    )


# Objective: Generate a plot of crack length a vs stress intensity factor K
odb = openOdb(path=odb_filename, readOnly=True)


# ===============================================
# Generate the r-curve, saved to r-curve.txt
# ===============================================

try:  # we append to the file, so if there's already one, delete it
    os.remove("r-curve.txt")
except OSError:  # file already deleted
    pass
f = open("r-curve.txt", "a")  # file to save data
f.write("name=" + odb_filename + "\n")
initial_x_values = [
    value.data[0]  # x value for each node in first frame
    for value in odb.steps.values()[0].frames[0].fieldOutputs["COORD"].values
]
x_offset = min(initial_x_values)
width = max(initial_x_values) - x_offset

current_a = a0
toughness = 0.5 * (strength * critical_displacement)
print("Toughness = " + str(toughness))
critical_sif = math.sqrt(toughness * modulus)
print("Critical SIF:", critical_sif)
for step in odb.steps.values():
    print("Processing: " + step.name)
    for frame in step.frames:
        # load the data
        csdmg = frame.fieldOutputs[
            "CSDMG    General_Contact_Faces/General_Contact_Faces"
        ]
        coords = frame.fieldOutputs["COORD"]

        # Find the crack tip
        # loop through the nodes and check their CSDMG
        for i in range(len(csdmg.values)):
            x = coords.values[i].data[0]
            if (
                csdmg.values[i].data > dmg_thresh
                and x > current_a
                and x < current_a + max_delta_a  # only look just ahead previous crack
            ):
                # print("New crack tip at x=" + str(coords.values[i].data[0]))
                current_a = coords.values[i].data[0]
                if current_a >= width:  # we've reached the end of the sample
                    print("End of sample reached")
                    exit()  # end logging

        # should have the leftmost failed node located at current_a
        # which should be the crack tip
        # Need to offset the crack since sample doesn't start at x=0
        a = current_a - x_offset
        print("Frame " + str(frame.frameId) + ": a=" + str(a)),

        # Determine the stress applied to the sample
        top = odb.rootAssembly.instances["PART-1-1"].nodeSets["TOP"]
        rf = frame.fieldOutputs["RF"].getSubset(region=top)
        f_total = 0
        for f_val in rf.values:
            # if f_val.data[1] > 0:  # exclude negative effects
            f_total += f_val.data[1]  # sum up the y values
        stress = f_total / width
        print("Stress=" + str(round(stress, 2))),

        # Determine the K_I
        K_I = stress_intensity_factor(stress, a, width)
        normalized = K_I / critical_sif
        print("K_I=" + str(round(normalized)))

        # Write the data to a file:
        f.write(str(a / width) + "\t" + str(normalized) + "\n")
f.close()


# ===============================================
# Find crack path in final frame
# ===============================================

x_array = []
y_array = []

frame = odb.steps.values()[-1].frames[-1]
coords = frame.fieldOutputs["COORD"]
csdmg = frame.fieldOutputs["CSDMG    General_Contact_Faces/General_Contact_Faces"]
for i in range(len(csdmg.values)):
    if csdmg.values[i].data > dmg_thresh:
        x_array.append(coords.values[i].data[0])
        y_array.append(coords.values[i].data[1])
# abaqus python returns values as numpy floats,
# so we need to make them native before serialization
x_array = [float(i) for i in x_array]
y_array = [float(i) for i in y_array]
json_data = {
    "title": os.path.basename(odb.name).split(".")[0],
    "type": "scatter",
    "color": "red",
    "x_values": x_array,
    "y_values": y_array,
    "num_failed_nodes": len(x_array),
    "mesh_size": mesh_size,
    "crack_path_length": len(x_array) * mesh_size,
}
json.dump(json_data, open("crack_path.json", "w"))

odb.close()
