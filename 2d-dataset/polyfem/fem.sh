#!/bin/bash
#
# Submit job as (build defaults to Release):
#
#   sbatch compile.sh
#   sbatch --export=BUILD='Debug',ALL compile.sh 
#
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --time=2:00:00
#SBATCH --array=0
#SBATCH --mem=5GB
#SBATCH --output=fem-%A-%a.out

# Load modules
module purge

module load gcc/10.2.0
module load cmake/3.18.4
module load intel/19.1.2
module load boost/intel/1.74.0

export CC=${GCC_ROOT}/bin/gcc
export CXX=${GCC_ROOT}/bin/g++

export PARDISO_LIC_PATH="${HOME}/.pardiso"
export PARDISO_INSTALL_PREFIX="${HOME}/.local"
export OMP_NUM_THREADS=16

python run.py -s fem -r 0 -n $SLURM_ARRAY_TASK_ID
