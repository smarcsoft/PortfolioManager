#!/bin/bash

POSITIONAL_ARGS=()
NO_INFRA=0
CONFIGFILE=""
NOEXEC=0
CONFIG=""
LOCAL=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --no-infra)
      NO_INFRA=1
      shift # past argument
      ;;
    --local)
      LOCAL=1
      shift # past argument
      ;;
    --config)
      CONFIGFILE="$2"
      shift # past argument
      shift # past value
      ;;
    --no-exec)
      NOEXEC=1
      shift
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
echo "Executing indexeer..."
#Get the public IP of the compute server
backend_ip=$(aws ec2 describe-instances --instance-ids i-0a3774d4c3e971e64 --query Reservations[].Instances[].PublicIpAddress[] --output text)

if [ -n "${CONFIGFILE}" ]
then
    CONFIG="--config $CONFIGFILE"
fi

COMMANDLINE=""
if [ $LOCAL -eq 1 ]
then
    echo "Running indeer..."
    cd $(dirname "$0")/../backend
    python indexer/indexer.py --debug INFO $CONFIG
else
    COMMANDLINE="ssh -i /home/smarcsoft/keys/PMsmarcsoft.pem -o StrictHostKeyChecking=no -o LogLevel=quiet smarcsoft@$backend_ip /home/smarcsoft/PortfolioManager/aws/indexer.sh --local $CONFIG"
fi

if [ $NOEXEC -eq 1 ]
then
    echo $COMMANDLINE
else
    $COMMANDLINE
fi
 
if [ $NO_INFRA -eq 0 ]
then
    echo "Stopping AWS infrastructure"
    $(dirname "$0")/stop_infra.sh
fi
