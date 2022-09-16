# run in background with nohup python3 -u batch_submission.py &
ncores = 20
abqpath = "/usr/local/DassaultSystemes/Commands"
# set simulation properties
size = 80
prop_1 = 50000
prop_2 = 10000
mod_fraction = 0.2
base_name = "crack"

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

cwd = os.getcwd()
mydir = "/mnt/beegfs/cf511"

name = f"{base_name}_{size}_{prop_1}_{prop_2}"
percent = int(mod_fraction * 100)
heterogenous_name = f"{name}_mod_{percent}p"
try:
    from .. import generate, modify  # if files are in the same directory
except ImportError:
    sys.path.append("/volume/NFS/cf511/polyxtal2d")
    from homogenous import generate
    from modify import modify  # pull from polyxtal2d folder

print("Creating microstrcture")
generate(name, size, prop_1, prop_2, coh_stiffness=2e9, mesh_size=0.11)
print("Generating Homogenous CAE")
srun(f"{abqpath}/abaqus cae noGUI={name}.py")
# we now have a CAE file with built in strength properties

mod_seed = random.randint(1000, 9999)  # use same seed for all modifier trials

for prop2 in [10000, 30000, 50000, 70000, 90000]:
    print(f"Modifying {base_name}_{size}_{prop_1}_{prop_2} with {percent}% modifiers")
    heterogenous_name = f"{name}_mod_{percent}p_{prop2}"
    plt.figure()  # make a new figure so stuff doesn't carry over
    modify(
        name + ".cae", heterogenous_name, mod_fraction, new_prop_2=prop2, seed=mod_seed
    )
    print("Generating Heterogenous CAE and inp")
    srun(f"{abqpath}/abaqus cae noGUI={heterogenous_name}.py")
    with open(heterogenous_name + ".batch", "w") as f:  # write batch file
        f.write(slurmhdr)  # write header
        f.write(
            f"{abqpath}/abaqus job={heterogenous_name} cpus={ncores} mp_mode=mpi scratch=. -interactive\n"
        )  # run the inp
        f.write(
            f"{abqpath}/abaqus python ~/polyxtal2d/post_processing/post_processor.py {heterogenous_name}.odb\n"
        )  # run the r-curve txt file generator while the files are still on fast storage
        f.write(
            f"mv {mydir}/{heterogenous_name} {cwd}\n"
        )  # move the results back to the directory where this script is called

    shell(f"mkdir {mydir}/{heterogenous_name}")
    shell(
        f"mv {heterogenous_name}.* {mydir}/{heterogenous_name}"
    )  # move all files to beegfs
    shell(
        f"sbatch {heterogenous_name}.batch",
        cwd=f"{mydir}/{heterogenous_name}",
    )
