# Al Munadi — Product Behavior Specification

This document defines the behavior every Al Munadi desktop client must implement.
Platforms share **behavior**, not compiled code: macOS stays SwiftUI, GNOME stays
GJS, Windows/Linux are Python today (C#/.NET and Rust/Qt are the migration
targets — see `migration-plan.md`). Schemas live next to this file; executable
cases live in `fixtures/behavior-fixtures.json` and are asserted by both the
Python and JS test suites.

## 1. Information hierarchy

Every client presents the same hierarchy, with native looks:

1. **Bar/tray/menu-bar label** — next prayer at a glance.
2. **Popup/dropdown** — header (mosque name, cached badge, Hijri date, Qibla),
   next-prayer emphasis, full daily schedule, Shuruq (visually distinct),
   Jumuah/Jumuah 2 on Fridays, footer actions (Refresh / Settings / Quit /
   Update available).
3. **Settings** — sections in this order: Mosque → Display → Notifications →
   Adhan → Prayer adjustments → App.
4. **Mosque search** — name/city search, loading state, no-results state,
   calm error state, paste-URL alternative.

## 2. Visual identity

- Primary: deep forest green / emerald (`#0F5D47` light contexts, `#46C79E` on dark).
- Dark surfaces: deep charcoal (`#14130F` background, `#1F1D17` cards).
- Accent: saffron/gold (`#E3B15A`), used sparingly (Shuruq, Jumuah, warnings).
- Prayer hues (refined, calm): Fajr `#D9A05B`, Dhuhr/Jumuah `#E3B15A`,
  Asr `#BC8A52`, Maghrib `#C96B4A`, Isha `#7D93C4`.
- Next prayer: emerald highlight + left accent bar. Past prayers: dimmed.
- Times and countdowns use tabular/monospaced digits where the platform allows.
- Errors are calm saffron/amber, never red walls; no raw exception text in UI.

## 3. Display modes (bar label)

| Mode        | Format                       | Example                  |
|-------------|------------------------------|--------------------------|
| `countdown` | `{name}  {time}  {countdown}`| `Dhuhr  13:41  -2h18m`   |
| `time`      | `{name}  {time}`             | `Dhuhr  13:41`           |
| `name`      | `{name}`                     | `Dhuhr`                  |
| `compact`   | `{name}  {countdown}`        | `Dhuhr  -2h18m`          |
| `icon`      | icon only (tooltip = name)   |                          |
| `since`     | `{since-label}  {elapsed}`   | `Since Fajr  +1h12m`     |

Countdown formats: `compact` → `-2h18m` / `-15m`; `full` → `-2h 18m` / `-15m`.
Elapsed uses `+` instead of `-`. Zero or negative remaining → localized `now`.
When data comes from cache, append the localized `cached_data` hint where the
platform shows tooltips/labels.

## 4. Prayer-time semantics

- Order is always Fajr, Dhuhr, Asr, Maghrib, Isha; Shuruq is metadata, never a
  notification target.
- **Jumuah** replaces Dhuhr (display + notifications) on Fridays when the mosque
  provides a `jumua` time; `jumua2` is displayed separately, never notified.
- **Iqama**: `HH:MM` values pass through; `+N`/`N` minute offsets are added to the
  prayer time; `0`, `+0`, empty → no iqama. Only shown if the mosque enables it.
- **Manual offsets**: per-prayer, clamped to ±60 minutes, applied at display and
  notification time, never written back to cache. Invalid stored values → 0.
- Day wrap: times that cross midnight (e.g. Isha `00:15`) belong to the
  following calendar day; the first prayer can wrap to the previous evening.
  See `prayer_datetime_events` (Python) / `prayerEvents` (JS).

## 5. Notifications

- At prayer time: title `{name} - {time}`, body localized `notification_body`.
- Reminder (N min before): title `{name}`, body localized `reminder_body`
  ("Dhuhr in 10 min"). Only fired when `reminder_minutes > 0`.
- Per-prayer settings: `enabled`, `reminder_minutes` (0–120), `adhan_enabled`
  override (true/false/null=global), `dnd_bypass` override (same tri-state).
- DND/Focus bypass is best-effort and platform-dependent:
  - Windows: alarm-scenario toast via PowerShell fallback.
  - Linux: `notify-send --urgency critical`.
  - GNOME: native MessageTray with urgency.
  - macOS: **not currently bypassing** — time-sensitive entitlement is disabled
    until provisioning supports it. Never claim otherwise in UI or docs.
- Timers are cancelled and rescheduled wholesale on every data/settings change;
  there must never be duplicate timers (GNOME must clear all sources in
  `disable()`).

## 6. Adhan audio

- Globally off by default; user supplies their own audio file (no bundled audio).
- Validate the file exists before playback; show `adhan_file_missing` otherwise.
- When adhan plays at prayer time, it replaces the notification sound path.
- Never overlap playback: starting a new adhan stops the previous one.
- Settings provide Test adhan and Stop adhan actions.

## 7. First run / empty / error / cache states

- No mosque configured: bar label shows localized `set_mosque`; the default
  click action opens setup; the popup shows a welcome state (app name, one-line
  explanation that Al Munadi uses public Mawaqit pages, primary
  "Find your mosque" action, paste-URL alternative in settings).
- Fetch fails with cache: keep showing cached data with localized
  `cached_data` badge plus calm `fetch_error` message; retry on next refresh.
- Fetch fails without cache: calm error + easy refresh; never a stack trace.
- Search: show `searching` while in flight (never block the UI thread),
  `no_results` when empty, `search_failed` on error.

## 8. Updates

- Check GitHub releases at most once per 24h; failures are silent.
- Compare versions numerically per dot segment, tolerating suffixes
  (`1.0.9-beta` → `1.0.9`); see `version_compare` fixtures.
- Surface as a quiet "Update available (vX.Y.Z)" row linking to the releases
  page. Never auto-download, never interrupt.

## 9. Data fetching

- Resolve the Mawaqit slug from the configured URL
  (`mawaqit.net/<lang>/(w/)?<slug>`), try the structured API first, fall back to
  scraping `confData` from the public HTML page.
- Search queries and slugs must be URL-encoded.
- All network calls are async/off the UI thread with timeouts (15s fetch, 10s
  update check). On success, write the cache (see `cache-schema.json`).
- Refresh daily around midnight, plus manual refresh.

## 10. Languages

English, Dutch, Arabic, French, Turkish. Missing keys fall back to English.
Arabic must remain readable in RTL contexts. Key registry:
`translation-keys.json`.

## 11. Platform polish backlog

Items specified here but not yet implemented everywhere (requires the platform
toolchain to verify, so they ship separately):

- **macOS (SwiftUI — needs Xcode to validate):** first-run empty state in the
  dropdown matching §7; next-prayer card at the top of the dropdown; settings
  regrouped into the §1 section order with Test adhan / Stop adhan / Reset
  offsets; cached-data badge in the dropdown header; widget empty/offline
  states; adopt the new translation keys in `Shared/Translations.swift`.
- **GNOME (GJS):** first-run menu item ("Find your mosque") when no mosque is
  configured; adopt the new translation keys in `translations/*.json`;
  optional next-prayer header card in the popup menu.
- **Windows/Linux (Python):** a dedicated "Retry" action in the popup error
  banner (currently Refresh serves this role).
