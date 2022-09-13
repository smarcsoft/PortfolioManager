. .\vars.ps1
Write-Host -NoNewline "Getting the public DNS name of the instance..."
Invoke-Expression "aws ec2 describe-instances --region us-east-1 --query `"Reservations[].Instances[?InstanceId=='$instance_id'].PublicIpAddress[]|[0]`"" -OutVariable out | Tee-Object -Variable out 
$dns = $out.Trim('"')
ssh -i C:\Users\sebma\OneDrive\dev\aws\PMsmarcsoft.pem smarcsoft@$($dns)