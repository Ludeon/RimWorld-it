# sudo pwsh.exe

$installDir = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data'
$basePath = (Get-Location).Path

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

Write-Host "basePath   : $basePath"
Write-Host "installDir : $installDir"

$dlcList = @('Core', 'Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

foreach ($dlc in $dlcList)
{
    Write-Host "Rimuovo cartella: $dlc"
    Remove-Item -Recurse -Force "$installDir\$dlc\Languages\Italiano"
}

foreach ($dlc in $dlcList)
{
    cmd /c mklink /d "$installDir\$dlc\Languages\Italiano" $basePath\$dlc
}

Write-Host ""
Read-Host "Premi qualsiasi tasto per chiudere... "