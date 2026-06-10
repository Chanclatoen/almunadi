using System.Globalization;

namespace AlMunadi.Core;

public static class MosqueMetadata
{
    private const double KaabaLatitude = 21.422487;
    private const double KaabaLongitude = 39.826206;
    private static readonly string[] HijriMonths =
    [
        "Muharram", "Safar", "Rabi al-awwal", "Rabi al-thani", "Jumada al-awwal", "Jumada al-thani",
        "Rajab", "Shaban", "Ramadan", "Shawwal", "Dhu al-Qadah", "Dhu al-Hijjah",
    ];

    public static string? FormatQiblaDirection(double? latitude, double? longitude)
    {
        if (latitude is null || longitude is null)
        {
            return null;
        }

        var lat1 = DegreesToRadians(latitude.Value);
        var lat2 = DegreesToRadians(KaabaLatitude);
        var deltaLongitude = DegreesToRadians(KaabaLongitude - longitude.Value);
        var y = Math.Sin(deltaLongitude);
        var x = (Math.Cos(lat1) * Math.Tan(lat2)) - (Math.Sin(lat1) * Math.Cos(deltaLongitude));
        var bearing = (Math.Round(RadiansToDegrees(Math.Atan2(y, x))) + 360) % 360;
        return $"{bearing.ToString(CultureInfo.InvariantCulture)}°";
    }

    public static string FormatHijriDate(DateOnly date, int adjustment = 0)
    {
        var julianDay = GregorianToJulianDay(date.Year, date.Month, date.Day) + adjustment;
        var year = (int)Math.Floor((30d * (julianDay - 1948439) + 10646) / 10631);
        var month = Math.Min(12, (int)Math.Ceiling((julianDay - (29 + IslamicToJulianDay(year, 1, 1))) / 29.5) + 1);
        var day = (int)(julianDay - IslamicToJulianDay(year, month, 1) + 1);
        return $"{day} {HijriMonths[month - 1]} {year} AH";
    }

    private static int GregorianToJulianDay(int year, int month, int day)
    {
        var a = (14 - month) / 12;
        var y = year + 4800 - a;
        var m = month + (12 * a) - 3;
        return day + (((153 * m) + 2) / 5) + (365 * y) + (y / 4) - (y / 100) + (y / 400) - 32045;
    }

    private static double IslamicToJulianDay(int year, int month, int day) =>
        day + Math.Ceiling(29.5 * (month - 1)) + ((year - 1) * 354) + Math.Floor((3 + (11d * year)) / 30) + 1948438;

    private static double DegreesToRadians(double value) => value * Math.PI / 180;
    private static double RadiansToDegrees(double value) => value * 180 / Math.PI;
}
