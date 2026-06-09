#!/usr/bin/env bash
# Build a release AlMunadi.app and package it into dist/AlMunadi-macOS.zip
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="AlMunadi.xcodeproj"
SCHEME="AlMunadi"
CONFIG="Release"
BUILD_DIR="build"
DIST_DIR="dist"
APP_NAME="AlMunadi.app"

# Regenerate the project from project.yml if xcodegen is available.
if command -v xcodegen >/dev/null 2>&1; then
  echo "==> Regenerating Xcode project with xcodegen"
  xcodegen generate
fi

# Honor an externally-provided signing identity (set by CI when Developer ID
# secrets exist); default to ad-hoc ("-") for local/unsigned builds.
CODE_SIGN_IDENTITY="${CODE_SIGN_IDENTITY:--}"
DEVELOPMENT_TEAM="${DEVELOPMENT_TEAM:-}"

echo "==> Building $SCHEME ($CONFIG) with identity: $CODE_SIGN_IDENTITY"
if [[ "$CODE_SIGN_IDENTITY" == "-" ]]; then
  # Ad-hoc fallback: no Developer ID available.
  xcodebuild \
    -project "$PROJECT" \
    -scheme "$SCHEME" \
    -configuration "$CONFIG" \
    -derivedDataPath "$BUILD_DIR" \
    clean build \
    CODE_SIGN_IDENTITY="-" \
    CODE_SIGN_STYLE=Automatic
else
  # Developer ID direct distribution: manual signing, no provisioning profile,
  # hardened runtime + secure timestamp (both mandatory for notarization).
  xcodebuild \
    -project "$PROJECT" \
    -scheme "$SCHEME" \
    -configuration "$CONFIG" \
    -derivedDataPath "$BUILD_DIR" \
    clean build \
    CODE_SIGN_IDENTITY="$CODE_SIGN_IDENTITY" \
    CODE_SIGN_STYLE=Manual \
    DEVELOPMENT_TEAM="$DEVELOPMENT_TEAM" \
    ENABLE_HARDENED_RUNTIME=YES \
    OTHER_CODE_SIGN_FLAGS="--timestamp --options runtime"
fi

APP_PATH="$BUILD_DIR/Build/Products/$CONFIG/$APP_NAME"
if [[ ! -d "$APP_PATH" ]]; then
  echo "error: build did not produce $APP_PATH" >&2
  exit 1
fi

# When signing for distribution, re-sign inside-out to guarantee the embedded
# widget extension carries the same Developer ID + hardened runtime, then verify.
# (Signing the outer .app seals the inner .appex, so the extension must go first.)
if [[ "$CODE_SIGN_IDENTITY" != "-" ]]; then
  EXT_PATH="$APP_PATH/Contents/PlugIns/AlMunadiWidget.appex"
  if [[ -d "$EXT_PATH" ]]; then
    echo "==> Deep-signing embedded widget extension"
    codesign --force --timestamp --options runtime \
      --entitlements AlMunadiWidget/AlMunadiWidget.entitlements \
      --sign "$CODE_SIGN_IDENTITY" "$EXT_PATH"
  fi
  echo "==> Signing app bundle"
  codesign --force --timestamp --options runtime \
    --entitlements AlMunadi/AlMunadi.entitlements \
    --sign "$CODE_SIGN_IDENTITY" "$APP_PATH"
  echo "==> Verifying signature"
  codesign --verify --deep --strict --verbose=2 "$APP_PATH"
fi

echo "==> Packaging"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
VERSION=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APP_PATH/Contents/Info.plist" 2>/dev/null || echo "dev")
ZIP_PATH="$DIST_DIR/AlMunadi-macOS-v${VERSION}.zip"

# ditto preserves the bundle's resource forks / symlinks for a valid .app archive.
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

echo "==> Done: $ZIP_PATH"
ls -lh "$ZIP_PATH"
