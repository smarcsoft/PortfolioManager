param ([switch]$notarfetch)
Write-Host "Restoring latest database tarball"
if(-not $notarfetch.IsPresent) {
    Write-Host "Fetching tar ball from remote file system..."
    aws s3 cp s3://smarcsoftportfoliomanager/db.tar ../../backend
} else
{
    Write-Host "Using the tar ball from local file system..."
}
Set-Location ../../backend
Write-Host "Extracting..."
7z x db.tar -y
Write-Host "Done"
if(-not $notarfetch.IsPresent) {
Remove-Item db.tar
}
Write-Host "Removing old database"
Remove-Item -Recurse -Force db
Move-Item -Path .\home\smarcsoft\PortfolioManager\backend\db -Destination .
Remove-Item -Recurse -Force home
Set-Location ../aws/db_scripts