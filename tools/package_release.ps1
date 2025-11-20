param([string]$platform = 'windows')

$OutDir = "galad-islands-$platform"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# Copy one-dir outputs
Copy-Item -Path dist\galad-islands -Destination "$OutDir\galad-islands" -Recurse -Force
Copy-Item -Path dist\galad-config-tool -Destination "$OutDir\galad-config-tool" -Recurse -Force
Copy-Item -Path dist\MaraudeurAiCleaner -Destination "$OutDir\MaraudeurAiCleaner" -Recurse -Force

# Dedup assets: move main assets to root
if (Test-Path "$OutDir\galad-islands\assets") {
    Move-Item -Path "$OutDir\galad-islands\assets" -Destination "$OutDir\assets"
}
# Remove other assets
Remove-Item -Path "$OutDir\galad-config-tool\assets" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$OutDir\MaraudeurAiCleaner\assets" -Recurse -Force -ErrorAction SilentlyContinue

# Move models
if (Test-Path "$OutDir\galad-islands\models") {
    Move-Item -Path "$OutDir\galad-islands\models" -Destination "$OutDir\models"
}

# Add README
Copy-Item -Path RELEASE_README.md -Destination "$OutDir\README.md"

# Zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($OutDir, "$OutDir.zip")
Write-Output "Packaged $OutDir.zip"