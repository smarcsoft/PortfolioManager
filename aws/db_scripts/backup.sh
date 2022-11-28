#!/bin/bash
PMBASEDIR=$( dirname -- "$( readlink -f -- "${BASH_SOURCE[0]}"; )"; )/../..
PMBASEDIR=$(realpath $PMBASEDIR)

POSITIONAL_ARGS=()
EXCHANGE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--exchange)
      EXCHANGE="$2"
      shift # past argument
      shift # past value
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

if [ -n "${EXCHANGE}" ]                                                                                                              
then
    echo "Creating tar ball for exchange $EXCHANGE"
    tar cvf db_$EXCHANGE.tar $PMBASEDIR/backend/db/EQUITIES/$EXCHANGE
    echo "Backing up database to s3://smarcsoftportfoliomanager"                                                                                                                                                                                                                 aws s3 cp db.tar s3://smarcsoftportfoliomanager                                                                                                                                                                                                                              rm db_$EXCHANGE.tar
else
    echo "Creating tar ball for all the database..."
    tar cvf db.tar $PMBASEDIR/backend/db
    echo "Backing up database to s3://smarcsoftportfoliomanager"
    aws s3 cp db.tar s3://smarcsoftportfoliomanager
    rm db.tar
fi
