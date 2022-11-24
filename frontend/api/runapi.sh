#!/bin/bash
current_dir=$(dirname "$0")
#Setup the python virtual environment
echo "setting up python environment"
. $current_dir/../../aws/update_infra.sh

#Create log dir
mkdir -p $current_dir/log

CONFIGFILE="$currentdir/config/pmapi.conf"

#Process command line argument --exchange US
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --config)
      CONFIGFILE="$2"
      shift # past argument
      shift # past value
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

echo "Running frontend API..."
cd $current_dir
python $current_dir/pmapi.py 
