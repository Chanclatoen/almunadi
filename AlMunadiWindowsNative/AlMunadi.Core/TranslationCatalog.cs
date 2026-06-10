using System.Reflection;
using System.Text.Json;

namespace AlMunadi.Core;

public sealed class TranslationCatalog
{
    private static readonly Lazy<IReadOnlyDictionary<string, Dictionary<string, string>>> Catalog = new(Load);
    private readonly string language;

    public TranslationCatalog(string? language)
    {
        this.language = Catalog.Value.ContainsKey(language ?? string.Empty) ? language! : "en";
    }

    public string this[string key] => Get(key);

    public string Get(string key, IReadOnlyDictionary<string, object?>? values = null)
    {
        var text = Catalog.Value[language].GetValueOrDefault(key)
            ?? Catalog.Value["en"].GetValueOrDefault(key)
            ?? key;
        if (values is null)
        {
            return text;
        }

        foreach (var (name, value) in values)
        {
            text = text.Replace($"{{{name}}}", value?.ToString() ?? string.Empty, StringComparison.Ordinal);
        }

        return text;
    }

    public string PrayerName(string name) => Get(name switch
    {
        "Fajr" => "prayer_fajr",
        "Dhuhr" => "prayer_dhuhr",
        "Asr" => "prayer_asr",
        "Maghrib" => "prayer_maghrib",
        "Isha" => "prayer_isha",
        "Shuruq" => "prayer_shuruq",
        "Jumuah" => "prayer_jumuah",
        "Jumuah 2" => "prayer_jumuah2",
        _ => name,
    });

    private static IReadOnlyDictionary<string, Dictionary<string, string>> Load()
    {
        var assembly = typeof(TranslationCatalog).Assembly;
        var resource = assembly.GetManifestResourceNames().Single(name => name.EndsWith("translations.json", StringComparison.Ordinal));
        using var stream = assembly.GetManifestResourceStream(resource)!;
        return JsonSerializer.Deserialize<Dictionary<string, Dictionary<string, string>>>(stream)
            ?? throw new InvalidDataException("Embedded translations are invalid.");
    }
}
