import json
from datetime import datetime
from unittest.mock import patch

import pytest

from next_prayer import (
    extract_slug,
    format_countdown,
    get_next_prayer,
    parse_time,
    resolve_iqama,
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
    @patch("next_prayer.datetime")
    def test_midday(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 12, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        idx, dt = get_next_prayer(times)
        assert idx == 1
        assert dt.hour == 12
        assert dt.minute == 30

    @patch("next_prayer.datetime")
    def test_after_isha(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        idx, dt = get_next_prayer(times)
        assert idx == 0
        assert dt.day == 9

    @patch("next_prayer.datetime")
    def test_before_fajr(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 3, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        times = ["05:30", "12:30", "16:00", "20:30", "22:00"]
        idx, dt = get_next_prayer(times)
        assert idx == 0
        assert dt.hour == 5


class TestFormatCountdown:
    @patch("next_prayer.datetime")
    def test_hours_and_minutes(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 10, 0, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target) == "-2h30m"

    @patch("next_prayer.datetime")
    def test_minutes_only(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 12, 15, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target) == "-15m"

    @patch("next_prayer.datetime")
    def test_now(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 6, 8, 12, 30, 0)
        target = datetime(2026, 6, 8, 12, 30, 0)
        assert format_countdown(target) == "now"


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
