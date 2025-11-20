#!/usr/bin/env bash
set -euo pipefail

# Packaging script to assemble a single release folder containing
# multiple onedir builds produced by PyInstaller.
# Usage: tools/package_release.sh <platform>

PLATFORM=${1:-linux}
OUT_DIR="galad-islands-${PLATFORM}"

mkdir -p "${OUT_DIR}"

# Copy each onedir
cp -r dist/galad-islands "${OUT_DIR}/galad-islands"
cp -r dist/galad-config-tool "${OUT_DIR}/galad-config-tool"
cp -r dist/MaraudeurAiCleaner "${OUT_DIR}/MaraudeurAiCleaner"

# Deduplicate assets: move assets from main into top-level and remove others
if [ -d "${OUT_DIR}/galad-islands/assets" ]; then
  mv "${OUT_DIR}/galad-islands/assets" "${OUT_DIR}/assets"
fi

# Remove assets from other folders to avoid duplication
rm -rf "${OUT_DIR}/galad-config-tool/assets" || true
rm -rf "${OUT_DIR}/MaraudeurAiCleaner/assets" || true

# Move models to root models folder (if present)
if [ -d "${OUT_DIR}/galad-islands/models" ]; then
  mv "${OUT_DIR}/galad-islands/models" "${OUT_DIR}/models"
fi

# Remove models from other folders to avoid duplication
rm -rf "${OUT_DIR}/galad-config-tool/models" || true
rm -rf "${OUT_DIR}/MaraudeurAiCleaner/models" || true

# Unify _internal folders: create a common _internal and deduplicate libraries
mkdir -p "${OUT_DIR}/_internal"

# Copy all libraries from each _internal to the common one (cp -n to avoid overwriting)
if [ -d "${OUT_DIR}/galad-islands/_internal" ]; then
  cp -rn "${OUT_DIR}/galad-islands/_internal"/* "${OUT_DIR}/_internal/" 2>/dev/null || true
fi
if [ -d "${OUT_DIR}/galad-config-tool/_internal" ]; then
  cp -rn "${OUT_DIR}/galad-config-tool/_internal"/* "${OUT_DIR}/_internal/" 2>/dev/null || true
fi
if [ -d "${OUT_DIR}/MaraudeurAiCleaner/_internal" ]; then
  cp -rn "${OUT_DIR}/MaraudeurAiCleaner/_internal"/* "${OUT_DIR}/_internal/" 2>/dev/null || true
fi

# Move executables to root level (temporarily with different names to avoid conflicts)
mv "${OUT_DIR}/galad-islands/galad-islands" "${OUT_DIR}/galad-islands.exe"
mv "${OUT_DIR}/galad-config-tool/galad-config-tool" "${OUT_DIR}/galad-config-tool.exe"
mv "${OUT_DIR}/MaraudeurAiCleaner/MaraudeurAiCleaner" "${OUT_DIR}/MaraudeurAiCleaner.exe"

# Remove the individual _internal folders and empty directories
rm -rf "${OUT_DIR}/galad-islands/_internal"
rm -rf "${OUT_DIR}/galad-config-tool/_internal"
rm -rf "${OUT_DIR}/MaraudeurAiCleaner/_internal"
rmdir "${OUT_DIR}/galad-islands" 2>/dev/null || true
rmdir "${OUT_DIR}/galad-config-tool" 2>/dev/null || true
rmdir "${OUT_DIR}/MaraudeurAiCleaner" 2>/dev/null || true

# Rename executables back to their final names
mv "${OUT_DIR}/galad-islands.exe" "${OUT_DIR}/galad-islands"
mv "${OUT_DIR}/galad-config-tool.exe" "${OUT_DIR}/galad-config-tool"
mv "${OUT_DIR}/MaraudeurAiCleaner.exe" "${OUT_DIR}/MaraudeurAiCleaner"

# Add README
cp RELEASE_README.md "${OUT_DIR}/README.md"

# Zip the package
zip -r "${OUT_DIR}.zip" "${OUT_DIR}"

echo "Packaged ${OUT_DIR}.zip"