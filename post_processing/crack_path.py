# Run with abaqus python .\crack_path.py .\odb_file.odb
# Outputs the locations of cracks at the very last frame in the crack_path.txt file
# the first column is x, the second column is y

import math, os
from odbAccess import *
from sys import argv
import json

odb_filename = argv[1]
dmg_thresh = 0.999


# Objective: Generate a plot of crack length a vs stress intensity factor K
odb = openOdb(path=odb_filename, readOnly=True)

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
    "title": os.path.basename(odb.name).split(".")[0] + "_crack",
    "type": "scatter",
    "color": "red",
    "x_values": x_array,
    "y_values": y_array,
}
json.dump(json_data, open("crack_path.json", "w"))
odb.close()
