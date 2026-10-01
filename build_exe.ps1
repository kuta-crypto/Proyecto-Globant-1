$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $projectPython)) {
        throw 'Primero crea .venv con: python -m venv .venv'
    }
    & $projectPython -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    & $projectPython -m PyInstaller --noconfirm --clean --onefile --windowed --name TimbaRNG --add-data 'assets:assets' --exclude-module pytest main.py
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el ejecutable.' }
    Write-Host "Ejecutable listo: $PSScriptRoot\dist\TimbaRNG.exe"
}
finally {
    Pop-Location
}
