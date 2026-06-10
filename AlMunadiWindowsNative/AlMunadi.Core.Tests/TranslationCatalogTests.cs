using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class TranslationCatalogTests
{
    [Fact]
    public void LoadsAllSupportedLanguagesAndFallsBackToEnglish()
    {
        Assert.Equal("Instellingen", new TranslationCatalog("nl")["settings"]);
        Assert.Equal("Settings", new TranslationCatalog("unknown")["settings"]);
        Assert.Equal("missing_key", new TranslationCatalog("en")["missing_key"]);
    }

    [Fact]
    public void FormatsPlaceholdersAndPrayerNames()
    {
        var translations = new TranslationCatalog("en");
        Assert.Equal("Dhuhr in 10 min", translations.Get("reminder_body", new Dictionary<string, object?>
        {
            ["name"] = "Dhuhr",
            ["minutes"] = 10,
        }));
        Assert.Equal("Jumuah", translations.PrayerName("Jumuah"));
    }
}
