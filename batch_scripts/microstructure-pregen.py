# run in background with nohup python3 -u batch_submission.py &
ncores = 1
abqpath = "/usr/local/DassaultSystemes/Commands"
# set simulation properties
size = 80
prop_1 = 50000
prop_2 = 50000
mod_fraction = 0.2
base_name = "pregen"

import sys, os, subprocess, random
from matplotlib import pyplot as plt

# make sure script is using python37
if sys.version_info[0] < 3:
    print("Run this script with python3")
    sys.exit()
if sys.version_info[0] == 3 and sys.version_info[1] < 7:
    print("You need to load the python37 module")
    sys.exit()

slurmhdr = f"""#!/bin/bash

#SBATCH --job-name={base_name}      # job name
#SBATCH --partition=SOE_sills       # partition (queue)
#SBATCH --account=sills_2
#SBATCH -t 7-00:00                  # time limit: (D-HH:MM)
#SBATCH --mem=30000                # total memory
#SBATCH -n {ncores}                 # number of tasks
#SBATCH -c 1                        # specify one CPU per task

module purge
module load python37
unset SLURM_GTIDS # otherwise Abaqus fails to run
"""


shell = lambda x, **kwargs: subprocess.run(x, shell=True, check=True, **kwargs)
srun = lambda x: shell(f"srun -A sills_2 -p SOE_sills --mem=10000 {x}")
sbatch = lambda x: shell(
    f"echo -e '#!/bin/sh \n {x}'| sbatch -A sills_2 -p SOE_sills --mem=10000"
)  # arcane bash bs

cwd = os.getcwd()
mydir = "/mnt/beegfs/cf511"

try:
    from .. import generate, modify  # if files are in the same directory
except ImportError:
    sys.path.append("/volume/NFS/cf511/polyxtal2d")
    from homogenous import generate
    from modify import modify  # pull from polyxtal2d folder)

for i in range(1, 100):  # generate 100 random microstructures
    seed = random.randint(1000, 9999)  # use same seed for all modifier trials
    print(f"Generating microstructure with seed {seed}")
    name = f"size_{size}_seed_{seed}"
    generate(name, size, prop_1, prop_2, coh_stiffness=1e10, mesh_size=0.11, seed=seed)
    print("Generating Homogenous CAE")
    sbatch(f"{abqpath}/abaqus cae noGUI={name}.py")
