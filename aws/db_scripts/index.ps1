param ($exchange, $config)
$script_dir = Split-Path $MyInvocation.MyCommand.Path -Parent
$base_dir = Split-Path $script_dir -Parent
$base_dir = Split-Path $base_dir -Parent
$Env:PYTHONPATH = "$base_dir\backend\api;$base_dir\utils"
$Env:DB_LOCATION= "$base_dir\backend\db"
if ($exchange){
    Write-Host "Indexing exchange $exchange..."
    Write-Host "Base directory:$base_dir"
    Write-Host "PYTHONPATH:$Env:PYTHONPATH"
    Write-Host "DB_LOCATION:$Env:DB_LOCATION"
    $curdir = Get-Location 
    Set-Location $base_dir\backend
    python $base_dir\backend\indexer\indexer.py --debug INFO --exchange $exchange 
    Set-Location $curdir
}
else {
    Write-Host "Indexing the whole database..."
    Write-Host "Base directory:$base_dir"
    Write-Host "PYTHONPATH:$Env:PYTHONPATH"
    Write-Host "DB_LOCATION:$Env:DB_LOCATION"
    $curdir = Get-Location 
    Set-Location $base_dir\backend
    python $base_dir\backend\indexer\indexer.py --debug INFO 
    Set-Location $curdir
}
