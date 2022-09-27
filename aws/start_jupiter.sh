#!/bin/bash
backend_ip=$(aws ec2 describe-instances --instance-ids i-0a3774d4c3e971e64 --query Reservations[].Instances[].PublicIpAddress[] --output text)
ssh -i /home/smarcsoft/keys/PMsmarcsoft.pem -o StrictHostKeyChecking=no smarcsoft@$backend_ip /home/smarcsoft/PortfolioManager/frontend/lab/run_jupiter.sh
