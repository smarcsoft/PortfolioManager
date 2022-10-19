#!/bin/bash

PMBASEDIR=$( dirname -- "$( readlink -f -- "${BASH_SOURCE[0]}"; )"; )/..
#Get the asbolute directory
PMBASEDIR=$(realpath $PMBASEDIR)
echo "Base directory set to $PMBASEDIR"
# source common variables (needed to get the database instance ID refered to below
. $PMBASEDIR/aws/vars.sh
CONF_FILE=$PMBASEDIR/backend/config/pm.conf
echo "Creating python virtual environment..."
CWD=$(pwd)
cd $PMBASEDIR
python3.10 -m venv smarcsoft
source smarcsoft/bin/activate
echo "Make 3.10 the default python"
ln -fs /usr/local/bin/python3.10 smarcsoft/bin/python3
cd $CWD
echo "Upgrading pip..."
python -m pip install --upgrade pip
echo "Installing EOD..."
python -m pip install eod
echo "Installing jupyther lab..."
pip install jupyterlab
echo "Installing jupyter notebook..."
pip install notebook
echo "Installing voila..."
pip install voila
echo "Installing pyodbc..."
python -m pip install pyodbc
echo "Creating log directory from $PMBASEDIR..."
mkdir -p $PMBASEDIR/backend/log
echo "Getting private IP address of database server $db_id to update configuration file..."
dbip=$(aws ec2 describe-instances --instance-ids $db_id --query Reservations[].Instances[].PrivateIpAddress[] --output text)
echo $dbip
echo "Updating configuration file $CONF_FILE..."
cp $CONF_FILE $CONF_FILE.org
cp $CONF_FILE $CONF_FILE.bak
sed "s/\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)/$dbip/" $CONF_FILE.bak > $CONF_FILE
rm $CONF_FILE.bak
echo "Updating configuration variables..."
computeip=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].PublicIpAddress[] --output text)
cp $PMBASEDIR/aws/vars.sh $PMBASEDIR/aws/vars.bak
sed "s/\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)/$computeip/" $PMBASEDIR/aws/vars.bak > $PMBASEDIR/aws/vars.sh
rm $PMBASEDIR/aws/vars.bak
echo "done"
