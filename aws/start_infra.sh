#!/bin/bash
current_dir=$(dirname "$0")

$current_dir/start_compute.sh
if [ $? -ne 0 ]
then
    exit $?
fi




