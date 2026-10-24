#!/usr/bin/env bash
# Construit openCRNA.app (Apple Silicon) et le zip. À lancer depuis la racine du projet.
# Sur macOS : signature ad hoc avec codesign. Sur Linux : nécessite rcodesign dans le PATH.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 build/build.py
VERSION=$(node -p "require('./mac/app/package.json').version")
npx --yes @electron/packager@18.3.6 mac/app openCRNA --platform=darwin --arch=arm64 \
  --electron-version=33.4.11 --icon=mac/icon.icns --app-bundle-id=fr.opencrna.simulator \
  --app-category-type=public.app-category.simulation-games --app-version="$VERSION" --out=mac/dist --overwrite
APP=mac/dist/openCRNA-darwin-arm64/openCRNA.app
( cd "$APP/Contents/Resources" && ls -d *.lproj | grep -v -E '^(fr|en|en_GB)\.lproj$' | xargs rm -rf )
if [[ "$(uname)" == "Darwin" ]]; then codesign --force --deep -s - "$APP"; else rcodesign sign "$APP"; fi
( cd mac/dist/openCRNA-darwin-arm64 && rm -f ../openCRNA-macOS-AppleSilicon.zip && zip -qry -9 ../openCRNA-macOS-AppleSilicon.zip openCRNA.app )
echo "OK : mac/dist/openCRNA-macOS-AppleSilicon.zip"
# Sur ton Mac, pour lancer directement : open "$APP"
