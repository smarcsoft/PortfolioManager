#!/bin/bash
# This script starts the infratructure to run Portfolio Manager, run it and update the proxy configuration accordingly to provide access to it.

POSITIONAL_ARGS=()
NO_INFRA=0
curdir=$(dirname "$0")


configure_proxy()
{
    PUBLIC_IP=$1
    PRIVATE_IP=$2
    echo "Configuring reverse proxy with public IP $PUBLIC_IP and private IP $PRIVATE_IP"
    python3 $curdir/configure_proxy.py --public $PUBLIC_IP --private $PRIVATE_IP
    echo "Configuring virtual host"
    sudo cp /opt/bitnami/apache/conf/httpd.conf /opt/bitnami/apache/conf/httpd.conf.bak
    sudo python3 $curdir/configure_virtual_host.py --up
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --no-infra)
      NO_INFRA=1
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


if [ $NO_INFRA -eq 1 ]
then
    # Check if infrastructure is already started.
    INFRA_STARTED=$($curdir/start_compute.sh --check)
    if [ $INFRA_STARTED = "not_started" ]
    then
	echo "AWS infrastructure has not been started. Exiting..."
	exit -1
    fi
else
    INFRA_STARTED=$($curdir/start_compute.sh --check --ips)
    if [ $INFRA_STARTED = "not_started" ]
    then
	echo "Starting AWS infrastructure..."
	INFRA_STARTED=$($curdir/start_compute.sh --silent --ips)
    fi
    #Get the IP addresses of the compute server to update the reverse proxy
    IPS=($(echo $INFRA_STARTED | tr ',' ' '))
    PUBLIC_IP=${IPS[0]}
    PRIVATE_IP=${IPS[1]}
    configure_proxy $PUBLIC_IP $PRIVATE_IP
    echo "Starting jupiter asynchronously..."
    $curdir/run_jupiter.sh --no-infra &
    sleep 5
    #Reload apache config file
    echo "Restarting reverse proxy..."
    $curdir/restart_proxy.sh
 fi

