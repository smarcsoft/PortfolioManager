#!/bin/bash
#Setup the python virtual environment
. $(dirname "$0")/linuxsetup.sh >/dev/null

TYPE="currency"

#Process command line argument --exchange US
POSITIONAL_ARGS=()
CONFIG_FILE=""

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

echo "Running single feeder processing exchange(s) $EXCHANGE..."
cd $(dirname "$0")/../backend
python feeder/fxfeed.py --debug INFO 
