#!/bin/bash

#SBATCH --job-name=fv-mesh
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --tasks-per-node=1
#SBATCH --mem=3GB
#SBATCH --time=12:00:00

cd /home/zh1476/fluid/fluid2d/ansys-run/gmsh2fluent

# singularity exec \
# --overlay $SCRATCH/fluid/model-problems/plot.ext3:ro \
# /scratch/work/public/singularity/cuda11.1-cudnn8-devel-ubuntu18.04.sif \
# /bin/bash -c \
# "
# source /ext3/miniconda3/etc/profile.d/conda.sh
# conda activate plot
# python batch-gmsh2fluent.py"

# python refine.py

python msh2cas.py -f /scratch/zh1476/ansys_2