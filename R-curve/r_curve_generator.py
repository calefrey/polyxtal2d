# Run with abaqus python .\r_curve_generator.py .\precrack.odb
#  r-curve.txt will be created in this directory with the values of a/w and K_I


import math, os
from odbAccess import *
from sys import argv


x_offset = 0.13
a0 = 0.13  # initial crack depth
width = 18.18  # width of the sample
dmg_thresh = 0.999


# Objective: Generate a plot of crack length a vs stress intensity factor K
odb = openOdb(path=argv[1], readOnly=True)
try:  # we append to the file, so if there's already one, delete it
    os.remove("r-curve.txt")
except OSError:  # file already deleted
    pass

current_a = a0


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
        print("Stress=" + str(stress)),

        # Determine the K_I
        K_I = stress_intensity_factor(stress, a, width)
        print("K_I=" + str(K_I))

        # Write the data to a file:
        with open("r-curve.txt", "a") as f:
            f.write(str(a / width) + "\t" + str(K_I) + "\n")
odb.close()
