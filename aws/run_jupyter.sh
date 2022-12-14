#!/bin/bash

POSITIONAL_ARGS=()
NO_INFRA=0
BACKGROUND=

while [[ $# -gt 0 ]]; do
  case $1 in
    --no-infra)
      NO_INFRA=1
      shift # past argument
      ;;
    --background)
      BACKGROUND='--background'
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


if [ $NO_INFRA -eq 0 ]
then
    echo "Starting AWS compute server"
    $(dirname "$0")/start_compute.sh
fi
echo "Executing jupiter on compute server ..."
#Get the public IP of the compute server
backend_ip=$(aws ec2 describe-instances --instance-ids i-0a3774d4c3e971e64 --query Reservations[].Instances[].PublicIpAddress[] --output text)
ssh -i /home/smarcsoft/keys/PMsmarcsoft.pem -o StrictHostKeyChecking=no smarcsoft@$backend_ip /home/smarcsoft/PortfolioManager/frontend/lab/run_jupyter.sh $BACKGROUND

