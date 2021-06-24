#!/bin/bash

#SBATCH --job-name=2d-dataset
#SBATCH --nodes=1
#SBATCH --tasks-per-node=16
#SBATCH --cpus-per-task=1
#SBATCH --mem=4GB
#SBATCH --array=8,7,4,1
#SBATCH --time=4:00:00
#SBATCH --output=post-%A-%a.out

module purge

# MPI version on single node with shared-memory

ntasks=$SLURM_NTASKS_PER_NODE
job_id=$SLURM_JOB_ID
# SLURM_ARRAY_TASK_ID=0
# dir=/scratch/zh1476/2d-dataset-ansys/100207_quad
idx=-1
minId=`expr $SLURM_ARRAY_TASK_ID \* 1050`
maxId=`expr $minId + 1050`

for dir in /scratch/zh1476/2d-dataset-ansys/*
do
    idx=`expr $idx + 1`
    # echo $idx $minId $maxId
    if [ $idx -ge $minId -a $idx -lt $maxId ]
    then
        cd ${dir}
        # pwd
        # echo $idx
        if [ -f tmp-1.cas ]; then
            continue
        else
            echo ${dir}
        fi
    
        /scratch/work/public/apps/prince/run-prince-apps.sh \
            /share/apps/ansys/19.0/v190/fluent/bin/fluent 2ddp -g -i run.jou -t$ntasks &

        # /scratch/work/public/apps/prince/run-prince-apps.sh \
        #     /share/apps/ansys/19.0/v190/fluent/bin/fluent 2ddp -g -i trans.jou -t0

        # Do not modify after this line

        pids=($!)

        sleep 15

        n=0
        while [ $n -lt 20 ]; do
            pids=($(pgrep -P ${pids[0]}))
            if [ ${#pids[@]} -eq $ntasks ]; then break; fi
            n=$((n+1))
        done
            
        cores=($(scontrol show hostname [$(cat /sys/fs/cgroup/cpuset/slurm/uid_${UID}/job_${job_id}/cpuset.cpus)]))

        if [ ${#pids[@]} -ne $ntasks ]; then
            echo "Number of processes does not match number of tasks"
            exit
        fi

        if [ ${#cores[@]} -ne $ntasks ]; then
            echo "Number of CPU cores do not match number of tasks"
            exit
        fi

        for((i=0; i<$ntasks; i++)); do
            taskset -pc ${cores[$i]} ${pids[$i]}
        done

        wait
    fi
done
