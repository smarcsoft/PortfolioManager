#!/bin/bash
. $(dirname "$0")/vars.sh

echo -n "Starting backend main server..."
aws ec2 start-instances --instance-ids $backend_id
if [ $? -ne 0 ]
then
    echo "failed!"
    exit -1
fi
echo "succeeded"
echo -n "Waiting for running status..."
aws ec2 wait instance-running --instance-ids $backend_id
if [ $? -ne 0 ]
then
    echo "failed!"
    exit -1
fi
echo "suceeded"
