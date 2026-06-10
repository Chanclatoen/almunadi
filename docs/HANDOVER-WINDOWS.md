# Al Munadi — Windows Session Handover

Last updated: 2026-06-10. Start from `main` (v1.0.9 is tagged and includes the
Python app polish and the completed macOS Workstream A). Create a fresh feature
branch for this work — the previous branch `claude/loving-franklin-8ufs4d` is
fully merged.

Read `docs/BACKLOG.md` first for ground rules, the brand palette, and the
overall plan; `shared/product-behavior.md` is the product spec;
`shared/migration-plan.md` is the migration strategy. This file turns
Workstream C (plus the Windows half of Workstream E) into a concrete, ordered
plan for a session running **on a Windows machine**.

---

## Task 1 — Smoke-test the Python app v1.0.9 (do this first, ~30 min)

The shipping Windows client got a full redesign in v1.0.9 that was never run
on real Windows (it was built in a headless Linux sandbox). Verify it before
any rewrite work:

```powershell
git clone https://github.com/Chanclatoen/almunadi && cd almunadi
pip install -r AlMunadiWindows\requirements.txt
python -m pytest AlMunadiWindows\test_al_munadi.py -q   # expect 72 passed
python AlMunadiWindows\al_munadi.py
```

Checklist (fix anything broken and push the fix — these are bugs in a shipped
release):

- [ ] First run (delete `%APPDATA%\AlMunadi` first): tray label shows
      "Set mosque", popup shows the welcome state with **Find your mosque**.
- [ ] Mosque search: async (UI never freezes), "Searching…" row, results,
      no-results and error states; paste-URL with a bad URL shows the
      invalid-URL message.
- [ ] Popup: next-prayer card (name, time, countdown, iqama), full schedule,
      Shuruq in saffron, dimmed past prayers, footer actions.
- [ ] All 6 settings sections render and save: Mosque → Display →
      Notifications → Adhan → Prayer adjustments → App. Window fits on a
      1080p screen.
- [ ] Test notification button fires a toast; Test adhan / Stop adhan work
      (WAV file); Reset offsets works; offsets clamp at ±60.
- [ ] All 6 tray display modes (countdown/time/name/compact/icon/since).
- [ ] Switch all 5 languages; Arabic renders readably.
- [ ] Offline: disconnect network, restart app → cached times + cached badge +
      calm error, Retry button refetches.
- [ ] HiDPI scaling (125%/150%) doesn't clip the popup or settings.

Also confirm the v1.0.9 release exe (PyInstaller artifact from
`windows-release.yml`) starts and shows the new design, not just the
from-source run.

---

## Task 2 — Workstream C: native C#/.NET rewrite (the main job)

### Prerequisites

- .NET 8 SDK (`winget install Microsoft.DotNet.SDK.8`). Verify: `dotnet --version`.
- No Visual Studio required; `dotnet build/test/publish` is enough.

### What already exists to build on

- **The spec is the contract**: `shared/product-behavior.md` (§1 hierarchy,
  §3 display modes, §4 prayer semantics, §5 notifications, §6 adhan, §7
  first-run/error states, §8 updates, §9 fetching, §10 languages).
- **Executable test cases**: `shared/fixtures/behavior-fixtures.json` — already
  asserted by Python (72), JS (184), Rust (8), Swift (9). The C# port makes it
  five languages.
- **A finished port to copy from**: the macOS session just did this exact
  exercise in Swift — `AlMunadiMac/Shared/BehaviorCore.swift` (the fixture-shaped
  core), `AlMunadiMac/Shared/BrandPalette.swift`, and
  `AlMunadiMac/AlMunadiTests/BehaviorFixtureTests.swift` (the fixture test
  pattern). The Rust equivalents are `AlMunadiLinuxNative/src/lib.rs` and
  `tests/fixtures.rs`. Port from these, not from scratch.
- **Reference implementation with full feature surface**:
  `AlMunadiWindows/al_munadi.py` + `core/al_munadi_core.py` (fetching, cache,
  notifications, adhan, settings UI structure, translations dict to copy
  verbatim).
- **Existing C# in the repo**: `AlMunadiWindows/widget_provider/` (MSIX widget
  provider) — `CacheReader.cs`, `NextPrayer.cs`, `Translations.cs` already
  parse the cache JSON and compute next prayer in C#. Reuse/extract rather
  than duplicate, and **do not break it**: it reads
  `%LOCALAPPDATA%\Packages\...` / `%APPDATA%\AlMunadi\cache.json` written by
  the tray app.

### Build order

1. **Scaffold** `AlMunadiWindowsNative/`:
   - `AlMunadi.Core/` — class library, zero UI deps: time math, countdown/
     elapsed/tray-title formatting, iqama resolution, Jumuah key, offsets +
     clamping, version compare, slug extraction, settings normalization,
     translations (copy the 86-key × 5-language dict from
     `core/al_munadi_core.py` `TRANSLATIONS`).
   - `AlMunadi.Core.Tests/` — xUnit, loads `shared/fixtures/behavior-fixtures.json`
     via a relative path (see how `AlMunadiLinuxNative/tests/fixtures.rs` does
     `CARGO_MANIFEST_DIR/../shared/...`). **Gate: all fixture groups green
     before writing any UI.**
   - `AlMunadi.App/` — WPF app (net8.0-windows), tray icon via WinForms
     `NotifyIcon` interop or H.NotifyIcon.Wpf.
2. **Data layer**: read/write `%APPDATA%\AlMunadi\settings.json` and
   `cache.json` **unchanged** — formats in `shared/settings-schema.json` and
   `shared/cache-schema.json`. Migration must be a no-op: a user replacing the
   Python exe with the native exe keeps their mosque, settings, and cache.
3. **Fetching**: `HttpClient`, Mawaqit structured API first
   (URL-encode queries), fall back to scraping `confData` from the public HTML
   page; 15s timeout; async; write cache on success; daily refresh around
   midnight + manual refresh. Update check vs GitHub releases ≤ once/24h,
   silent on failure (spec §8/§9).
4. **Tray + popup**: 6 display modes per spec §3; popup with next-prayer card,
   schedule, Shuruq, Jumuah on Fridays, cached badge, calm error + Retry,
   first-run welcome state (§7). Use the brand palette from `docs/BACKLOG.md`
   §2 (WPF resource dictionary; respect light/dark via `UISettings`).
5. **Settings window**: six sections in spec order with everything the Python
   app has (search, paste URL + validation, saved mosques, display mode +
   countdown format + language, global + per-prayer notifications/reminders/
   DND/adhan overrides, adhan file picker + Test/Stop, offsets with Reset,
   App section: version, launch-at-login, Open releases page,
   Test notification).
6. **Notifications/adhan**: `Microsoft.Toolkit.Uwp.Notifications` toasts;
   `scenario=alarm` for DND bypass (replaces the Python PowerShell hack —
   note the AUMID requirement for unpackaged exes: register a Start-menu
   shortcut at first run or via the installer). Adhan via
   `System.Windows.Media.MediaPlayer` (any format, not just WAV); never
   overlap playback; validate file exists (`adhan_file_missing`).
7. **Launch at login**: `HKCU\...\Run` registry value (same key the Python
   app uses — check `al_munadi.py` for the exact name so the toggle migrates).
8. **Release**: `dotnet publish -c Release -r win-x64 --self-contained
   -p:PublishSingleFile=true`; new `.github/workflows/windows-native-release.yml`
   attaching `AlMunadi-Windows-Native-vX.Y.Z.exe` to the same release, built on
   the `v*` tag like the others. Ship **side-by-side** with the Python exe for
   ≥2 releases — do not remove `windows-release.yml` or the Python app.

### Parity checklist (all must pass before the Python exe is ever dropped)

6 tray modes · popup states (normal/first-run/cached/error) · 6 settings
sections · search + paste URL · saved mosques/switching · per-prayer
notifications, reminders (0–120), adhan + DND overrides · manual offsets ±60 ·
offline cache reuse · update check · launch at login · 5 languages incl. RTL
Arabic · HiDPI · light/dark · widget provider still updates.

### Non-negotiables (from `docs/BACKLOG.md` §2)

No analytics/tracking/accounts, no Electron. Calm saffron errors, never stack
traces. Every string through translations (all 5 languages + register in
`shared/translation-keys.json`). Behavior changes start in
`shared/fixtures/behavior-fixtures.json` and must keep Python/JS/Rust/Swift
suites green. Pushes to `main` auto-release unless `[skip release]` — develop
on a branch.

---

## Suggested session prompt

> Check out a new branch from main. Read docs/HANDOVER-WINDOWS.md and do
> Task 1 (smoke-test the Python app, fix what's broken), then Task 2 (the
> C#/.NET native rewrite) following its build order. Verify with
> `dotnet test` against the shared fixtures and a manual run at each step.
