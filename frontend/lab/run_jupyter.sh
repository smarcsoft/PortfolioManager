#!/bin/bash
PMBASEDIR=$( dirname -- "$( readlink -f -- "${BASH_SOURCE[0]}"; )"; )/../..
#Get the asbolute directory
PMBASEDIR=$(realpath $PMBASEDIR)
ROOTDIR=$(realpath $PMBASEDIR/..)
BACKGROUND=0

#switch to the linux environment
echo "Sourcing python virtual environment at $ROOTDIR/smarcsoft"
source $ROOTDIR/smarcsoft/bin/activate

export PYTHONPATH="$PMBASEDIR/backend/api"
export DB_LOCATION="$PMBASEDIR/backend/db"


while [[ $# -gt 0 ]]; do
  case $1 in
    --background)
      BACKGROUND=1
      shift # past argument
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done


if [ $BACKGROUND -eq 0 ]
then
    echo "Starting jupiter server...."
    jupyter server --notebook-dir=$PMBASEDIR/frontend/lab/notebooks
else
    echo "Starting jupiter server as a background process..."
    jupyter server --notebook-dir=$PMBASEDIR/frontend/lab/notebooks&
fi

