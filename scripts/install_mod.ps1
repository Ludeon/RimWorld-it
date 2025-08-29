# Script per creare e installare la mod RimWorld Italiano
# Crea una cartella dist con solo i file necessari per la traduzione

param(
    [string] $ModName = "RimWorld-ita-dev",
    [string] $SteamModsDir = "C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods",
    [string] $BasePath = (Get-Location).Path,
    [string] $DistDir = "dist"
)

# Array dei DLC da includere
$DlcList = @('Core', 'Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey')

Write-Host ">> Creazione cartella dist per mod: $ModName" -ForegroundColor Green

# Crea/pulisce la cartella dist
$distPath = Join-Path $BasePath $DistDir
if (Test-Path $distPath) {
    Remove-Item $distPath -Recurse -Force
    Write-Host "Cartella dist esistente rimossa"
}
New-Item -ItemType Directory -Path $distPath -Force | Out-Null
Write-Host "Creata cartella dist: $distPath"

# Copia About folder (metadati mod)
$aboutSrc = Join-Path $BasePath "About"
$aboutDest = Join-Path $distPath "About"
if (Test-Path $aboutSrc) {
    Copy-Item $aboutSrc $aboutDest -Recurse -Force
    Write-Host "Copiato: About/"
} else {
    Write-Warning "Cartella About/ non trovata in $aboutSrc"
}

# Per ogni DLC, copia solo i file di traduzione necessari
foreach ($dlc in $DlcList) {
    $dlcSrcPath = Join-Path $BasePath $dlc
    $dlcDestPath = Join-Path $distPath $dlc
    
    if (!(Test-Path $dlcSrcPath)) {
        Write-Host "Saltato $dlc (non trovato)" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "Processando DLC: $dlc" -ForegroundColor Cyan
    
    # Crea struttura DLC nella dist
    New-Item -ItemType Directory -Path $dlcDestPath -Force | Out-Null
    
    # Copia DefInjected (traduzioni definizioni)
    $defInjectedSrc = Join-Path $dlcSrcPath "DefInjected"
    $defInjectedDest = Join-Path $dlcDestPath "DefInjected"
    if (Test-Path $defInjectedSrc) {
        Copy-Item $defInjectedSrc $defInjectedDest -Recurse -Force
        $fileCount = (Get-ChildItem $defInjectedDest -Recurse -File).Count
        Write-Host "  ✓ DefInjected/ ($fileCount files)"
    }
    
    # Copia Keyed (traduzioni UI/messaggi)
    $keyedSrc = Join-Path $dlcSrcPath "Keyed"
    $keyedDest = Join-Path $dlcDestPath "Keyed"
    if (Test-Path $keyedSrc) {
        Copy-Item $keyedSrc $keyedDest -Recurse -Force
        $fileCount = (Get-ChildItem $keyedDest -Recurse -File).Count
        Write-Host "  ✓ Keyed/ ($fileCount files)"
    }
    
    # Copia Strings (liste di nomi)
    $stringsSrc = Join-Path $dlcSrcPath "Strings"
    $stringsDest = Join-Path $dlcDestPath "Strings"
    if (Test-Path $stringsSrc) {
        Copy-Item $stringsSrc $stringsDest -Recurse -Force
        $fileCount = (Get-ChildItem $stringsDest -Recurse -File).Count
        Write-Host "  ✓ Strings/ ($fileCount files)"
    }
    
    # Copia WordInfo (regole grammaticali)
    $wordInfoSrc = Join-Path $dlcSrcPath "WordInfo"
    $wordInfoDest = Join-Path $dlcDestPath "WordInfo"
    if (Test-Path $wordInfoSrc) {
        Copy-Item $wordInfoSrc $wordInfoDest -Recurse -Force
        $fileCount = (Get-ChildItem $wordInfoDest -Recurse -File).Count
        Write-Host "  ✓ WordInfo/ ($fileCount files)"
    }
    
    # Per Core, copia anche LanguageInfo.xml e LangIcon.png
    if ($dlc -eq "Core") {
        $langInfoSrc = Join-Path $dlcSrcPath "LanguageInfo.xml"
        $langInfoDest = Join-Path $dlcDestPath "LanguageInfo.xml"
        if (Test-Path $langInfoSrc) {
            Copy-Item $langInfoSrc $langInfoDest -Force
            Write-Host "  ✓ LanguageInfo.xml"
        }
        
        $langIconSrc = Join-Path $dlcSrcPath "LangIcon.png"
        $langIconDest = Join-Path $dlcDestPath "LangIcon.png"
        if (Test-Path $langIconSrc) {
            Copy-Item $langIconSrc $langIconDest -Force
            Write-Host "  ✓ LangIcon.png"
        }
    }
}

# Calcola statistiche della dist
$totalFiles = (Get-ChildItem $distPath -Recurse -File).Count
$distSize = (Get-ChildItem $distPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
$distSizeMB = [math]::Round($distSize / 1MB, 2)

Write-Host "`n>> Cartella dist creata con successo!" -ForegroundColor Green
Write-Host "   Files totali: $totalFiles"
Write-Host "   Dimensione: $distSizeMB MB"
Write-Host "   Percorso: $distPath"

# Copia nella cartella Steam Mods
$steamModPath = Join-Path $SteamModsDir $ModName
Write-Host "`n>> Installazione mod in Steam" -ForegroundColor Green
Write-Host "   Destinazione: $steamModPath"

# Rimuovi mod esistente
if (Test-Path $steamModPath) {
    Remove-Item $steamModPath -Recurse -Force
    Write-Host "   Mod esistente rimossa"
}

# Copia dist -> Steam Mods
Copy-Item $distPath $steamModPath -Recurse -Force
Write-Host "   ✓ Mod installata con successo!"

Write-Host "`n>> Pronta per Steam Workshop!" -ForegroundColor Yellow
Write-Host "   1. Avvia RimWorld"
Write-Host "   2. Vai su Mods → Workshop → Upload"
Write-Host "   3. Seleziona: $ModName"
Write-Host ""