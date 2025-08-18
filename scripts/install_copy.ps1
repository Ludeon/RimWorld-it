# sudo pwsh.exe

$basePath = (Get-Location).Path

Write-Host "basePath        : $basePath"
Write-Host "PSCommandPath   : $PSCommandPath"
Write-Host "=========================="

# Verifica se lo script è in esecuzione come amministratore
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Riavvio lo script come amministratore..."
    $cmd = "Set-Location -LiteralPath '$basePath'; & '$PSCommandPath'"
    Start-Process -FilePath powershell -Verb RunAs `
    -ArgumentList @(
        '-ExecutionPolicy','Bypass',
        '-Command', $cmd
    )`
    -WorkingDirectory $basePath
    exit
}

$installDir = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data'

# copia i file originali dall'inglese inglese
# Core

$dlcList = @('Core', 'Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

foreach ($dlc in $dlcList) {
    Write-Host "Processing DLC: $dlc"
    $italianDir = "$installDir\$dlc\Languages\Italiano"
    if (Test-Path $italianDir) {
        Remove-Item -Recurse -Force $italianDir
    }
    # Installa la patch italiana per ogni DLC
    robocopy "$basePath\$dlc" $italianDir `
        /NFL /NDL /MIR /NJH /NJS /NC /NS /NP
}

echo "RimWorld Italian translation installed successfully."
echo ""
Read-Host "Premi qualsiasi tasto per chiudere..."