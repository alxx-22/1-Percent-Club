#!/usr/bin/env bash
# Pack the unpacked Percy solution source (./src) into an importable .zip.
# Prereq: Power Platform CLI — dotnet tool install --global Microsoft.PowerPlatform.CLI
#
# SCAFFOLD: src/ uses placeholder GUIDs. If pack/import errors, align Customizations.xml against a
# real exported solution. The guaranteed zip comes from build-in-portal + Export (see IMPORT-SOLUTION.md).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/src"
OUT="$HERE/out"
ZIP="$OUT/Percy1PctClub.zip"
TYPE="${1:-Unmanaged}"   # Unmanaged (default) or Managed

if ! command -v pac >/dev/null 2>&1; then
  echo "ERROR: 'pac' (Power Platform CLI) not found. Install: dotnet tool install --global Microsoft.PowerPlatform.CLI" >&2
  exit 1
fi

mkdir -p "$OUT"
echo "Packing $SRC -> $ZIP ($TYPE) ..."
pac solution pack --zipfile "$ZIP" --folder "$SRC" --packagetype "$TYPE"
echo "Done. Import via: Power Apps/Power Automate -> Solutions -> Import solution -> $ZIP"
