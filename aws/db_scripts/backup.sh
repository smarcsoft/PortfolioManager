#!/bin/bash
PMBASEDIR=$( dirname -- "$( readlink -f -- "${BASH_SOURCE[0]}"; )"; )/../..
PMBASEDIR=$(realpath $PMBASEDIR)
echo "Creating tar ball..."
tar cvf db.tar $PMBASEDIR/backend/db
echo "Backing up database to s3://smarcsoftportfoliomanager"
aws s3 cp db.tar s3://smarcsoftportfoliomanager
rm db.tar
