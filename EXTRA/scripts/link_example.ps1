# sudo pwsh.exe

$installDir = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data'
$basePath = 'C:\Users\montr\progetti\RimWorld-it\EXTRA\Examples'
$langs = @('English', 'German (Deutsch)', 'Spanish (Español(Castellano))')
$dlcList = @('Core', 'Anomaly', 'Biotech', 'Ideology', 'Royalty', 'Odyssey')

# Creazione dei link per le lingue
foreach ($dlc in $dlcList) {
    foreach ($lang in $langs) {

        $sourcePath = "$installDir\$dlc\Languages\$lang"
        $targetPath = "$basePath\$dlc\$lang"

        Write-Host "* Folder: $targetPath"

        # Verifica se la directory sorgente esiste
        if (Test-Path $sourcePath) {
            # Rimuovi il link esistente se presente
            if (Test-Path $targetPath) {
                Remove-Item $targetPath -Force -Recurse
            }

            # Crea la directory padre se non esiste
            $parentDir = Split-Path $targetPath
            if (!(Test-Path $parentDir)) {
                New-Item -ItemType Directory -Force -Path $parentDir
            }

            # Crea il link simbolico
            cmd /c mklink /d "$targetPath" "$sourcePath"
            Write-Host "Creato link: $targetPath -> $sourcePath"
        }

        # Verifica se esiste un file tar nella cartella Examples
        $tarFile = "$sourcePath.tar"
        if (Test-Path "$tarFile") {
            Write-Host "Trovato file tar: $tarFile"
            
            # Rimuovi la directory esistente se presente
            if (Test-Path $targetPath) {
                Remove-Item $targetPath -Force -Recurse
            }

            # Crea la directory padre se non esiste
            $parentDir = Split-Path $targetPath
            Write-Host "Creo cartella: $targetPath"
            if (!(Test-Path $targetPath)) {
                New-Item -ItemType Directory -Force -Path $targetPath
            }

            # Estrai il file tar nella cartella Examples
            Write-Host "Estraendo $tarFile in $targetPath"
            tar -xf $tarFile -C $targetPath

        }
        else
        {
            Write-Host "Nessun file tar trovato in $tarFile"
        }
    }
}

