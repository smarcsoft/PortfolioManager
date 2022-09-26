#!/bin/bash
. $(dirname "$0")/vars.sh

echo -n "Starting database server..."
aws ec2 start-instances --instance-ids $db_id
if [ $? -ne 0 ]
then
    echo "failed!"
    exit -1
fi
echo "succeeded"

echo -n "Waiting for running status..."
aws ec2 wait instance-running --region $region --instance-ids $db_id
if [ $? -ne 0 ]
then
    echo "failed!"
    exit -1
fi
echo "suceeded"
