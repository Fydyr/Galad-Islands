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

# Clean up redundant empty directories
rmdir "${OUT_DIR}/galad-islands" 2>/dev/null || true

# Add README
cp RELEASE_README.md "${OUT_DIR}/README.md"

# Zip the package
zip -r "${OUT_DIR}.zip" "${OUT_DIR}"

echo "Packaged ${OUT_DIR}.zip"