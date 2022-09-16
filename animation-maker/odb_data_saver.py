# Run with abaqus python .\post_processor.py .\filename.odb
from odbAccess import *
from sys import argv
import json

compression = 1  # higher values run faster but skip more values
odb_filename = argv[1]
fieldOutput = argv[2]
try:
    odb = openOdb(path=odb_filename, readOnly=True)
except OdbError:
    print("Error: Could not find odb file.")
    exit(1)

x_array = []
y_array = []
data_array = []
json_data = {}
total_frames = len(odb.steps.values()[0].frames)
for frame in odb.steps.values()[-1].frames:
    print("Saving Frame " + str(frame.frameId) + " of " + str(total_frames - 1))
    coords = frame.fieldOutputs["COORD"]
    try:
        data = frame.fieldOutputs[fieldOutput]
    except KeyError:
        print("No field output named " + fieldOutput)
        exit(1)
    for i in range(len(data.values)):
        if i % compression == 0:  # low resolution
            if data.values[i].data > 0.01:
                x_array.append(coords.values[i].data[0])
                y_array.append(coords.values[i].data[1])
                data_array.append(data.values[i].data)
            else:
                pass
    # abaqus python returns values as numpy floats,
    # so we need to make them native before serialization
    x_array = [float(i) for i in x_array]
    y_array = [float(i) for i in y_array]
    data_array = [float(i) for i in data_array]
    json_data[int(frame.frameId)] = {"x": x_array, "y": y_array, "data": data_array}

print("Saving to file...")
json.dump(json_data, open("data.json", "w"), indent=4, sort_keys=True, default=str)
print("Data Saved")
