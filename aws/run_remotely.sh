#!/bin/bash
echo "Starting AWS infrastructure"
$(dirname "$0")/start_infra.sh
echo "Executing feeder..."
. $(dirname "$0")/vars.sh #to get the IP adress of the newly started server
echo "ssh -i /home/smarcsoft/keys/PMsmarcsoft.pem smarcsoft@$backend_ip /home/smarcsoft/dev/PortfolioManager/aws/run.sh --exchange VX"
#echo "Stopping AWS infrastructure"
#$(dirname "$0")/stop_infra.sh
