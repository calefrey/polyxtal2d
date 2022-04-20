# run in background with nohup python3 -u batch_submission.py &
ncores = 20
abqpath = "/usr/local/DassaultSystemes/Commands"
vol_sills_path = "/vol_sills/NFS06/cf511"
# set simulation properties
size = 80
base_prop = 50000
base_crit_disp = 1e-5
I_0, I_R = 20, 24  # simulation control parameters
base_name = ""
job_id = 0
num_replicates = 5
mod_vals = [0.2, 0.4, 0.6]
strength_ratios = [0.75, 1.25]
toughness_ratios = [0.25, 0.5, 0.75, 1.25]


import sys, os, subprocess, random
from matplotlib import pyplot as plt
from numpy import format_float_scientific

ffs_wrapper = lambda x: format_float_scientific(x, trim="-").replace(".", "_")
# replace the periods in the scientific notation with underscores so abaqus doesn't yell at us

# make sure script is using python37
if sys.version_info[0] < 3:
    print("Run this script with python3")
    sys.exit()
if sys.version_info[0] == 3 and sys.version_info[1] < 7:
    print("You need to load the python37 module")
    sys.exit()

try:  # check both paths, one for running on the cluster and one for local coding
    from . import modify

except ImportError:
    sys.path.append("/volume/NFS/cf511/polyxtal2d")
    from modify import modify  # pull from polyxtal2d folder


def slurmhdr(jobname=base_name):

    return f"""#!/bin/bash

#SBATCH --job-name={jobname}      # job name
#SBATCH --partition=SOE_sills       # partition (queue)
#SBATCH --account=sills_2
#SBATCH -t 2-12:00                  # time limit: (D-HH:MM)
#SBATCH --mem=96000                # total memory
#SBATCH -n {ncores}                 # number of tasks
#SBATCH -c 1                        # specify one CPU per task

module purge
module load python37
unset SLURM_GTIDS # otherwise Abaqus fails to run
"""


mydir = "/mnt/beegfs/cf511"
shell = lambda x, **kwargs: subprocess.run(x, shell=True, check=True, **kwargs)


seed_list = []
for i in range(num_replicates):
    cae_found = False
    while cae_found is False:
        seed = random.randint(1, 10000)
        # see if there is an existing cae file
        cae_file = (
            f"{vol_sills_path}/pregen/abq2019/size_{size}/size_{size}_seed_{seed}.cae"
        )
        if seed in seed_list:  # duplicate seed
            continue
        if os.path.isfile(cae_file):  # great, we can us it
            seed_list.append(seed)
            cae_found = True
        else:  # nope, try again
            continue
print(f"Using seeds: {seed_list}")

for mod in mod_vals:
    if not os.path.exists(str(mod)):
        os.mkdir(str(mod))

    for strength_ratio in strength_ratios:
        if not os.path.exists(f"{mod}/{strength_ratio}"):
            os.mkdir(f"{mod}/{strength_ratio}")

        for toughness_ratio in toughness_ratios:
            if not os.path.exists(f"{mod}/{strength_ratio}/{toughness_ratio}"):
                os.mkdir(f"{mod}/{strength_ratio}/{toughness_ratio}")
            for seed in seed_list:

                # pregenerated cae file
                cae_file = f"{vol_sills_path}/pregen/abq2019/size_{size}/size_{size}_seed_{seed}.cae"

                # new name for the output files
                name = (
                    f"mod_{ffs_wrapper(mod)}_"
                    f"str_ratio_{ffs_wrapper(strength_ratio)}_"
                    f"tough_ratio_{ffs_wrapper(toughness_ratio)}_"
                    f"seed_{seed}"
                )

                plt.close()
                plt.figure()  # new figure
                # do the modification
                modify(
                    cae_file,
                    name,
                    mod,
                    seed,
                    viscosity=0.002,
                    new_prop_1=base_prop,
                    new_prop_2=base_prop * strength_ratio,
                    new_crit_disp_1=base_crit_disp,
                    # \delta_m = \delta_0 \times \frac{\bar \Gamma}{\bar \sigma}
                    new_crit_disp_2=base_crit_disp * toughness_ratio / strength_ratio,
                )

                # final directory name
                dir_name = (
                    f"{os.getcwd()}/{mod}/{strength_ratio}/{toughness_ratio}/"
                    f"mod_{mod}_strength-ratio_{strength_ratio}_toughness-ratio_{toughness_ratio}seed_{seed}"
                )
                # write sbatch file
                with open(f"{name}.batch", "w") as f:
                    f.write(slurmhdr(str(job_id)))
                    f.write(f"{abqpath}/abaqus cae noGUI={name}.py\n")
                    f.write(
                        "python3 ~/polyxtal2d/utils/max_increment.py"
                        f" {name} {I_0} {I_R}\n"
                    )  # run script that modifies input file
                    f.write(
                        f"{abqpath}/abaqus job={name} cpus={ncores} mp_mode=mpi"
                        ' memory="96000 mb" scratch=. -interactive\n'
                    )
                    f.write(
                        f"{abqpath}/abaqus python"
                        f" ~/polyxtal2d/post_processing/post_processor.py {name}.odb\n"
                    )
                    f.write(
                        f"python3 ~/polyxtal2d/post_processing/node_lut.py {name}.inp\n"
                    )
                    f.write(
                        f"mv {mydir}/{name} {dir_name}\n"
                    )  # move the results back to the directory where this script is called

                shell(f"mkdir {mydir}/{name}")
                shell(f"mv {name}.* {mydir}/{name}")
                print(f"Submitted job: {name}")
                shell(
                    f"sbatch {name}.batch",
                    cwd=f"{mydir}/{name}",
                )
                print(
                    f"Submitted job {job_id} of {num_replicates*len(mod_vals)*len(strength_ratios)*len(toughness_ratios)}"
                )
                job_id += 1
