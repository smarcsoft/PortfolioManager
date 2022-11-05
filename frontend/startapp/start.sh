#!/bin/bash
current_dir=$(dirname "$0")
cd $current_dir
sudo PORT=80 node ./node_modules/.bin/react-scripts start
