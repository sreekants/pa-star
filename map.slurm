#!/bin/bash

#SBATCH --job-name=8123-perfrun
#SBATCH --time=08:00:00
#SBATCH --partition=CPUQ
#SBATCH --account=share-ie-idi
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --output=perfrun_map_%j.log

cd ${SLURM_SUBMIT_DIR}

module purge
module load Python/3.11.3-GCCcore-12.3.0
source .venv/bin/activate

if [ ! -d data ]; then
   mkdir data
fi

if [ ! -d build ]; then
   mkdir build
fi

python app/map.py --header

srun --ntasks=8 --wait=0 --multi-prog ./file.conf
