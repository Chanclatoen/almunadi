import json
import sys
from datetime import datetime
from unittest.mock import MagicMock

# Allow importing al_munadi on non-Windows platforms for unit tests
if sys.platform != "win32":
    sys.modules.setdefault("winsound", MagicMock())
    winotify_mock = MagicMock()
    winotify_mock.Notification = MagicMock
    winotify_mock.audio = MagicMock()
    sys.modules.setdefault("winotify", winotify_mock)
    sys.modules.setdefault("pystray", MagicMock())

from unittest.mock import patch

import pytest

from al_munadi import (
    extract_slug,
    format_countdown,
    get_next_prayer,
    parse_time,
    resolve_iqama,
    apply_offset,
    apply_prayer_offsets,
    merge_prayer_notification_settings,
    merge_prayer_offsets,
    format_tray_title,
    notification_key_for_index,
    should_play_adhan,
    default_prayer_notification_settings,
    prayer_datetime_events,
)


class TestExtractSlug:
    def test_full_url_with_w(self):
        assert extract_slug("https://mawaqit.net/en/w/arrahmaan-dordrecht") == "arrahmaan-dordrecht"

    def test_full_url_without_w(self):
        assert extract_slug("https://mawaqit.net/en/arrahmaan-dordrecht") == "arrahmaan-dordrecht"

    def test_url_with_trailing_slash(self):
        assert extract_slug("https://mawaqit.net/fr/w/my-mosque/") == "my-mosque"

    def test_different_language(self):
        assert extract_slug("https://mawaqit.net/fr/w/mosquee-paris") == "mosquee-paris"

    def test_invalid_url(self):
        assert extract_slug("https://example.com/mosque") is None

    def test_empty_string(self):
        assert extract_slug("") is None


class TestParseTime:
    def test_basic(self):
        dt = parse_time("13:30")
        assert dt.hour == 13
        assert dt.minute == 30
        assert dt.second == 0

    def test_midnight(self):
        dt = parse_time("00:00")
        assert dt.hour == 0
        assert dt.minute == 0

    def test_end_of_day(self):
        dt = parse_time("23:59")
        assert dt.hour == 23
        assert dt.minute == 59


class TestGetNextPrayer:
    @patch("al_munadi.datetime")
    def test_midday(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        idx, dt = get_next_prayer(times)
        assert idx == 1
        assert dt.hour == 12
        assert dt.minute == 30

    @patch("al_munadi.datetime")
    def test_after_isha(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        idx, dt = get_next_prayer(times)
        assert idx == 0
        assert dt.day == 9

    @patch("al_munadi.datetime")
    def test_before_fajr(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 3, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        idx, dt = get_next_prayer(times)
        assert idx == 0
        assert dt.hour == 5

    @patch("al_munadi.datetime")
    def test_isha_wrapped_after_midnight(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["05:30", "12:30", "16:00", "20:30", "00:15"]
        idx, dt = get_next_prayer(times)
        assert idx == 4
        assert dt.day == 9
        assert dt.hour == 0
        assert dt.minute == 15

    @patch("al_munadi.datetime")
    def test_fajr_wrapped_to_previous_evening(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["23:45", "12:30", "16:00", "20:30", "22:00"]
        idx, dt = get_next_prayer(times)
        assert idx == 0
        assert dt.day == 8
        assert dt.hour == 23
        assert dt.minute == 45


class TestFormatCountdown:
    @patch("al_munadi.datetime")
    def test_hours_and_minutes(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 10, 0, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target) == "-2h30m"

    @patch("al_munadi.datetime")
    def test_minutes_only(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 12, 15, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target) == "-15m"

    @patch("al_munadi.datetime")
    def test_full_format(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 10, 0, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target, {"countdown_format": "full"}) == "-2h 30m"

    @patch("al_munadi.datetime")
    def test_now(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 12, 30, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target) == "now"


class TestApplyOffset:
    def test_positive(self):
        assert apply_offset("12:30", 15) == "12:45"

    def test_negative(self):
        assert apply_offset("12:30", -30) == "12:00"

    def test_wrap_midnight(self):
        assert apply_offset("00:15", -30) == "23:45"


class TestApplyPrayerOffsets:
    def test_multiple(self):
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        offsets = {"Fajr": 5, "Dhuhr": -10, "Maghrib": 15, "Isha": -5}
        result = apply_prayer_offsets(times, offsets)
        assert result == ["05:35", "12:20", "16:00", "20:45", "21:55"]


class TestPrayerDateTimeEvents:
    def test_isha_wraps_to_tomorrow(self):
        base = datetime(2026, 6, 8, 23, 0, 0)
        events = prayer_datetime_events(["05:30", "12:30", "16:00", "20:30", "00:15"], base)
        assert events[4][1].day == 9
        assert events[4][1].hour == 0

    def test_fajr_wraps_to_previous_day(self):
        base = datetime(2026, 6, 8, 23, 0, 0)
        events = prayer_datetime_events(["23:45", "12:30", "16:00", "20:30", "22:00"], base)
        assert events[0][1].day == 7
        assert events[1][1].day == 8


class TestFormatTrayTitle:
    def test_countdown_mode(self):
        title = format_tray_title("Dhuhr", "12:30", "-1h30m", "countdown")
        assert title == "Dhuhr  12:30  -1h30m"

    def test_name_mode(self):
        title = format_tray_title("Dhuhr", "12:30", "-1h30m", "name")
        assert title == "Dhuhr"

    def test_icon_mode(self):
        title = format_tray_title("Dhuhr", "12:30", "-1h30m", "icon")
        assert title == "Dhuhr"


class TestNotificationSettings:
    def test_defaults(self):
        settings = default_prayer_notification_settings()
        assert settings["Fajr"]["enabled"] is True
        assert settings["Jumuah"]["reminder_minutes"] == 0

    def test_merge_disabled(self):
        merged = merge_prayer_notification_settings({"Asr": {"enabled": False}})
        assert merged["Asr"]["enabled"] is False
        assert merged["Fajr"]["enabled"] is True

    def test_jumuah_key(self):
        assert notification_key_for_index(1, True, True) == "Jumuah"
        assert notification_key_for_index(1, False, True) == "Dhuhr"

    def test_should_play_adhan(self):
        assert should_play_adhan({"adhan_enabled": None}, True) is True
        assert should_play_adhan({"adhan_enabled": False}, True) is False


class TestMergeOffsets:
    def test_clamp(self):
        merged = merge_prayer_offsets({"Maghrib": 90})
        assert merged["Maghrib"] == 60


class TestResolveIqama:
    def test_offset_with_plus(self):
        result = resolve_iqama("12:30", "+15")
        assert result == "12:45"

    def test_offset_without_plus(self):
        result = resolve_iqama("12:30", "15")
        assert result == "12:45"

    def test_absolute_time(self):
        result = resolve_iqama("12:30", "13:00")
        assert result == "13:00"

    def test_zero_offset(self):
        assert resolve_iqama("12:30", "+0") is None
        assert resolve_iqama("12:30", "0") is None

    def test_none_value(self):
        assert resolve_iqama("12:30", None) is None

    def test_empty_string(self):
        assert resolve_iqama("12:30", "") is None

    def test_offset_crossing_hour(self):
        result = resolve_iqama("12:50", "+20")
        assert result == "13:10"
