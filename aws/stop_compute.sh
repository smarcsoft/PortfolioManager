#!/bin/bash
. $(dirname "$0")/vars.sh

echo -n "Starting backend main server..."
aws ec2 stop-instances --instance-ids $backend_id
if [ $? -ne 0 ]
then
    echo "failed!"
    exit -1
fi
echo "succeeded"
echo -n "Waiting for stopped status..."
aws ec2 wait instance-stopped --instance-ids $backend_id
if [ $? -ne 0 ]
then
    echo "failed!"
    exit -1
fi
echo "suceeded"
