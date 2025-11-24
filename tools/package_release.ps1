# tools/package_release.ps1
param(
    [string]$OS = "windows"
)

$version = "0.0.1-test"  # Ou récupérer depuis les inputs du workflow si nécessaire
$packageName = "galad-islands-$OS"

# Créer le dossier de package
New-Item -ItemType Directory -Path $packageName -Force

# Copier les dossiers complets d'abord
Copy-Item "dist/galad-islands" "$packageName/galad-islands" -Recurse -Force
Copy-Item "dist/galad-config-tool" "$packageName/galad-config-tool" -Recurse -Force
# MaraudeurAiCleaner packaging removed (merged into galad-config-tool)

# Dédupliquer assets et models
if (Test-Path "$packageName/galad-islands/assets") {
    Move-Item "$packageName/galad-islands/assets" "$packageName/assets" -Force
}
Remove-Item "$packageName/galad-config-tool/assets" -Recurse -Force -ErrorAction SilentlyContinue
# No separate MaraudeurAiCleaner assets to remove

if (Test-Path "$packageName/galad-islands/models") {
    Move-Item "$packageName/galad-islands/models" "$packageName/models" -Force
}
Remove-Item "$packageName/galad-config-tool/models" -Recurse -Force -ErrorAction SilentlyContinue
# No separate MaraudeurAiCleaner models to remove

# Unifier les _internal : créer un dossier commun et copier toutes les bibliothèques
New-Item -ItemType Directory -Path "$packageName/_internal" -Force

# Copier depuis chaque _internal individuel (sans duplication grâce à Copy-Item -Force)
Get-ChildItem "dist/galad-islands/_internal/*" | Copy-Item -Destination "$packageName/_internal/" -Recurse -Force
Get-ChildItem "dist/galad-config-tool/_internal/*" | Copy-Item -Destination "$packageName/_internal/" -Recurse -Force
# No MaraudeurAiCleaner _internal to merge

# Déplacer les exécutables à la racine
Move-Item "$packageName/galad-islands/galad-islands.exe" "$packageName/galad-islands.exe" -Force
Move-Item "$packageName/galad-config-tool/galad-config-tool.exe" "$packageName/galad-config-tool.exe" -Force
# No separate MaraudeurAiCleaner executable to move

# Supprimer les _internal individuels et les dossiers vides
Remove-Item "$packageName/galad-islands/_internal" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$packageName/galad-config-tool/_internal" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$packageName/galad-islands" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$packageName/galad-config-tool" -Recurse -Force -ErrorAction SilentlyContinue
# No MaraudeurAiCleaner folder to remove

# Copier le README
Copy-Item "RELEASE_README.md" "$packageName/README.md" -Force

# Créer le ZIP
Compress-Archive -Path $packageName -DestinationPath "$packageName.zip"

Write-Host "Package créé : $packageName.zip"