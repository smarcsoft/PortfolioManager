. .\vars.ps1

Write-Host -NoNewline "Starting session server..."
Start-EC2Instance -Region $region -InstanceId $session_id 
if(!$?)
{
    Write-Host "failed!..."
    throw "Could not start instance $session_id in region $region"
} 
#Invoke-Expression "aws ec2 start-instances --region $region --instance-ids $instance_id"
Write-Host "succeeded..."
Write-Host -NoNewline "Waiting for running status..."
# wait until the instance is running
Invoke-Expression "aws ec2 wait instance-running --region $region --instance-ids $session_id"
Write-Host "instance successfully running"