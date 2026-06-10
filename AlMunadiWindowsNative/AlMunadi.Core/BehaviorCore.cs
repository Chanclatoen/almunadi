using System.Globalization;
using System.Text.RegularExpressions;

namespace AlMunadi.Core;

public static partial class BehaviorCore
{
    public static readonly string[] PrayerNames = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"];

    public static string FormatCountdown(int remainingMinutes, string format = "compact") =>
        FormatDuration(remainingMinutes, '-', format);

    public static string FormatElapsed(int elapsedMinutes, string format = "compact") =>
        FormatDuration(elapsedMinutes, '+', format);

    public static string FormatTrayTitle(
        string mode,
        string name,
        string time,
        string countdown)
    {
        return mode switch
        {
            "time" => $"{name}  {time}",
            "name" or "icon" => name,
            "compact" or "since" => string.IsNullOrEmpty(countdown) ? name : $"{name}  {countdown}",
            _ => $"{name}  {time}  {countdown}",
        };
    }

    public static string? ResolveIqama(string prayerTime, string? iqama)
    {
        var value = iqama?.Trim();
        if (string.IsNullOrEmpty(value) || value is "0" or "+0")
        {
            return null;
        }

        if (value.Contains(':'))
        {
            return TryParseTime(value, out _) ? value : null;
        }

        if (!int.TryParse(value.TrimStart('+'), NumberStyles.Integer, CultureInfo.InvariantCulture, out var offset)
            || offset <= 0
            || !TryParseTime(prayerTime, out var prayerMinutes))
        {
            return null;
        }

        return FromMinutes(prayerMinutes + offset);
    }

    public static string ApplyOffset(string time, int offset)
    {
        if (offset == 0 || !TryParseTime(time, out var minutes))
        {
            return time;
        }

        return FromMinutes(minutes + offset);
    }

    public static int ClampOffset(object? value)
    {
        var parsed = value switch
        {
            int number => number,
            long number when number is >= int.MinValue and <= int.MaxValue => (int)number,
            _ => 0,
        };

        return Math.Clamp(parsed, -60, 60);
    }

    public static string NotificationKey(int index, bool isFriday, bool hasJumua)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(index);
        if (index >= PrayerNames.Length)
        {
            throw new ArgumentOutOfRangeException(nameof(index));
        }

        return index == 1 && isFriday && hasJumua ? "Jumuah" : PrayerNames[index];
    }

    public static bool IsNewerVersion(string current, string latest)
    {
        if (string.IsNullOrWhiteSpace(latest))
        {
            return false;
        }

        var currentParts = VersionParts(current);
        var latestParts = VersionParts(latest);
        var length = Math.Max(currentParts.Count, latestParts.Count);
        for (var index = 0; index < length; index++)
        {
            var currentPart = index < currentParts.Count ? currentParts[index] : 0;
            var latestPart = index < latestParts.Count ? latestParts[index] : 0;
            if (latestPart != currentPart)
            {
                return latestPart > currentPart;
            }
        }

        return false;
    }

    public static string? ExtractSlug(string? url)
    {
        if (string.IsNullOrWhiteSpace(url))
        {
            return null;
        }

        var match = MawaqitUrlRegex().Match(url);
        return match.Success ? match.Groups[1].Value : null;
    }

    private static string FormatDuration(int minutes, char prefix, string format)
    {
        if (minutes <= 0)
        {
            return "now";
        }

        var hours = minutes / 60;
        var remainder = minutes % 60;
        if (hours == 0)
        {
            return $"{prefix}{remainder}m";
        }

        var separator = format == "full" ? " " : string.Empty;
        return $"{prefix}{hours}h{separator}{remainder:00}m";
    }

    private static bool TryParseTime(string value, out int minutes)
    {
        minutes = 0;
        var parts = value.Split(':');
        if (parts.Length != 2
            || !int.TryParse(parts[0], NumberStyles.None, CultureInfo.InvariantCulture, out var hours)
            || !int.TryParse(parts[1], NumberStyles.None, CultureInfo.InvariantCulture, out var minutePart)
            || hours is < 0 or > 23
            || minutePart is < 0 or > 59)
        {
            return false;
        }

        minutes = (hours * 60) + minutePart;
        return true;
    }

    private static string FromMinutes(int totalMinutes)
    {
        var normalized = ((totalMinutes % 1440) + 1440) % 1440;
        return $"{normalized / 60:00}:{normalized % 60:00}";
    }

    private static List<int> VersionParts(string version)
    {
        return version.Split('.')
            .Select(part => new string(part.Trim().TakeWhile(char.IsDigit).ToArray()))
            .Select(part => int.TryParse(part, out var number) ? number : 0)
            .ToList();
    }

    [GeneratedRegex(@"^https?://(?:www\.)?mawaqit\.net/\w+/(?:w/)?([^/?#]+)/?(?:[?#].*)?$", RegexOptions.IgnoreCase)]
    private static partial Regex MawaqitUrlRegex();
}
