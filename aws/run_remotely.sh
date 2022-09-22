#!/bin/bash
echo "Starting AWS infrastructure"
$(dirname "$0")/start_infra.sh
echo "Executing feeder..."
#Get the public IP of the compute server
backend_ip=$(aws ec2 describe-instances --instance-ids i-0a3774d4c3e971e64 --query Reservations[].Instances[].PublicIpAddress[] --output text)
ssh -i /home/smarcsoft/keys/PMsmarcsoft.pem -o StrictHostKeyChecking=no smarcsoft@$backend_ip /home/smarcsoft/dev/PortfolioManager/aws/run.sh --exchange VX
echo "Stopping AWS infrastructure"
$(dirname "$0")/stop_infra.sh
