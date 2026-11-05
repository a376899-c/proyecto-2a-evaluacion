# Instala lo que falte (Python y pymongo), crea la base BDAutos, corre las 25 consultas y abre la app.
# Se ejecuta con doble clic en instalar_y_correr.bat
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$log = Join-Path $PSScriptRoot 'log_ejecucion.txt'
Set-Content -Path $log -Value "=== BDAutos - $(Get-Date) ===" -Encoding UTF8

function Log($m) { Write-Host $m; Add-Content -Path $log -Value $m -Encoding UTF8 }
function Correr([scriptblock]$cmd) { & $cmd 2>&1 | ForEach-Object { Log ("  " + "$_") } }
function Refrescar-Path {
    $env:Path = "$env:SystemRoot\System32;$env:SystemRoot;$env:SystemRoot\System32\WindowsPowerShell\v1.0;" +
                "$env:SystemRoot\System32\Wbem;$env:LOCALAPPDATA\Microsoft\WindowsApps;" +
                [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
    $extra = @()
    $extra += Get-ChildItem 'C:\Program Files\MongoDB\Server\*\bin' -Directory -ErrorAction SilentlyContinue |
              Sort-Object FullName -Descending | ForEach-Object FullName
    $extra += "$env:LOCALAPPDATA\Programs\mongosh", 'C:\Program Files\mongosh'
    $extra += Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*" -Directory -ErrorAction SilentlyContinue |
              Sort-Object FullName -Descending | ForEach-Object { $_.FullName; "$($_.FullName)\Scripts" }
    # se ponen al inicio para ganarle al "python" falso de la Microsoft Store
    foreach ($d in $extra) { if ($d -and (Test-Path $d)) { $env:Path = "$d;" + $env:Path } }
}
function Tiene($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function PythonOk {
    if (-not (Tiene python)) { return $false }
    & python -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" 2>$null
    return ($LASTEXITCODE -eq 0)
}
function Instalar($id, $nombre, $extra = '') {
    if (-not (Tiene winget)) { Log "ERROR: no hay winget para instalar $nombre. Instálalo a mano."; return }
    Log ">> Instalando $nombre con winget (puede pedir permiso de administrador: dale Sí)..."
    if ($extra) {
        Correr { winget install -e --id $id --silent --accept-source-agreements --accept-package-agreements --disable-interactivity --override $extra }
    } else {
        Correr { winget install -e --id $id --silent --accept-source-agreements --accept-package-agreements --disable-interactivity }
    }
    Refrescar-Path
}

Refrescar-Path
Log "`n[1/5] Revisando programas"
if (PythonOk) { Log "  Python: OK ($(python --version 2>&1))" } else { Instalar 'Python.Python.3.12' 'Python 3.12' '/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_tcltk=1' }
if (Tiene mongod) { Log "  MongoDB Server: OK" } else { Instalar 'MongoDB.Server' 'MongoDB Server' }
Log "  python: $(Tiene python) | mongod: $(Tiene mongod)"

Log "`n[2/5] Instalando pymongo"
Correr { python -m pip install --upgrade --quiet pymongo }
Correr { python -c "import pymongo; print('pymongo', pymongo.version)" }

Log "`n[3/5] Encendiendo MongoDB"
function MongoArriba { & python -c "from conexion import get_db, URI, BD; get_db(URI, BD)" 2>$null | Out-Null; return ($LASTEXITCODE -eq 0) }
if (-not (MongoArriba)) {
    $svc = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
    if ($svc) { Log "  Iniciando el servicio MongoDB..."; Start-Service MongoDB -ErrorAction SilentlyContinue; Start-Sleep 4 }
}
if (-not (MongoArriba) -and (Tiene mongod)) {
    $data = Join-Path $PSScriptRoot 'datos_mongo'
    New-Item -ItemType Directory -Force -Path $data | Out-Null
    Log "  Iniciando mongod con la carpeta datos_mongo..."
    Start-Process mongod -ArgumentList "--dbpath `"$data`" --bind_ip 127.0.0.1" -WindowStyle Minimized
    Start-Sleep 6
}
if (MongoArriba) { Log "  MongoDB corriendo" }
else { Log "ERROR: MongoDB no arrancó. Revisa que se haya instalado."; Log "FIN CON ERRORES"; exit 1 }

$env:PYTHONIOENCODING = 'utf-8'
Log "`n[4/5] Creando la base BDAutos"
Correr { python crear_bd.py }
$env:PYTHONIOENCODING = 'utf-8'
Correr { python conexion.py }

Log "`n[5/5] Corriendo las 25 consultas"
python consultas.py 2>&1 | Out-File -FilePath (Join-Path $PSScriptRoot 'resultados_consultas.txt') -Encoding utf8
$n = (Select-String -Path 'resultados_consultas.txt' -Pattern '^--- \d+ documento').Count
Log "  Consultas con resultado (Python): $n de 25  -> resultados_consultas.txt"
Log "`nAbriendo la app de consultas..."
Start-Process -FilePath (Join-Path $PSScriptRoot 'abrir_app.bat') -WindowStyle Hidden
Log "`nLISTO"
