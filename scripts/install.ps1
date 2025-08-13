# sudo pwsh.exe

$installDir = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data'
$basePath = (Get-Location).Path

Write-Host "basePath   : $basePath"
Write-Host "installDir : $installDir"

rm "$installDir\Core\Languages\Italiano"

$dlcList = @('Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

foreach ($dlc in $dlcList)
{
    rm "$installDir\$dlc\Languages\Italiano"
}

echo $basePath\Core

cmd /c mklink /d "$installDir\Core\Languages\Italiano" $basePath\Core

foreach ($dlc in $dlcList)
{
    cmd /c mklink /d "$installDir\$dlc\Languages\Italiano" $basePath\$dlc
}
