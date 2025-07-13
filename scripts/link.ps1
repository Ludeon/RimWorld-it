# sudo pwsh.exe

rm 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Core\Languages\Italiano'
rm 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Royalty\Languages\Italiano'
rm 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Ideology\Languages\Italiano'
rm 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Biotech\Languages\Italiano'
rm 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Anomaly\Languages\Italiano'

$basePath = 'C:\Users\montr\progetti\RimWorld-it'

echo $basePath\Core

cmd /c mklink /d 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Core\Languages\Italiano' $basePath\Core
cmd /c mklink /d 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Royalty\Languages\Italiano' $basePath\Royalty
cmd /c mklink /d 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Ideology\Languages\Italiano' $basePath\Ideology
cmd /c mklink /d 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Biotech\Languages\Italiano' $basePath\Biotech
cmd /c mklink /d 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Anomaly\Languages\Italiano' $basePath\Anomaly