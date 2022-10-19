#!/bin/bash
# This script sttop the infratructure of Portfolio Manager, and update the proxy configuration accordingly to provide access to it.

POSITIONAL_ARGS=()
NO_INFRA=0
curdir=$(dirname "$0")


configure_proxy()
{
    echo "Configuring virtual host"
    sudo cp /opt/bitnami/apache/conf/httpd.conf /opt/bitnami/apache/conf/httpd.conf.bak
    sudo python3 $curdir/configure_virtual_host.py --down
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

$curdir/stop_infra.sh

configure_proxy
#Reload apache config file
echo "Restarting reverse proxy..."
$curdir/restart_proxy.sh

