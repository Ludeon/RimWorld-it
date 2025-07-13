# sudo pwsh.exe

$installDir = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data'
$basePath = 'C:\Users\montr\progetti\RimWorld-it'

rm "$installDir\Core\Languages\Italiano"

$dlcList = @('Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

foreach ($dlc in $dlcList) {
    rm "$installDir\$dlc\Languages\Italiano"
}

echo $basePath\Core

cmd /c mklink /d "$installDir\Core\Languages\Italiano" $basePath\Core

foreach ($dlc in $dlcList) {
    cmd /c mklink /d "$installDir\$dlc\Languages\Italiano" $basePath\$dlc
}
