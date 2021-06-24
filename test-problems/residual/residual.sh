#!/bin/bash

#SBATCH --job-name=residual
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=48
#SBATCH --array=0
#SBATCH --time=4:00:00
#SBATCH --mem=15GB
#SBATCH --output=./logs/cavity-%A-%a.out

method_arr=(mac)
method_id=`expr $SLURM_ARRAY_TASK_ID % 5`
# ref_id=`expr $SLURM_ARRAY_TASK_ID / 5`

problem=cavity
method=${method_arr[$method_id]}
visc=0.1

# export MKL_NUM_THREADS=8
# export NUMEXPR_NUM_THREADS=8
# export OMP_NUM_THREADS=8

for (( ref=1; ref<7; ref++ ))
do
    singularity exec \
    --overlay $SCRATCH/fluid/model-problems/plot.ext3:ro \
    /scratch/work/public/singularity/cuda11.1-cudnn8-devel-ubuntu18.04.sif \
    /bin/bash -c \
    "
    source /ext3/miniconda3/etc/profile.d/conda.sh
    conda activate plot
    echo ${problem}_2d_${method}_ref${ref}_visc${visc}
    python compute-residual-parallel.py $SCRATCH/fluid/model-problems/${problem}_2d_${method}_ref${ref}_visc${visc} \
    --output ${problem}.csv --ntasks 48
    "

    # singularity exec \
    # --overlay $SCRATCH/fluid/model-problems/plot.ext3:ro \
    # /scratch/work/public/singularity/cuda11.1-cudnn8-devel-ubuntu18.04.sif \
    # /bin/bash -c \
    # "
    # source /ext3/miniconda3/etc/profile.d/conda.sh
    # conda activate plot
    # echo ${problem}_2d_${method}_ref${ref}_visc${visc}
    # python compute-residual.py $SCRATCH/fluid/model-problems/${problem}_2d_${method}_ref${ref}_visc${visc} 
    # "
done
