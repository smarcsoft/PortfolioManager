#!/bin/bash

POSITIONAL_ARGS=()
NO_INFRA=0
CONFIGFILE="config/controller.json"
TYPE="price"
BATCH=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --no-infra)
      NO_INFRA=1
      shift # past argument
      ;;
    --type)
      TYPE="$2" #price or fundamental_data
      shift
      shift
      ;;
     --batch)
      BATCH="--batch $2"
      shift
      shift
      ;;
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


if [ $NO_INFRA -eq 0 ]
then
    echo "Starting AWS infrastructure"
    $(dirname "$0")/start_infra.sh
fi
echo "Executing feeder on $TYPE..."
#Get the public IP of the compute server
backend_ip=$(aws ec2 describe-instances --instance-ids i-0a3774d4c3e971e64 --query Reservations[].Instances[].PublicIpAddress[] --output text)
ssh -i /home/smarcsoft/keys/PMsmarcsoft.pem -o StrictHostKeyChecking=no -o LogLevel=quiet smarcsoft@$backend_ip /home/smarcsoft/PortfolioManager/aws/run.sh --controller --type $TYPE --config $CONFIGFILE $BATCH
 
if [ $NO_INFRA -eq 0 ]
then
    echo "Stopping AWS infrastructure"
    $(dirname "$0")/stop_infra.sh
fi
