// Minimal translation table for the widget. Only includes the keys the widget
// actually renders; the main Python app owns the full table in
// core/al_munadi_core.py. Falls back to English for missing keys.

using System.Collections.Generic;

namespace AlMunadi.Widget;

public static class Translations
{
    private static readonly Dictionary<string, Dictionary<string, string>> Map = new()
    {
        ["en"] = new()
        {
            ["Fajr"] = "Fajr", ["Dhuhr"] = "Dhuhr", ["Asr"] = "Asr", ["Maghrib"] = "Maghrib", ["Isha"] = "Isha",
            ["Jumuah"] = "Jumuah", ["Shuruq"] = "Shuruq", ["Iqama"] = "Iqama", ["Qibla"] = "Qibla",
            ["now"] = "now", ["next_prayer"] = "Next Prayer",
        },
        ["nl"] = new()
        {
            ["Fajr"] = "Fadjr", ["Dhuhr"] = "Dhuhr", ["Asr"] = "Asr", ["Maghrib"] = "Maghrib", ["Isha"] = "Isha",
            ["Jumuah"] = "Joemoe'a", ["Shuruq"] = "Zonsopgang", ["Iqama"] = "Iqama", ["Qibla"] = "Qibla",
            ["now"] = "nu", ["next_prayer"] = "Volgend gebed",
        },
        ["ar"] = new()
        {
            ["Fajr"] = "الفجر", ["Dhuhr"] = "الظهر", ["Asr"] = "العصر", ["Maghrib"] = "المغرب", ["Isha"] = "العشاء",
            ["Jumuah"] = "الجمعة", ["Shuruq"] = "الشروق", ["Iqama"] = "الإقامة", ["Qibla"] = "القبلة",
            ["now"] = "الآن", ["next_prayer"] = "الصلاة القادمة",
        },
        ["fr"] = new()
        {
            ["Fajr"] = "Fajr", ["Dhuhr"] = "Dhouhr", ["Asr"] = "Asr", ["Maghrib"] = "Maghrib", ["Isha"] = "Icha",
            ["Jumuah"] = "Joumouâ", ["Shuruq"] = "Shourouq", ["Iqama"] = "Iqama", ["Qibla"] = "Qibla",
            ["now"] = "maintenant", ["next_prayer"] = "Prochaine prière",
        },
        ["tr"] = new()
        {
            ["Fajr"] = "İmsak", ["Dhuhr"] = "Öğle", ["Asr"] = "İkindi", ["Maghrib"] = "Akşam", ["Isha"] = "Yatsı",
            ["Jumuah"] = "Cuma", ["Shuruq"] = "Güneş", ["Iqama"] = "İkamet", ["Qibla"] = "Kıble",
            ["now"] = "şimdi", ["next_prayer"] = "Sonraki Namaz",
        },
    };

    public static string T(string key, string language)
    {
        if (Map.TryGetValue(language, out var table) && table.TryGetValue(key, out var value))
        {
            return value;
        }
        if (Map["en"].TryGetValue(key, out var fallback))
        {
            return fallback;
        }
        return key;
    }
}
