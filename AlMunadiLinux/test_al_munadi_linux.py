import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.modules.setdefault("pystray", MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parent))

from al_munadi_linux import (  # noqa: E402
    LANGUAGE_LABELS,
    _set_language,
    apply_offset,
    apply_prayer_offsets,
    default_prayer_notification_settings,
    extract_slug,
    format_countdown,
    format_elapsed_since,
    format_hijri_date,
    format_tray_title,
    get_last_prayer,
    get_next_prayer,
    merge_prayer_notification_settings,
    merge_prayer_offsets,
    notification_key_for_index,
    parse_time,
    prayer_datetime_events,
    qibla_bearing,
    resolve_iqama,
    should_play_adhan,
    t,
)


class TestLinuxHelpers:
    def test_extract_slug(self):
        assert extract_slug("https://mawaqit.net/en/w/arrahmaan-dordrecht") == "arrahmaan-dordrecht"
        assert extract_slug("https://example.com/mosque") is None

    def test_parse_time(self):
        dt = parse_time("13:30")
        assert dt.hour == 13
        assert dt.minute == 30

    @patch("core.al_munadi_core.datetime")
    def test_get_next_prayer_isha_wrapped_after_midnight(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        idx, dt = get_next_prayer(["05:30", "12:30", "16:00", "20:30", "00:15"])
        assert idx == 4
        assert dt.day == 9
        assert dt.hour == 0
        assert dt.minute == 15

    @patch("core.al_munadi_core.datetime")
    def test_get_next_prayer_fajr_wrapped_to_previous_evening(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        idx, dt = get_next_prayer(["23:45", "12:30", "16:00", "20:30", "22:00"])
        assert idx == 0
        assert dt.day == 8
        assert dt.hour == 23
        assert dt.minute == 45

    @patch("core.al_munadi_core.datetime")
    def test_format_countdown(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 10, 0, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target) == "-2h30m"
        assert format_countdown(target, {"countdown_format": "full"}) == "-2h 30m"

    @patch("core.al_munadi_core.datetime")
    def test_elapsed_since(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 13, 45, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_elapsed_since(target) == "+1h15m"

    def test_apply_offset(self):
        assert apply_offset("12:30", 15) == "12:45"
        assert apply_offset("00:15", -30) == "23:45"
        assert apply_offset("23:45", 30) == "00:15"

    def test_apply_prayer_offsets(self):
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        offsets = {"Fajr": 5, "Dhuhr": -10, "Maghrib": 15, "Isha": -5}
        assert apply_prayer_offsets(times, offsets) == ["05:35", "12:20", "16:00", "20:45", "21:55"]

    def test_prayer_datetime_events(self):
        base = datetime(2026, 6, 8, 23, 0, 0)
        isha_events = prayer_datetime_events(["05:30", "12:30", "16:00", "20:30", "00:15"], base)
        assert isha_events[4][1].day == 9
        fajr_events = prayer_datetime_events(["23:45", "12:30", "16:00", "20:30", "22:00"], base)
        assert fajr_events[0][1].day == 7
        assert fajr_events[1][1].day == 8

    @patch("core.al_munadi_core.datetime")
    def test_get_last_prayer(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 17, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        idx, dt = get_last_prayer(["05:30", "12:30", "16:00", "20:30", "22:00"])
        assert idx == 2
        assert dt.hour == 16

    def test_format_tray_title(self):
        assert format_tray_title("Dhuhr", "12:30", "-1h30m", "countdown") == "Dhuhr  12:30  -1h30m"
        assert format_tray_title("Dhuhr", "12:30", "-1h30m", "icon") == "Dhuhr"

    def test_notification_settings(self):
        defaults = default_prayer_notification_settings()
        assert defaults["Fajr"]["enabled"] is True
        merged = merge_prayer_notification_settings({"Asr": {"enabled": False}})
        assert merged["Asr"]["enabled"] is False
        assert notification_key_for_index(1, True, True) == "Jumuah"
        assert notification_key_for_index(1, False, True) == "Dhuhr"
        assert should_play_adhan({"adhan_enabled": None}, True) is True
        assert should_play_adhan({"adhan_enabled": False}, True) is False

    def test_merge_offsets(self):
        merged = merge_prayer_offsets({"Maghrib": 90, "Isha": -5})
        assert merged["Maghrib"] == 60
        assert merged["Isha"] == -5

    def test_resolve_iqama(self):
        assert resolve_iqama("12:30", "+15") == "12:45"
        assert resolve_iqama("12:30", "13:00") == "13:00"
        assert resolve_iqama("12:30", "+0") is None

    def test_dutch_language_available(self):
        _set_language("nl")
        assert LANGUAGE_LABELS["nl"] == "Nederlands"
        assert t("settings") == "Instellingen"
        assert t("next_prayer") == "Volgend gebed"
        _set_language("en")

    def test_islamic_metadata_helpers(self):
        assert 120 <= qibla_bearing(52.0, 5.0) <= 130
        assert format_hijri_date(datetime(2026, 6, 8), adjustment=0).endswith("AH")
