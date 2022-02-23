import json, time
from find_node_properties import node_toughness

from sys import argv

# python3 node_lut.py <inp_file>
try:
    inp_filename = argv[1]
    print(f"Reading {inp_filename}")
    with open(inp_filename, "r") as f:
        inp_lines = f.readlines()
except IndexError:
    print("Usage: python3 node_lut.py <inp_file>")
    exit(1)

node_ids = json.load(open("job_data.json"))["node_ids"]

start_time = time.time()
lut = {}
total = len(node_ids)
print("total nodes: ", total)
for i, node in enumerate(node_ids):
    try:
        lut[node] = node_toughness(node, inp_lines=inp_lines, debug=False)
        if i % 100 == 0:
            print(f"Processed {i}/{total}: {i/total*100:.2f}%")
    except ValueError as e:
        print(e)
        json.dump(lut, open("node_lut.json", "w"))
        exit()


json.dump(lut, open("node_lut.json", "w"))
