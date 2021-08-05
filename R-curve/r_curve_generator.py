# Run with abaqus python .\r_curve_generator.py .\precrack.odb
#  r-curve.txt will be created in this directory with the values of a/w and K_I


import math, os
from odbAccess import *
from sys import argv

# PROPERTIES TO CHANGE ========================
a0 = 5  # initial crack depth, be conservative
strength = 50000  # primary property cohesive strength
modulus = 1e9  # under traction separaton behaivor in the contact property
critical_displacement = 1e-05  # total plastic displacement
# ==============================================


dmg_thresh = 0.999


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
odb = openOdb(path=argv[1], readOnly=True)
try:  # we append to the file, so if there's already one, delete it
    os.remove("r-curve.txt")
except OSError:  # file already deleted
    pass

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
            if (
                csdmg.values[i].data > dmg_thresh
                and coords.values[i].data[0] > current_a
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
        with open("r-curve.txt", "a") as f:
            f.write(str(a / width) + "\t" + str(normalized) + "\n")
odb.close()
