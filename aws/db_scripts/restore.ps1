param ([switch]$notarfetch, $exchange, [switch]$keeptarball)

if($exchange) {
    Write-Host "Restoring latest database tarball containing the $exchange exchange"
    if(-not $notarfetch.IsPresent) {
        Write-Host "Fetching tar ball from remote file system..."
        aws s3 cp s3://smarcsoftportfoliomanager/db_$exchange.tar ../../backend
    } else
    {
        Write-Host "Using the tar ball from local file system..."
    }
} else
{
    Write-Host "Restoring latest database tarball containing the entire database"
    if(-not $notarfetch.IsPresent) {
        Write-Host "Fetching tar ball from remote file system..."
        aws s3 cp s3://smarcsoftportfoliomanager/db.tar ../../backend
    } else
    {
        Write-Host "Using the tar ball from local file system..."
    }
}
Set-Location ../../backend
if($exchange) {
    $tarball="db_$exchange.tar"
} else {
    $tarball="db.tar"
}
Write-Host "Extracting $tarball..."
7z x $tarball -y
Write-Host "Done"

if(-not $keeptarball.IsPresent) {
Remove-Item $tarball
}
if($exchange) {
    Write-Host "Removing $exchange exchange"
    Remove-Item -Recurse -Force db/EQUITIES/$exchange
    Move-Item -Path .\home\smarcsoft\PortfolioManager\backend\db\EQUITIES\$exchange -Destination .\db\EQUITIES\$exchange
}
else {
    Write-Host "Removing old database"
    Remove-Item -Recurse -Force db
    Move-Item -Path .\home\smarcsoft\PortfolioManager\backend\db -Destination .
}
Remove-Item -Recurse -Force home
Set-Location ../aws/db_scripts