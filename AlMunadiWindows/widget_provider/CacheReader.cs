// Reads the snake_case JSON files that AlMunadi.exe (the Python app) writes
// under %APPDATA%\AlMunadi\. We are read-only -- the main app stays the single
// Mawaqit consumer.

using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AlMunadi.Widget;

public sealed record CacheData(
    [property: JsonPropertyName("times")] List<string> Times,
    [property: JsonPropertyName("shuruq")] string? Shuruq,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("iqama")] List<string>? Iqama,
    [property: JsonPropertyName("iqama_enabled")] bool IqamaEnabled,
    [property: JsonPropertyName("jumua")] string? Jumua,
    [property: JsonPropertyName("jumua2")] string? Jumua2,
    [property: JsonPropertyName("hijri_date")] string? HijriDate,
    [property: JsonPropertyName("qibla_direction")] string? QiblaDirection,
    [property: JsonPropertyName("date")] string? Date);

public sealed record AppSettings(
    [property: JsonPropertyName("language")] string Language,
    [property: JsonPropertyName("countdown_format")] string CountdownFormat,
    [property: JsonPropertyName("prayer_offsets")] Dictionary<string, int>? PrayerOffsets);

public static class CacheReader
{
    public static string AppDataDir =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "AlMunadi");

    private static string CachePath => Path.Combine(AppDataDir, "cache.json");
    private static string SettingsPath => Path.Combine(AppDataDir, "settings.json");

    private static readonly JsonSerializerOptions s_options = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    };

    public static CacheData? LoadCache()
    {
        if (!File.Exists(CachePath)) return null;
        try
        {
            using var stream = File.OpenRead(CachePath);
            return JsonSerializer.Deserialize<CacheData>(stream, s_options);
        }
        catch (Exception)
        {
            return null;
        }
    }

    public static AppSettings LoadSettings()
    {
        if (!File.Exists(SettingsPath))
        {
            return new AppSettings("en", "compact", null);
        }
        try
        {
            using var stream = File.OpenRead(SettingsPath);
            var parsed = JsonSerializer.Deserialize<AppSettings>(stream, s_options);
            return parsed ?? new AppSettings("en", "compact", null);
        }
        catch (Exception)
        {
            return new AppSettings("en", "compact", null);
        }
    }
}
