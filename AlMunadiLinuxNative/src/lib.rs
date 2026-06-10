//! Al Munadi behavior core — Rust spike for the future native Linux tray app.
//!
//! Scope: pure behavior logic only (no tray, no GTK, no network). It exists to
//! prove that `shared/fixtures/behavior-fixtures.json` is portable across
//! languages before the real rewrite starts; `tests/fixtures.rs` asserts the
//! exact same cases as the Python and GNOME JS suites. See
//! `shared/migration-plan.md` for the full plan and `shared/product-behavior.md`
//! for the semantics implemented here.

pub const PRAYER_NAMES: [&str; 5] = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];

/// "13:41" -> minutes since midnight.
pub fn to_minutes(time: &str) -> Option<i64> {
    let (h, m) = time.split_once(':')?;
    Some(h.trim().parse::<i64>().ok()? * 60 + m.trim().parse::<i64>().ok()?)
}

/// Minutes since midnight -> "HH:MM", wrapping across day boundaries.
pub fn from_minutes(total: i64) -> String {
    let normalized = total.rem_euclid(1440);
    format!("{:02}:{:02}", normalized / 60, normalized % 60)
}

/// Apply a manual offset (minutes) to an "HH:MM" time.
pub fn apply_offset(time: &str, offset: i64) -> String {
    if offset == 0 {
        return time.to_string();
    }
    match to_minutes(time) {
        Some(minutes) => from_minutes(minutes + offset),
        None => time.to_string(),
    }
}

/// Manual offsets are bounded to ±60 minutes.
pub fn clamp_offset(value: i64) -> i64 {
    value.clamp(-60, 60)
}

/// Countdown to the next prayer. `full` selects "-2h 18m" over "-2h18m".
pub fn format_countdown(remaining_minutes: i64, full: bool) -> String {
    if remaining_minutes <= 0 {
        return "now".to_string();
    }
    let (h, m) = (remaining_minutes / 60, remaining_minutes % 60);
    match (full, h > 0) {
        (true, true) => format!("-{}h {:02}m", h, m),
        (true, false) => format!("-{}m", m),
        (false, true) => format!("-{}h{:02}m", h, m),
        (false, false) => format!("-{}m", m),
    }
}

/// Elapsed time since the previous prayer ("since" display mode).
pub fn format_elapsed(elapsed_minutes: i64, full: bool) -> String {
    if elapsed_minutes <= 0 {
        return "now".to_string();
    }
    let (h, m) = (elapsed_minutes / 60, elapsed_minutes % 60);
    match (full, h > 0) {
        (true, true) => format!("+{}h {:02}m", h, m),
        (true, false) => format!("+{}m", m),
        (false, true) => format!("+{}h{:02}m", h, m),
        (false, false) => format!("+{}m", m),
    }
}

/// Tray/bar label per display mode. See product-behavior.md §3.
pub fn format_tray_title(name: &str, time: &str, countdown: &str, mode: &str) -> String {
    match mode {
        "icon" => name.to_string(),
        "since" => {
            if countdown.is_empty() {
                name.to_string()
            } else {
                format!("{}  {}", name, countdown)
            }
        }
        _ => {
            let mut parts: Vec<&str> = Vec::new();
            if matches!(mode, "countdown" | "time" | "name" | "compact") {
                parts.push(name);
            }
            if matches!(mode, "countdown" | "time") {
                parts.push(time);
            }
            if matches!(mode, "countdown" | "compact") && !countdown.is_empty() {
                parts.push(countdown);
            }
            if parts.is_empty() {
                name.to_string()
            } else {
                parts.join("  ")
            }
        }
    }
}

/// Resolve a Mawaqit iqama value: "HH:MM" passes through, "+N"/"N" adds
/// minutes to the prayer time, zero/empty yields None.
pub fn resolve_iqama(prayer_time: &str, iqama: Option<&str>) -> Option<String> {
    let val = iqama?.trim();
    if val.is_empty() || val == "0" || val == "+0" {
        return None;
    }
    let val = val.trim_start_matches('+');
    if val.contains(':') {
        return Some(val.to_string());
    }
    let offset: i64 = val.parse().ok()?;
    if offset <= 0 {
        return None;
    }
    let total = to_minutes(prayer_time)? + offset;
    Some(format!("{:02}:{:02}", (total / 60) % 24, total % 60))
}

/// Which per-prayer notification settings apply: Jumuah replaces Dhuhr
/// (index 1) on Fridays when the mosque provides a Jumuah time.
pub fn notification_key_for_index(index: usize, is_friday: bool, has_jumua: bool) -> &'static str {
    if index == 1 && is_friday && has_jumua {
        return "Jumuah";
    }
    PRAYER_NAMES[index]
}

/// Parse "1.2.3" into a comparable vector, tolerating junk like "1.2.3-beta".
pub fn version_tuple(version: &str) -> Vec<u64> {
    let parts: Vec<u64> = version
        .split('.')
        .map(|chunk| {
            let digits: String = chunk
                .trim()
                .chars()
                .take_while(|c| c.is_ascii_digit())
                .collect();
            digits.parse().unwrap_or(0)
        })
        .collect();
    if parts.is_empty() {
        vec![0]
    } else {
        parts
    }
}

pub fn is_newer_version(current: &str, latest: &str) -> bool {
    version_tuple(latest) > version_tuple(current)
}

/// Extract the mosque slug from a Mawaqit URL
/// (`mawaqit.net/<lang>/(w/)?<slug>`), mirroring the Python/JS regex.
pub fn extract_slug(url: &str) -> Option<String> {
    let idx = url.find("mawaqit.net/")?;
    let rest = &url[idx + "mawaqit.net/".len()..];
    let (lang, mut path) = rest.split_once('/')?;
    if lang.is_empty() || !lang.chars().all(|c| c.is_alphanumeric() || c == '_') {
        return None;
    }
    if let Some(stripped) = path.strip_prefix("w/") {
        if !stripped.trim_end_matches('/').is_empty() {
            path = stripped;
        }
    }
    let slug = path.trim_end_matches('/');
    if slug.is_empty() {
        None
    } else {
        Some(slug.to_string())
    }
}
