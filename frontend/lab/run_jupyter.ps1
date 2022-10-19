$Env:PYTHONPATH = "..\..\..\backend\api"
$Env:DB_LOCATION= "..\..\..\backend\db"
Write-Host "Starting jupiter lab"
jupyter-lab --no-browser --notebook-dir=notebooks