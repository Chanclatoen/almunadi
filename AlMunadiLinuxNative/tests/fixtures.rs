//! Asserts the shared cross-platform fixtures, exactly like the Python suite
//! (AlMunadiWindows/test_al_munadi.py) and the GNOME JS suite
//! (tests/test_utils.js). If this passes, the Rust core matches the shipping
//! clients' behavior.

use almunadi_core::*;
use serde_json::Value;

fn fixtures() -> Value {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../shared/fixtures/behavior-fixtures.json"
    );
    serde_json::from_str(&std::fs::read_to_string(path).expect("fixtures readable"))
        .expect("fixtures valid JSON")
}

#[test]
fn countdown_matches_fixtures() {
    let fx = fixtures();
    for (fmt, full) in [("compact", false), ("full", true)] {
        for case in fx["countdown"][fmt].as_array().unwrap() {
            let remaining = case["remaining_minutes"].as_i64().unwrap();
            assert_eq!(
                format_countdown(remaining, full),
                case["expected"].as_str().unwrap(),
                "countdown {fmt} {remaining}"
            );
        }
    }
}

#[test]
fn elapsed_matches_fixtures() {
    let fx = fixtures();
    for (fmt, full) in [("compact", false), ("full", true)] {
        for case in fx["elapsed_since"][fmt].as_array().unwrap() {
            let elapsed = case["elapsed_minutes"].as_i64().unwrap();
            assert_eq!(
                format_elapsed(elapsed, full),
                case["expected"].as_str().unwrap(),
                "elapsed {fmt} {elapsed}"
            );
        }
    }
}

#[test]
fn tray_title_matches_fixtures() {
    let fx = fixtures();
    for case in fx["tray_title"].as_array().unwrap() {
        assert_eq!(
            format_tray_title(
                case["name"].as_str().unwrap(),
                case["time"].as_str().unwrap(),
                case["countdown"].as_str().unwrap(),
                case["mode"].as_str().unwrap(),
            ),
            case["expected"].as_str().unwrap(),
            "tray mode {}",
            case["mode"]
        );
    }
}

#[test]
fn iqama_matches_fixtures() {
    let fx = fixtures();
    for case in fx["iqama"].as_array().unwrap() {
        let iqama = case["iqama"].as_str();
        let expected = case["expected"].as_str().map(str::to_string);
        assert_eq!(
            resolve_iqama(case["prayer_time"].as_str().unwrap(), iqama),
            expected,
            "iqama {:?}",
            case["iqama"]
        );
    }
}

#[test]
fn offsets_match_fixtures() {
    let fx = fixtures();
    let apply = &fx["prayer_offsets"]["apply"];
    let times: Vec<&str> = apply["times"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v.as_str().unwrap())
        .collect();
    let offsets = apply["offsets"].as_object().unwrap();
    let expected: Vec<&str> = apply["expected"]
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v.as_str().unwrap())
        .collect();
    for (i, time) in times.iter().enumerate() {
        let offset = offsets
            .get(PRAYER_NAMES[i])
            .and_then(Value::as_i64)
            .unwrap_or(0);
        assert_eq!(apply_offset(time, offset), expected[i], "offset {}", PRAYER_NAMES[i]);
    }
    for case in fx["prayer_offsets"]["clamp"].as_array().unwrap() {
        // Junk/null stored values normalize to 0 before clamping.
        let input = case["input"].as_i64().unwrap_or(0);
        assert_eq!(
            clamp_offset(input),
            case["expected"].as_i64().unwrap(),
            "clamp {:?}",
            case["input"]
        );
    }
}

#[test]
fn jumuah_key_matches_fixtures() {
    let fx = fixtures();
    for case in fx["jumuah_notification_key"].as_array().unwrap() {
        assert_eq!(
            notification_key_for_index(
                case["index"].as_u64().unwrap() as usize,
                case["is_friday"].as_bool().unwrap(),
                case["has_jumua"].as_bool().unwrap(),
            ),
            case["expected"].as_str().unwrap(),
        );
    }
}

#[test]
fn version_compare_matches_fixtures() {
    let fx = fixtures();
    for case in fx["version_compare"].as_array().unwrap() {
        assert_eq!(
            is_newer_version(
                case["current"].as_str().unwrap(),
                case["latest"].as_str().unwrap(),
            ),
            case["is_newer"].as_bool().unwrap(),
            "{:?}",
            case
        );
    }
}

#[test]
fn slug_extraction_matches_fixtures() {
    let fx = fixtures();
    for case in fx["slug_extraction"].as_array().unwrap() {
        let expected = case["expected"].as_str().map(str::to_string);
        assert_eq!(
            extract_slug(case["input"].as_str().unwrap()),
            expected,
            "slug {:?}",
            case["input"]
        );
    }
}
