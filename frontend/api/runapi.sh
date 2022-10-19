#!/bin/bash
current_dir=$(dirname "$0")
#Setup the python virtual environment
echo "setting up python environment"
. $current_dir/../../aws/linuxsetup.sh >/dev/null

#Create log dir
mkdir -p $current_dir/log

#Updating python search path
export PYTHONPATH=$current_dir/../../utils:$PYTHONPATH
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
python $current_dir/pmapi.py 
