. .\vars.ps1
Write-Host -NoNewline "Starting backend main server..."
Start-EC2Instance -Region $region -InstanceId $instance_id 
if(!$?)
{
    Write-Host "failed!..."
    throw "Could not start instance $instance_id in region $region"
} 
#Invoke-Expression "aws ec2 start-instances --region $region --instance-ids $instance_id"
Write-Host "succeeded..."
Write-Host -NoNewline "Waiting for running status..."
# wait until the instance is running
Invoke-Expression "aws ec2 wait instance-running --region $region --instance-ids $instance_id"
Write-Host "instance successfully running"