# call with python3 max_increment.py {name} {I_0} {I_R}
from sys import argv

if len(argv) != 4:
    print("Usage: python3 max_increment.py name I_0 I_R")
    exit(1)


name = argv[1]
I_0 = int(argv[2])
I_R = int(argv[3])
to_insert = f"*CONTROLS, PARAMETERS=TIME INCREMENTATION\n{I_0}, {I_R}\n"

# read in the file
with open(f"{name}.inp", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "*Controls, analysis=discontinuous" in line:
        lines.insert(i + 1, to_insert)

with open(f"{name}.inp", "w") as f:
    f.writelines(lines)
