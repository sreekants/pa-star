#!/bin/bash

#SBATCH --job-name=reduce-perfrun
#SBATCH --time=00:05:00
#SBATCH --partition=CPUQ
#SBATCH --account=share-ie-idi
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --output=perfrun_reduce_%j.log

cd ${SLURM_SUBMIT_DIR}


srun python app/reduce.py
