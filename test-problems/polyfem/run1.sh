#!/bin/bash

#SBATCH --job-name=split-Lshape_tri
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=5GB
#SBATCH --array=5-6
#SBATCH --time=5:00:00
#SBATCH --output=./logs/split-Lshape_tri-%A-%a.out

module purge

module load gcc/10.2.0
module load cmake/3.18.4
module load intel/19.1.2
module load boost/intel/1.74.0

export CC=${GCC_ROOT}/bin/gcc
export CXX=${GCC_ROOT}/bin/g++

export OMP_NUM_THREADS=16
export destination=/scratch/zh1476/fluid/model-problems/

source /share/apps/anaconda3/2020.07/etc/profile.d/conda.sh
conda activate

ref=$SLURM_ARRAY_TASK_ID
command="python run.py $ref -s split -p Lshape_tri"

workdir=$(singularity exec \
--overlay $SCRATCH/fluid/model-problems/plot.ext3:ro \
/scratch/work/public/singularity/cuda11.1-cudnn8-devel-ubuntu18.04.sif \
/bin/bash -c \
"
source /ext3/miniconda3/etc/profile.d/conda.sh
conda activate plot
${command}")

cd $workdir

/scratch/zh1476/fluid/polyfem/build/PolyFEM_bin --json ${workdir}/run.json --cmd
