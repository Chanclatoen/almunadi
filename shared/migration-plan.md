# Al Munadi — Native Migration Plan (Windows & Linux)

Status: **planning approved, not yet started.** The Python tray apps remain the
shipping clients until a native replacement reaches feature parity.

## Target architecture

| Platform | Today | Target | Verdict |
|----------|-------|--------|---------|
| macOS | Swift + SwiftUI (`MenuBarExtra`, widgets, App Group) | unchanged | Keep — already the right native stack |
| GNOME | GJS Shell extension | unchanged | Keep — the only correct extension model |
| Windows | Python + pystray + tkinter + winotify | **C#/.NET** tray app | Rewrite |
| Linux tray | Python + pystray + tkinter | **Rust + GTK4/libadwaita + StatusNotifier**, with Qt/C++ as the fallback choice | Rewrite after Windows |

No Electron. No single cross-platform framework. Consistency comes from
`shared/` (behavior spec, schemas, fixtures), not from shared compiled code.

## Why migrate Windows first

- Python on Windows is the weakest link: PyInstaller one-file builds are slow to
  start, trip antivirus heuristics, and the tkinter settings window will never
  feel native (theme, DPI, IME, accessibility).
- pystray's Win32 backend is a maintenance risk; .NET gives first-class
  `NotifyIcon`/`TaskbarIcon`, toast notifications with the alarm scenario (the
  current PowerShell DND-bypass hack becomes a normal API call), Startup-task
  integration, and a signed MSIX path that reuses the existing
  `widget_provider` signing flow (the repo already contains C# there).

### Windows C#/.NET plan

1. New `AlMunadiWindowsNative/` project: .NET 8, WPF for the settings window and
   tray popup (WinUI 3 adds packaging weight without benefit for a tray app),
   `H.NotifyIcon`-style tray or raw `NotifyIcon` via WinForms interop.
2. Port `core/al_munadi_core.py` behavior against `shared/fixtures/` — fetch +
   HTML fallback, cache, settings normalization, countdown/iqama/Jumuah rules.
   Unit-test with the same fixture file.
3. Read the existing `%APPDATA%/AlMunadi/settings.json` and `cache.json`
   unchanged (schemas in `shared/`), so migration is a no-op for users.
4. Notifications via `Microsoft.Toolkit.Uwp.Notifications` (toast with
   `scenario=alarm` for DND bypass); adhan via `MediaPlayer` (drops the
   WAV-only winsound limitation).
5. Release: add a `windows-native-release.yml` building a self-contained
   single-file exe; ship side-by-side with the Python exe for ≥2 releases.
6. Parity checklist (must all pass before the Python exe is dropped):
   tray label modes ×6, popup, settings sections ×6, search, paste URL,
   saved mosques, per-prayer notifications/reminders/adhan/DND, manual offsets,
   offline cache reuse, update check, launch at login, 5 languages, HiDPI,
   light/dark.

## Linux evaluation: Rust+GTK vs Qt/C++

**Recommendation: Rust + GTK4/libadwaita + StatusNotifier (ksni crate), pending
a tray-compatibility spike on KDE, XFCE, Cinnamon, and MATE.**

- For (Rust/GTK): memory-safe long-running daemon; libadwaita settings UI feels
  native on most modern Linux desktops; `ksni`/`zbus` implement
  StatusNotifierItem directly (the same protocol KDE/most trays speak); cargo
  produces a single binary close to the current PyInstaller artifact; the repo
  already has Rust toolchain affinity in CI runners.
- For (Qt/C++): `QSystemTrayIcon` has the broadest out-of-the-box tray support
  and looks native on KDE; heavier runtime to ship, C++ maintenance cost,
  duplicated look vs GNOME extension users.
- Decision gate: if the StatusNotifier spike fails on XFCE/MATE (older trays
  only speak XEmbed), switch to Qt, which still wraps XEmbed.
- GNOME users are explicitly served by the Shell extension, not the tray app.

### Linux plan

0. **Done:** `AlMunadiLinuxNative/` — a dependency-free Rust behavior core
   (countdown/tray/iqama/offsets/Jumuah/version/slug) whose `cargo test`
   asserts the same `shared/fixtures/behavior-fixtures.json` cases as the
   Python and GNOME suites. Proves the fixtures are language-portable.
1. Spike: minimal ksni tray + libadwaita window, test on KDE/XFCE/Cinnamon/MATE.
2. Port core behavior against `shared/fixtures/`; reuse
   `~/.config/AlMunadi/{settings,cache}.json` unchanged.
3. Notifications via `notify-rust` (urgency critical for DND bypass), audio via
   `rodio` with graceful no-audio fallback.
4. Package: single binary first (matches current release), then evaluate
   Flatpak (best reach) vs deb/rpm.
5. Same parity checklist as Windows; keep the Python app for ≥2 releases.

## Deprecation sequence

1. Ship native Windows side-by-side → gather issues → make it the default
   download → remove Python Windows app.
2. Repeat for Linux.
3. Python `core/` remains as the executable reference implementation of the
   behavior spec (its tests pin the fixtures) until both rewrites are stable,
   then it can shrink to a test oracle.

## Risks

- Tray protocol fragmentation on Linux (mitigated by the spike + Qt fallback).
- Toast identity/AUMID handling on unpackaged Windows exes (mitigated by
  registering a Start-menu shortcut or shipping MSIX).
- Behavior drift during the dual-client window (mitigated by shared fixtures —
  extend them before porting, not after).
- Signing: new artifacts must enter the existing release workflows without
  touching macOS notarization or GNOME zip packaging.
