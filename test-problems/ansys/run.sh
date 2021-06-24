#!/bin/bash

#SBATCH --job-name=fv-cavity_tri
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --tasks-per-node=16
#SBATCH --mem=5GB
#SBATCH --array=0-7
#SBATCH --time=1:00:00
#SBATCH --output=./logs/cavity_tri-%A-%a.out

module purge

# MPI version on single node with shared-memory

ntasks=$SLURM_NTASKS_PER_NODE
job_id=$SLURM_JOB_ID

visc_arr=(-1) # (0.01 0.005 0.002 0.001 0.0005)

export problem=cavity_tri
visc_id=`expr $SLURM_ARRAY_TASK_ID % ${#visc_arr[*]}`
export visc=${visc_arr[$visc_id]}
export destination=/scratch/zh1476/fluid/model-problems/ansys/
export ref=`expr $SLURM_ARRAY_TASK_ID / ${#visc_arr[*]}`

extra_statement="--cavity 0 --extra"

workdir=$(singularity exec \
--overlay $SCRATCH/fluid/model-problems/plot.ext3:ro \
/scratch/work/public/singularity/cuda11.1-cudnn8-devel-ubuntu18.04.sif \
/bin/bash -c \
"
source /ext3/miniconda3/etc/profile.d/conda.sh
conda activate plot
python get_jou.py -r ${ref} -p ${problem} -v ${visc} ${extra_statement}")

cd $workdir
pwd

for e in $(env | grep SLURM_ | cut -d= -f1); do unset $e; done

/scratch/work/public/apps/prince/run-prince-apps.sh \
    /share/apps/ansys/19.0/v190/fluent/bin/fluent 2ddp -g -i run.jou -t$ntasks -mpi=intel &

pids=($!)

sleep 20

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

/scratch/work/public/apps/prince/run-prince-apps.sh \
    /share/apps/ansys/19.0/v190/fluent/bin/fluent 2ddp -g -i trans.jou -t0


cd /home/zh1476/fluid/model-problems/ansys
rm -r $workdir

python post.py ${workdir/-tmp/}

if [ $problem != drag ]
then
    destination=${workdir/-tmp/}
    /scratch/zh1476/fluid/ensight-case-gold-to-vtu/build/fluent_vtu $destination
fi