#!/bin/bash

#SBATCH --job-name=Lshape_tri
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=5GB
#SBATCH --array=0-4
#SBATCH --time=12:00:00
#SBATCH --output=./logs/Lshape_tri-%A-%a.out

module purge

problem_arr=(Lshape_tri)
visc_arr=(0.01 0.005 0.002 0.001 0.0005)
method_arr=(split)
max_arr=(6 6 5)
min_arr=(5 1 1)
ref_arr=($(seq 0 1 30))

extra_statement=""

module load gcc/10.2.0
module load cmake/3.18.4
module load intel/19.1.2
module load boost/intel/1.74.0

export CC=${GCC_ROOT}/bin/gcc
export CXX=${GCC_ROOT}/bin/g++

export OMP_NUM_THREADS=16

num_problems=${#problem_arr[*]}
len_visc=${#visc_arr[*]}
len_method=${#method_arr[*]}
len_ref=${#ref_arr[*]}

for (( p=0; p<$num_problems; p++ ))
do
    for (( i=0; i<$len_visc; i++ ))
    do
        export visc=${visc_arr[$i]}
        # export maxtime=${time_arr[$i]}
        for (( j=0; j<$len_method;  j++ ))
        do
            export method=${method_arr[$j]}
            export idx=`expr $j + $i \* $len_method + $p \* $len_method \* $len_visc` 
            if [ ${idx} == ${SLURM_ARRAY_TASK_ID} ]
            then
                for (( k=0; k<$len_ref;  k++ ))
                do
                    export ref=${ref_arr[$k]}
                    if [ $ref -le ${max_arr[$j]} -a ${min_arr[$j]} -le $ref ]
                    then
                        printf '%s\n' "python run.py ${ref} -s ${method} -p ${problem_arr[$p]} -v ${visc} ${extra_statement}"
                        workdir=$(singularity exec \
                        --overlay $SCRATCH/fluid/model-problems/plot.ext3:ro \
                        /scratch/work/public/singularity/cuda11.1-cudnn8-devel-ubuntu18.04.sif \
                        /bin/bash -c \
                        "
                        source /ext3/miniconda3/etc/profile.d/conda.sh
                        conda activate plot
                        cd /home/zh1476/fluid/model-problems/polyfem
                        python run.py ${ref} -s ${method} -p ${problem_arr[$p]} -v ${visc} ${extra_statement}")

                        cd $workdir
                        /scratch/zh1476/fluid/polyfem/build/PolyFEM_bin --json ${workdir}/run.json --cmd
                    fi
                done
            fi
        done
    done
done
