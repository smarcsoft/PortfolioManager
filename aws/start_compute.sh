#!/bin/bash
. $(dirname "$0")/vars.sh


POSITIONAL_ARGS=()
INFRA_STARTED=0
CHECK=0
PUBLIC_IP=
PRIVATE_IP=
SILENT=0
DISPLAY_IPS=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --check)
      CHECK=1
      shift # past argument
      ;;
    --ips)
      DISPLAY_IPS=1
      shift # past argument
      ;;
    --silent)
      SILENT=1
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

if [ $CHECK -eq 1 ]
then
    #Check if compute server is started
    STATE=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].State.Code --output text)
    if [ $STATE -eq 16 ]
    then
	#Compute server running
	#Get its public IP
	PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].PublicIpAddress --output text)
	PRIVATE_IP=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].PrivateIpAddress --output text)
	[ $DISPLAY_IPS -eq 1 ] && echo "$PUBLIC_IP,$PRIVATE_IP"
	exit 0
    else
	echo "not_started"
	exit -1
    fi
fi

[ $SILENT -eq 0 ] && echo -n "Starting backend main server..."
aws ec2 start-instances --instance-ids $backend_id >/dev/null
if [ $? -ne 0 ]
then
    [ $SILENT -eq 0 ] && echo "failed!"
    exit -1
fi
[ $SILENT -eq 0 ] && echo "succeeded"
[ $SILENT -eq 0 ] && echo -n "Waiting for running status..."
$(aws ec2 wait instance-running --instance-ids $backend_id >/dev/null)
if [ $? -ne 0 ]
then
    [ $SILENT -eq 0 ] && echo "failed!"
    exit -1
fi
[ $SILENT -eq 0 ] && echo "suceeded"
if [ $DISPLAY_IPS -eq 1 ]
then
    PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].PublicIpAddress --output text)
    PRIVATE_IP=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].PrivateIpAddress --output text)
    echo "$PUBLIC_IP,$PRIVATE_IP"
fi
