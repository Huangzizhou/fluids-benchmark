#!/bin/bash

#SBATCH --job-name=3d-dataset
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=5GB
#SBATCH --array=0-9
#SBATCH --time=2:00:00
#SBATCH --output=fv-%A-%a.out

module purge

# MPI version on single node with shared-memory

ntasks=$SLURM_NTASKS_PER_NODE
job_id=$SLURM_JOB_ID
# SLURM_ARRAY_TASK_ID=0
# dir=/scratch/zh1476/2d-dataset-ansys/100207_quad
idx=-1
minId=`expr $SLURM_ARRAY_TASK_ID \* 20`
maxId=`expr $minId + 20`

for file in /scratch/zh1476/ansys3d_1/*
do  
    strB="cas"
    result=$(echo $file | grep "${strB}")
    if [[ "$result" != "" ]]
    then
        continue
    fi
    idx=`expr $idx + 1`
    if [ $idx -ge $minId -a $idx -lt $maxId ]
    then
        python msh2cas.py -f $file
        # echo ${file}
    fi
done