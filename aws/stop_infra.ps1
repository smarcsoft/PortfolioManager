. .\vars.ps1
Write-Host -NoNewline "Stopping backend main server..."
Invoke-Expression "aws ec2 stop-instances --region $region --instance-ids $instance_id"
Write-Host "succeeded..."
Write-Host -NoNewline "Waiting for stopped status..."
# wait until the instance is running
Invoke-Expression "aws ec2 wait instance-stopped --region $region --instance-ids $instance_id"
Write-Host "instance successfully stopped"

Write-Host -NoNewline "Stopping session manager server..."
Invoke-Expression "aws ec2 stop-instances --region $region --instance-ids $session_id"
Write-Host "succeeded..."
Write-Host -NoNewline "Waiting for stopped status..."
# wait until the instance is running
Invoke-Expression "aws ec2 wait instance-stopped --region $region --instance-ids $session_id"
Write-Host "instance successfully stopped"


Write-Host -NoNewline "Stopping database server..."
Invoke-Expression "aws ec2 stop-instances --region $region --instance-ids $db_id"
Write-Host "succeeded..."
Write-Host -NoNewline "Waiting for stopped status..."
# wait until the instance is running
Invoke-Expression "aws ec2 wait instance-stopped --region $region --instance-ids $db_id"
Write-Host "instance successfully stopped"