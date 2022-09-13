set region=us-east-1
echo "Starting backend main server..."
aws ec2 start-instances --region %region% --instance-ids i-0a3774d4c3e971e64