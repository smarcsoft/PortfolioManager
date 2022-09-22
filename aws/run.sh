#!/bin/bash
#Setup the python virtual environment
. $(dirname "$0")/linuxsetup.sh >/dev/null

#Updating python search path
EXCHANGE=US

#Process command line argument --exchange US
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--exchange)
      EXCHANGE="$2"
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

echo "Processing exchange(s) $EXCHANGE..."
cd $(dirname "$0")/../backend
python feeder/feeder.py --debug INFO --exchange $EXCHANGE --update
