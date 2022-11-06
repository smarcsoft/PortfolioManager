$script_dir = Split-Path $MyInvocation.MyCommand.Path -Parent
$base_dir = Split-Path $script_dir -Parent
$base_dir = Split-Path $base_dir -Parent
$Env:PYTHONPATH = "$base_dir\backend\api;$base_dir\utils"
$Env:DB_LOCATION= "$base_dir\backend\db"
Write-Host "Starting jupiter lab..."
Write-Host "Base directory:$base_dir"
Write-Host "PYTHONPATH:$Env:PYTHONPATH"
Write-Host "DB_LOCATION:$Env:DB_LOCATION"
jupyter-lab --no-browser --notebook-dir=notebooks