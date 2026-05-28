#!/usr/bin/env bash
# Build a release NextPrayer.app and package it into dist/NextPrayer-macOS.zip
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="NextPrayer.xcodeproj"
SCHEME="NextPrayer"
CONFIG="Release"
BUILD_DIR="build"
DIST_DIR="dist"
APP_NAME="NextPrayer.app"

# Regenerate the project from project.yml if xcodegen is available.
if command -v xcodegen >/dev/null 2>&1; then
  echo "==> Regenerating Xcode project with xcodegen"
  xcodegen generate
fi

echo "==> Building $SCHEME ($CONFIG)"
xcodebuild \
  -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration "$CONFIG" \
  -derivedDataPath "$BUILD_DIR" \
  clean build \
  CODE_SIGN_IDENTITY="-" \
  CODE_SIGN_STYLE=Automatic

APP_PATH="$BUILD_DIR/Build/Products/$CONFIG/$APP_NAME"
if [[ ! -d "$APP_PATH" ]]; then
  echo "error: build did not produce $APP_PATH" >&2
  exit 1
fi

echo "==> Packaging"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
VERSION=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APP_PATH/Contents/Info.plist" 2>/dev/null || echo "dev")
ZIP_PATH="$DIST_DIR/NextPrayer-macOS-v${VERSION}.zip"

# ditto preserves the bundle's resource forks / symlinks for a valid .app archive.
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo "==> Done: $ZIP_PATH"
ls -lh "$ZIP_PATH"
