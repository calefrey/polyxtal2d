#!/bin/bash

# TEMPLATE FOR BATCH JOB SUBMISSION WITH ABAQUS ON SOE CLUSTERS
# EVERYTHING WITH *** NEEDS TO BE CUSTOMIZED FOR EACH SIMULATION

#number of cores
#ALWAYS USE AN EVEN NUMBER OF CORES FOR ABAQUS
ncores=20

#full path to abaqus executable
abqpath=/usr/local/DassaultSystemes/Commands

# set simulation properties
size=20
prop_1=50000
prop_2=10000
mod_fraction=.2
base_name=autocrack

cat >slurmhdr <<EOF1
#!/bin/bash

#SBATCH --job-name=$base_name        # job name
#SBATCH --partition=SOE_sills       # partition (queue)
#SBATCH --account=sills_2
#SBATCH -t 7-00:00                  # time limit: (D-HH:MM)
#SBATCH --mem-per-cpu=10000         # memory per cpu in MB (usually 10000 is sufficient, each node has 192000 MB)
#SBATCH -n $ncores                  # number of tasks
#SBATCH -c 1                        # specify one CPU per task

module purge
module load python37
unset SLURM_GTIDS # otherwise Abaqus fails to run
EOF1

#MAKE DIRECTORY VARIABLES
#current workding directory where this script is called
cwd=${PWD}
#beegfs folder for runtime storage
mydir="/mnt/beegfs/$USER"
name=${base_name}_${size}_${prop_1}_${prop_2} # generate name for simulation based on parameters
percent=$(python -c "print(int(100*$mod_fraction))")
heterogenous_name="${base_name}_mod_${percent}p" # generate name for heterogenous simulation

module load python37 # need to make python3 point to python37
echo "creating microstructure"
python3 ~/polyxtal2d/homogenous.py $name $size $prop_1 $prop_2 # create microstructure model and python script to geneate cae
echo "Generating homogenous CAE"
srun -A sills_2 -p SOE_sills --mem=10000 $abqpath/abaqus cae noGUI=$name.py # run the py -> cae process as a single-core job on a compute node
echo "writing modifier script"
python3 ~/polyxtal2d/modify.py $heterogenous_name $name.cae $mod_fraction # modify the microstructure model
echo "Generating heterogenous inp file"
srun -A sills_2 -p SOE_sills --mem=10000 $abqpath/abaqus cae noGUI=$heterogenous_name.py # run the python script to add modifiers and generate .inp files
# we now have an inp file named $heterogenous_name.inp

#MAKE THE WORKING DIRECTORY
mkdir $mydir/$heterogenous_name

# Create the batch file
cp slurmhdr $heterogenous_name.batch # add slurm header to batch file
cat >>$heterogenous_name.batch <<EOF2
$abqpath/abaqus job=$heterogenous_name cpus=$ncores mp_mode=mpi scratch=. -interactive # run the .inp
mv $mydir/$heterogenous_name/* $cwd                                       # move the results back to the directory where this script is called
EOF2

#Move  input file and slurm file to beegfs folder
mv $heterogenous_name.inp $mydir/$heterogenous_name
mv $heterogenous_name.batch $mydir/$heterogenous_name

#MOVE INTO THE WORKING DIRECTORY, CALL SLURM, AND MOVE BACK
cd $mydir/$heterogenous_name
sbatch $heterogenous_name.batch
cd $cwd

rm slurmhdr
