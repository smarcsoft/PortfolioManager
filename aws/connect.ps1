param ($username='smarcsoft', $keyfile='PMsmarcsoft.pem', $server="backend")
switch ($server)
{
    "compute"
    {
        . .\vars.ps1
        Write-Host "Connecting to the main compute server"
        Write-Host -NoNewline "Getting the public DNS name of the instance..."
        Invoke-Expression "aws ec2 describe-instances --region us-east-1 --query `"Reservations[].Instances[?InstanceId=='$instance_id'].PublicIpAddress[]|[0]`"" -OutVariable out | Tee-Object -Variable out 
        $dns = $out.Trim('"')
        Write-Host "Connecting with user $username and keyfile $keyfile"
        Invoke-Expression "ssh -o StrictHostKeyChecking=no -i C:\Users\sebma\OneDrive\dev\aws\$keyfile $($username)@$($dns)" 
    }
    "scheduler"
    {
        $dns="54.171.15.30"
        Write-Host "Connecting to the scheduling server"
        Invoke-Expression "ssh -o StrictHostKeyChecking=no -i C:\Users\sebma\OneDrive\dev\aws\$keyfile $($username)@$($dns)" 
    }
    "session"
    {
        . .\vars.ps1
        Write-Host -NoNewline "Getting the public DNS name of the instance..."
        Invoke-Expression "aws ec2 describe-instances --region us-east-1 --query `"Reservations[].Instances[?InstanceId=='$session_id'].PublicIpAddress[]|[0]`"" -OutVariable out | Tee-Object -Variable out 
        $dns = $out.Trim('"')
        Write-Host "Connecting to the session server"
        Invoke-Expression "ssh -o StrictHostKeyChecking=no -i C:\Users\sebma\OneDrive\dev\aws\PortfolioManager.pem $($username)@$($dns)" 
    }
}

