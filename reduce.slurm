#!/bin/bash

#SBATCH --job-name=reduce-perfrun
#SBATCH --time=00:05:00
#SBATCH --partition=CPUQ
#SBATCH --account=share-ie-idi
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --output=perfrun_reduce_%j.log

cd ${SLURM_SUBMIT_DIR}

module purge
module load Python/3.11.3-GCCcore-12.3.0
source .venv/bin/activate


srun python app/reduce.py
