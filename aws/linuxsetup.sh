#!/bin/bash

. $(dirname "$0")/vars.sh
curdir=$(dirname "$0")

CONF_FILE=$curdir/../backend/config/pm.conf
echo "Creating python virtual environment..."
python3.10 -m venv smarcsoft
source smarcsoft/bin/activate
echo "Make 3.10 the default python"
ln -fs /usr/local/bin/python3.10 smarcsoft/bin/python3
echo "Upgrading pip..."
python -m pip install --upgrade pip
echo "Installing EOD..."
python -m pip install eod
echo "Installing pyodbc..."
python -m pip install pyodbc
echo "Creating log directory..."
mkdir -p $curdir/../backend/log
echo -n "Getting private IP address of database server to update configuration file..."
dbip=$(aws ec2 describe-instances --instance-ids $db_id --query Reservations[].Instances[].PrivateIpAddress[] --output text)
echo $dbip
echo -n "Updating configuration file $CONF_FILE..."
cp $CONF_FILE $CONF_FILE.bak
sed "s/\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)/$dbip/" $CONF_FILE.bak > $CONF_FILE
echo "done"
echo -n "Updating configuration variables..."
computeip=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].PublicIpAddress[] --output text)
cp $curdir/vars.sh $curdir/vars.bak
sed "s/\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)/$computeip/" $curdir/vars.bak > $curdir/vars.sh
rm $curdir/vars.bak
echo "done"
