#!/bin/bash
. $(dirname "$0")/vars.sh

echo "Starting AWS infrastructure"
start_infra.sh
echo "Executing feeder..."
ssh -i /home/smarcsoft/keys/PMsmarcsoft.pem smarcsoft@$backend_ip /home/smarcsoft/dev/PortfolioManager/aws/run.sh
echo "Stopping AWS infrastructure"
stop_infra.sh
