#!/bin/bash

#SBATCH --job-name=8123-perfrun
#SBATCH --time=04:00:00
#SBATCH --partition=CPUQ
#SBATCH --account=share-ie-idi
#SBATCH --nodes=3
#SBATCH --cpus-per-task=1
#SBATCH --output=perfrun_map_%j.log

cd ${SLURM_SUBMIT_DIR}

if [ ! -d data ]; then
   mkdir data
fi

if [ ! -d build ]; then
   mkdir build
fi

python app/map.py --header

srun --ntasks=8 --multi-prog ./file.conf
