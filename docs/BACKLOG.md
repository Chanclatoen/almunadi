# Al Munadi — Full Backlog & Handoff

Last updated: 2026-06-10. Branch: `claude/loving-franklin-8ufs4d` (ahead of `main`).
This document is self-contained: hand it (or a single workstream section) to any
session/developer and they have everything needed to execute and verify.

---

## 1. Current state (what is already done)

- **Website** (`site/`, on `main`, deployed to Cloudflare Pages → almunadi.net):
  full premium landing page, SEO head, version-stamped assets (`?v=2`),
  deploy workflow `.github/workflows/site-deploy.yml`. Live and styled.
- **Shared behavior layer** (`shared/`, on the branch):
  - `product-behavior.md` — the product spec all clients must implement (§1–§11).
  - `settings-schema.json`, `cache-schema.json` — on-disk formats (Python and
    future native apps share the same files).
  - `translation-keys.json` — canonical key registry (86 keys × 5 languages).
  - `fixtures/behavior-fixtures.json` — executable behavior cases asserted by
    **three** suites: Python (72 tests), GNOME JS (184), Rust (8). Any port must
    assert these fixtures before shipping.
  - `migration-plan.md` — native rewrite plan (Windows C#/.NET, Linux Rust/GTK).
- **Python apps** (`AlMunadiWindows/`, `AlMunadiLinux/`, on the branch): full
  brand-identity repaint, first-run flow, async search, next-prayer card popup,
  six-section settings (Mosque → Display → Notifications → Adhan → Prayer
  adjustments → App), Test notification / Test adhan / Stop adhan / Reset
  offsets, URL validation, Retry in error banner, 86-key translations in all
  5 languages.
- **Rust spike** (`AlMunadiLinuxNative/`): dependency-free behavior core,
  `cargo test` green against the shared fixtures.
- **GNOME**: accent recolor (blue → emerald, error → saffron) in
  `stylesheet.css` only; logic untouched.
- **macOS**: untouched this round (no Xcode in the sandbox) — see Workstream A.

## 2. Ground rules (apply to every workstream)

- **Never break:** Mawaqit fetching (API + HTML `confData` fallback), offline
  cache reuse, update check, the 5 languages, notifications, adhan playback,
  manual offsets (±60 clamp), multi-mosque, GNOME Shell compatibility, macOS
  signing/notarization, App Group `PM49C5H4XK.net.almunadi.AlMunadi`.
- **No analytics, tracking, or accounts. No Electron.**
- Release flow: pushing to `main` auto-tags a release (`auto-release.yml`)
  unless the commit message contains `[skip release]` or only touches ignored
  paths (`site/**`, `worker/**`, `scripts/**`, `.github/**`, READMEs).
  A `vX.Y.Z` tag builds all four platform artifacts. **`tests/` and the app
  dirs are NOT ignored** — merging this branch to main cuts v1.0.9.
- Every user-facing string goes through the translation layer; add keys to all
  5 languages (en, nl, ar, fr, tr) **and** to `shared/translation-keys.json`.
- Errors are calm saffron text, never red walls or stack traces in UI.
- Behavior changes require updating `shared/fixtures/behavior-fixtures.json`
  first, then making all suites pass (Python, JS, Rust — and Swift once it
  asserts them too).

### Brand palette (dark surfaces)

| Token | Hex | | Token | Hex |
|---|---|---|---|---|
| BG | `#14130F` | | ACCENT (emerald) | `#46C79E` |
| CARD | `#1F1D17` | | ACCENT_HOVER | `#5ED2AC` |
| CARD_HOVER | `#27241C` | | ON_ACCENT | `#0C1A14` |
| TEXT_PRIMARY | `#F1EDE2` | | HIGHLIGHT_BG | `#1B2E26` |
| TEXT_SECONDARY | `#AAB0A3` | | SAFFRON (Shuruq/warn) | `#E3B15A` |
| TEXT_DIM | `#6E7466` | | ERROR_TEXT | `#E0B36A` |
| DIVIDER | `#2D2B23` | | Light-context accent | `#0F5D47` |

Prayer hues: Fajr `#D9A05B` · Dhuhr/Jumuah `#E3B15A` · Asr `#BC8A52` ·
Maghrib `#C96B4A` · Isha `#7D93C4`.

---

## 3. Workstream A — macOS app polish (needs a Mac with Xcode 15+)

Repo dir: `AlMunadiMac/`. The Xcode project is generated: `brew install
xcodegen && xcodegen generate`, then build the **AlMunadi** scheme, or
`./scripts/build-release.sh` for a distributable zip. App targets macOS 14+.

Files: `AlMunadi/AlMunadiApp.swift` (MenuBarExtra), `AlMunadi/PrayerTimesView.swift`
(dropdown), `AlMunadi/SettingsView.swift`, `AlMunadi/PrayerService.swift`,
`Shared/Translations.swift`, `Shared/Models.swift`, `Shared/PrayerListBuilder.swift`,
`Shared/NextPrayerComputation.swift`, `Shared/WidgetSharedStore.swift`,
`AlMunadiWidget/` (small/medium/large views).

Tasks (spec: `shared/product-behavior.md`, esp. §1–§3, §7, §11):

1. **Brand identity**: adopt the palette above. Replace the blue next-prayer
   highlight with emerald (`#46C79E` highlight + left accent bar); Shuruq and
   Jumuah rows get saffron accents; past prayers dimmed; tabular digits for
   times/countdowns.
2. **First-run empty state** in the dropdown (spec §7): when no mosque is
   configured show app name, one-line "Al Munadi shows your mosque's prayer
   times from its public Mawaqit page", a primary **Find your mosque** button
   opening Settings, instead of an empty/erroring list. Menu-bar label shows
   localized `set_mosque`.
3. **Next-prayer card** at the top of the dropdown: "NEXT PRAYER" label,
   prayer name + time large, live countdown, iqama line when present,
   emerald accent edge.
4. **Settings restructure** into the six §1 sections in order:
   Mosque → Display → Notifications → Adhan → Prayer adjustments → App.
   Include: Test adhan / Stop adhan buttons, Reset offsets, Test notification,
   App section with version + "Open releases page". Validate pasted URLs
   (reject when no slug extracts; show localized `invalid_mawaqit_url`).
5. **Cached-data badge** in the dropdown header when showing cached times
   (localized `cached_data`), with a calm `fetch_error` line — never raw errors.
6. **Widget empty/offline states**: no-mosque → "Set your mosque in Al Munadi";
   stale cache → show times with cached hint. Never a blank widget.
7. **Translations**: add the new keys to `Shared/Translations.swift` for all 5
   languages — `set_mosque`, `first_run_title`, `first_run_body`, `searching`,
   `test_adhan`, `stop_adhan`, `reset_offsets`, `reminder_body`,
   `adhan_file_missing`, `offsets_hint`, `retry`, `test_notification`,
   `app_version`, `open_releases`, `dnd_platform_note`, `invalid_mawaqit_url`,
   `display`, `app`. Copy the exact strings from `TRANSLATIONS` in
   `core/al_munadi_core.py` so wording matches across platforms. Then remove
   the corresponding entry from the `todo` list in `shared/translation-keys.json`.
8. **Fixture tests (recommended)**: add a small XCTest target that loads
   `shared/fixtures/behavior-fixtures.json` and asserts countdown/elapsed
   formats, tray-title modes, iqama resolution, offset clamping, the Jumuah
   notification key, version comparison, and slug extraction — same as the
   Python/JS/Rust suites.
9. **DND honesty**: time-sensitive notifications stay disabled until a
   provisioning profile exists (see `AlMunadiMac/README.md` §"Time-sensitive
   notifications"); the UI must not claim Focus bypass works on macOS
   (use the `dnd_platform_note` string).

Constraints: don't rename the App Group or bundle IDs; keep `project.yml` the
source of truth; keep `scripts/build-release.sh` and
`.github/workflows/macos-release.yml` working (hardened runtime, notarization).

Verify: `xcodegen generate && xcodebuild -project AlMunadi.xcodeproj -scheme
AlMunadi -configuration Release build`, run the app, check all 5 languages,
first-run flow with `defaults delete net.almunadi.AlMunadi`, widget in all
three sizes, and the release script end-to-end.

---

## 4. Workstream B — GNOME extension polish (needs GNOME Shell to verify)

Files: `extension.js`, `prefs.js`, `translations/*.json`, `stylesheet.css`.

1. First-run menu item: when no mosque is configured, show a "Find your
   mosque" item (opens prefs) and the `set_mosque` panel label instead of an
   empty menu.
2. Adopt the new translation keys (same list as Workstream A item 7) in
   `translations/*.json`; update `shared/translation-keys.json` todo.
3. Optional: next-prayer header card at the top of the popup menu (St.BoxLayout
   with the `.next-prayer-menu-active` emerald styling already in
   `stylesheet.css`).
4. Keep the exemplary `disable()` cleanup intact (all timers/signals/GStreamer
   sources cleared) — reviewers check this for extensions.gnome.org.

Verify: `node --test tests/` still passes (184 assertions), then manual install
on a GNOME Shell session (`make install` / nested shell).

---

## 5. Workstream C — Windows native rewrite (C#/.NET; needs .NET 8 SDK)

Full plan: `shared/migration-plan.md`. Summary of next actions:

1. Scaffold `AlMunadiWindowsNative/`: .NET 8, WPF settings window + tray popup,
   `NotifyIcon` tray (WinForms interop or H.NotifyIcon).
2. Port behavior against `shared/fixtures/behavior-fixtures.json` (xUnit suite
   reading the same file). Reuse `%APPDATA%/AlMunadi/{settings,cache}.json`
   unchanged (`shared/*-schema.json`) so user migration is a no-op.
3. Notifications via `Microsoft.Toolkit.Uwp.Notifications` with
   `scenario=alarm` for DND bypass (replaces the PowerShell hack); adhan via
   `MediaPlayer` (lifts the WAV-only limit).
4. New `windows-native-release.yml` building a self-contained single-file exe;
   ship **side-by-side** with the Python exe for ≥2 releases.
5. Parity checklist before dropping the Python exe: 6 tray modes, popup,
   6 settings sections, search, paste URL, saved mosques, per-prayer
   notifications/reminders/adhan/DND, offsets, offline cache, update check,
   launch at login, 5 languages, HiDPI, light/dark.

## 6. Workstream D — Linux native rewrite (Rust; compiles anywhere, GUI needs a desktop)

`AlMunadiLinuxNative/` already holds the fixture-verified behavior core.

1. Tray spike: `ksni` (StatusNotifier) icon + label; **decision gate** — test on
   KDE, XFCE, Cinnamon, MATE; if older trays (XEmbed-only) fail, switch to Qt.
2. Settings/cache IO with `serde`, reusing `~/.config/AlMunadi/*.json` unchanged.
3. Mawaqit client (`reqwest` + rustls; API first, HTML `confData` fallback),
   async with 15s timeout.
4. Notifications via `notify-rust` (urgency critical = DND bypass), audio via
   `rodio` with graceful no-audio fallback.
5. Settings UI: GTK4/libadwaita. Package as a single binary first, evaluate
   Flatpak later. Same parity checklist and ≥2-release overlap as Windows.

## 7. Workstream E — ship the current branch (Python apps interim)

1. Smoke-test from the branch on real machines:
   - Windows: `python AlMunadiWindows/al_munadi.py` — first run, search,
     all 6 settings sections, test notification/adhan, tray modes, offsets.
   - Linux: `python3 AlMunadiLinux/al_munadi_linux.py` — same pass.
2. Run the suites: `python -m pytest AlMunadiWindows/test_al_munadi.py` (72),
   `node --test tests/` (184), `cargo test --manifest-path
   AlMunadiLinuxNative/Cargo.toml` (8).
3. Merge `claude/loving-franklin-8ufs4d` → `main`. This auto-releases
   **v1.0.9** with all four platform builds — intended, but only after the
   smoke test.
4. Recapture screenshots afterwards (`docs/screenshots/README.md` lists what's
   stale after the repaint).

## 8. Workstream F — website & ops follow-ups

1. **Rotate the Cloudflare API token** that was pasted into chat, then update
   the `CLOUDFLARE_API_TOKEN` repo secret. (High priority, 5 minutes.)
2. OG/social image: create a real 1200×630 `site/og.png` and reference it in
   `site/index.html` (the OG tags exist; image is the missing piece). Bump the
   `?v=` query strings if other assets change.
3. Optional: purge the Cloudflare zone cache after big site deploys, or keep
   relying on the `?v=N` cache-busting convention.

---

## 9. Quick reference — test commands

```bash
python -m pytest AlMunadiWindows/test_al_munadi.py -q   # Python core + apps (72)
node --test tests/                                       # GNOME JS utils (184)
cargo test --manifest-path AlMunadiLinuxNative/Cargo.toml  # Rust core (8)
node --test site/tests/                                  # site utils (36)
```

All four suites must stay green; the first three assert the same
`shared/fixtures/behavior-fixtures.json`.
