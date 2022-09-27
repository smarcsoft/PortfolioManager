#!/bin/bash
PMBASEDIR=$( dirname -- "$( readlink -f -- "${BASH_SOURCE[0]}"; )"; )/../..
#Get the asbolute directory
PMBASEDIR=$(realpath $PMBASEDIR)
ROOTDIR=$(realpath $PMBASEDIR/..)

#switch to the linux environment
echo "Sourcing python virtual environment at $ROOTDIR/smarcsoft"
source $ROOTDIR/smarcsoft/bin/activate

export PYTHONPATH="$PMBASEDIR/backend/api"
export DB_LOCATION="$PMBASEDIR/backend/db"
echo "Starting jupiter lab...."
jupyter-lab --ip "*" --port=8888 --no-browser --notebook-dir=$PMBASEDIR/frontend/lab/notebooks
