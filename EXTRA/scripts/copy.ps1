# sudo pwsh.exe

#rm -Recurse -Force  'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Core\Languages\Italiano'
#rm -Recurse -Force  'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Royalty\Languages\Italiano'
#rm -Recurse -Force  'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Ideology\Languages\Italiano'
#rm -Recurse -Force  'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Biotech\Languages\Italiano'
#rm -Recurse -Force  'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data\Anomaly\Languages\Italiano'

$basePath = 'C:\Users\montr\progetti\RimWorld-it'
$installDir = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data'


# copia i file originali dall'inglese inglese
# Core
robocopy '$installDir\Core\Languages\English' "$basePath\English\Core" `
    /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP

# Anomaly
robocopy '$installDir\Anomaly' "$basePath\English\Anomaly" `
     /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP `
     /XD '$installDir\Anomaly\Languages'
robocopy '$installDir\Anomaly\Languages\English' "$basePath\English\Anomaly\English"  /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP

# Biotech
robocopy "$installDir\Biotech" "$basePath\English\Biotech" `
     /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP `
     /XD "$installDir\Biotech\Languages"
robocopy "$installDir\Biotech\Languages\English" "$basePath\English\Biotech\English" `
    /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP

# Royalty
robocopy "$installDir\Royalty" "$basePath\English\Royalty" `
     /XD "$installDir\Royalty\Languages" `
     /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP
robocopy "$installDir\Royalty\Languages\English" "$basePath\English\Royalty\English" `
     /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP

# Ideology
robocopy "$installDir\Ideology" "$basePath\English\Ideology" `
     /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP `
     /XD "$installDir\Ideology\Languages"
robocopy "$installDir\Ideology\Languages\English" "$basePath\English\Ideology\English" `
    /MIR /NFL /NDL /E /XO /XN /NJH /NJS /NC /NS /NP


# installa la patch
robocopy "$basePath\Core" "$installDir\Core\Languages\Italiano" `
    /NFL /NDL /MIR /NJH /NJS /NC /NS /NP
robocopy "$basePath\Royalty" "$installDir\Royalty\Languages\Italiano" `
    /NFL /NDL /MIR /NJH /NJS /NC /NS /NP
robocopy "$basePath\Ideology" "$installDir\Ideology\Languages\Italiano" `
    /NFL /NDL /MIR /NJH /NJS /NC /NS /NP
robocopy "$basePath\Biotech" "$installDir\Biotech\Languages\Italiano" `
    /NFL /NDL /MIR /NJH /NJS /NC /NS /NP
robocopy "$basePath\Anomaly" "$installDir\Anomaly\Languages\Italiano" `
    /NFL /NDL /MIR /NJH /NJS /NC /NS /NP

echo "RimWorld Italian translation installed successfully."