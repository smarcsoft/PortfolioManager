#!/bin/bash
echo "Starting frontend session API...."
cd /home/smarcsoft/PortfolioManager/frontend/api
nohup ./runapi.sh &
sleep 5
echo "Starting session web app..."
cd /home/smarcsoft/PortfolioManager/frontend/startapp
nohup ./start.sh &
cd /home/smarcsoft/PortfolioManager/frontend
