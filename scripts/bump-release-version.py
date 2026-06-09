#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


# The macOS .xcodeproj is generated from project.yml by xcodegen at build time,
# so only project.yml carries the version (no committed pbxproj to patch).
VERSION_FILES = [
    ("core/al_munadi_core.py", r'APP_VERSION = "\d+\.\d+\.\d+"', 'APP_VERSION = "{version}"'),
    ("AlMunadiMac/AlMunadi/PrayerService.swift", r'static let appVersion = "\d+\.\d+\.\d+"', 'static let appVersion = "{version}"'),
    ("extension.js", r"const _VERSION = '\d+\.\d+\.\d+';", "const _VERSION = '{version}';"),
    ("AlMunadiMac/project.yml", r'MARKETING_VERSION: "\d+\.\d+\.\d+"', 'MARKETING_VERSION: "{version}"'),
    ("AlMunadiMac/project.yml", r'CURRENT_PROJECT_VERSION: "\d+"', 'CURRENT_PROJECT_VERSION: "{build}"'),
]


def read_current_version():
    source = (ROOT / "core/al_munadi_core.py").read_text()
    match = re.search(r'APP_VERSION = "(\d+)\.(\d+)\.(\d+)"', source)
    if not match:
        raise SystemExit("Could not find APP_VERSION")
    return tuple(int(part) for part in match.groups())


def bump_patch(version):
    major, minor, patch = version
    return major, minor, patch + 1


def replace_once(path, pattern, replacement):
    text = path.read_text()
    updated, count = re.subn(pattern, replacement, text)
    if count == 0:
        raise SystemExit(f"No match for {pattern!r} in {path}")
    path.write_text(updated)


def main():
    parser = argparse.ArgumentParser(description="Bump release version across platform manifests.")
    parser.add_argument("--dry-run", action="store_true", help="Print the next version without editing files.")
    args = parser.parse_args()

    next_version_tuple = bump_patch(read_current_version())
    version = ".".join(str(part) for part in next_version_tuple)

    metadata_path = ROOT / "metadata.json"
    metadata_text = metadata_path.read_text()
    metadata_match = re.search(r'"version":\s*(\d+)', metadata_text)
    if not metadata_match:
        raise SystemExit("Could not find metadata.json version")
    build = int(metadata_match.group(1)) + 1

    if args.dry_run:
        print(version)
        return

    for relative_path, pattern, template in VERSION_FILES:
        replace_once(ROOT / relative_path, pattern, template.format(version=version, build=build))

    replace_once(metadata_path, r'"app-version":\s*"\d+\.\d+\.\d+"', f'"app-version": "{version}"')
    replace_once(metadata_path, r'"version":\s*\d+', f'"version": {build}')
    print(version)


if __name__ == "__main__":
    main()
