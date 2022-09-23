#!/bin/bash
#Setup the python virtual environment
. $(dirname "$0")/linuxsetup.sh >/dev/null

echo "Running portfolio manager update process..."
cd $(dirname "$0")/../backend
python feeder/feeder.py --debug INFO --exchange $EXCHANGE --update
