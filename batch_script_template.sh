#!/bin/bash
# TEMPLATE FOR BATCH JOB SUBMISSION WITH ABAQUS ON SOE CLUSTERS
# EVERYTHING WITH *** NEEDS TO BE CUSTOMIZED FOR EACH SIMULATION

#number of cores
#ALWAYS USE AN EVEN NUMBER OF CORES FOR ABAQUS
ncores=4

#name of the template file

#executable name
exe=abaqus

#full path to the executable
exedir=/usr/local/DassaultSystemes/Commands

#WRITE THE SLURM HEADER INFO
cat >slurmhdr <<EOF1
#!/bin/bash

#SBATCH --job-name=voronoi_test          # job name
#SBATCH --partition=SOE_sills   # partition (queue)
#SBATCH --account=sills_2
#SBATCH -t 1-00:00            # time limit: (D-HH:MM)
#SBATCH --mem-per-cpu=10000       # memory per cpu in MB (usually 10000 is sufficient, each node has 192000 MB)
#SBATCH -n $ncores              # number of tasks
#SBATCH -c 1                    # specify one CPU per task

module purge
module load python37
unset SLURM_GTIDS               # otherwise Abaqus fails to run
EOF1

#pull the code repo first to get the latest changes
git -C ~/polyxtal2d/ pull

#MAKE DIRECTORY VARIABLES
#current workding directory where this script is called
cwd=$(pwd)

#beegfs folder for runtime storage
mydir="/mnt/beegfs/$USER"

#DEFINE SIMULATION PARAMETERS
size=20

#LOOP OVER SOME VARIABLES
for p1 in 1000 10000 100000; do #(ex: 1 2 3 loops over 1, 2, and 3)
    for p2 in 1000 10000 100000; do
        #repeat as necessary

        #define a name based on the specified parameters
        name="size_${size}_prop_1_${p1}_prop_2_${p2}"

        #WRITE THE SLURM BATCH FILE, WHICH WILL COPY FILES INTO STORAGE AT THE END OF THE RUN
        cp slurmhdr $name.batch
        echo "python3 ~/vol_sills/scripted/voronoi_gen.py $name $size $p1 $p2" >>$name.batch        # generate the python script
        echo "$exedir/$exe cae noGUI=${name}.py" >>$name.batch                                      # run the python script to generate the .inp
        echo "$exedir/$exe job=$name cpus=$ncores mp_mode=mpi scratch=. -interactive" >>$name.batch # run the .inp
        echo "cd ..; cp -r $name $cwd; rm -r $name" >>$name.batch
        echo "~/pushover-cli $name 'Job Completed'" >>$name.batch

        #MAKE THE WORKING DIRECTORY
        mkdir $mydir/$name

        #COPY INPUT FILE, SLURM FILE, AND EXECUTABLE TO THE WORKING DIRECTORY
        mv $name.batch $mydir/$name

        #MOVE INTO THE WORKING DIRECTORY, CALL SLURM, AND MOVE BACK
        cd $mydir/$name
        sbatch $name.batch
        cd $cwd

    done
done

rm slurmhdr
