#!/bin/bash
PMBASEDIR=$( dirname -- "$( readlink -f -- "${BASH_SOURCE[0]}"; )"; )/..
PMBASEDIR=$(realpath $PMBASEDIR)
echo "Base directory set to $PMBASEDIR"
. $PMBASEDIR/aws/vars.sh
source $PMBASEDIR/smarcsoft/bin/activate

echo "Updating configuration variables..."
computeip=$(aws ec2 describe-instances --instance-ids $backend_id --query Reservations[].Instances[].PublicIpAddress[] --output text)
# Check if compute IP is there
if [ -n "${computeip}" ]
then
    echo "Compute server IP address:$computeip"
    cp $PMBASEDIR/aws/vars.sh $PMBASEDIR/aws/vars.bak
    sed "s/\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)\.\([0-9]\+\)/$computeip/" $PMBASEDIR/aws/vars.bak > $PMBASEDIR/aws/vars.sh
else
    echo "Warning: Could not find out the IP address of the compute server. Is it started?"
fi
. $PMBASEDIR/aws/vars.sh
rm -f $PMBASEDIR/aws/vars.bak
echo "Setting up PYTHONPATH"
export PYTHONPATH=$PMBASEDIR/utils:$PMBASEDIR/backend/feeder:$PMBASEDIR/backend/api
echo "done"

