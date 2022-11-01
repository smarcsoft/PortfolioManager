#!/bin/bash
#Setup the python virtual environment
. $(dirname "$0")/linuxsetup.sh >/dev/null

#Updating python search path
EXCHANGE=US
CONTROLLER=0
CONFIGFILE="config/controller.json"
TYPE="price"

#Process command line argument --exchange US
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--exchange)
      EXCHANGE="$2"
      shift # past argument
      shift # past value
      ;;
    -c|--controller)
      CONTROLLER=1
      shift
      ;;
    --config)
      CONFIGFILE="$2"
      shift # past argument
      shift # past value
      ;;
    --type)
      TYPE="$2"
      shift
      shift
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

if [ $CONTROLLER -eq 0 ]
then
    echo "Running single feeder processing exchange(s) $EXCHANGE..."
    cd $(dirname "$0")/../backend
    python feeder/feeder.py --debug INFO --exchange $EXCHANGE --update
else
    echo "Running single controller feeder..."
    cd $(dirname "$0")/../backend
    python controlFeed.py --debug INFO --load $TYPE --config $CONFIGFILE
fi
