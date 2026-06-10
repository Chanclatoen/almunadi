namespace AlMunadi.Core;

public sealed class AppSettings
{
    public string MosqueUrl { get; set; } = string.Empty;
    public bool NotificationsEnabled { get; set; } = true;
    public string Language { get; set; } = "en";
    public bool AdhanEnabled { get; set; }
    public string AdhanPath { get; set; } = string.Empty;
    public string DisplayMode { get; set; } = "countdown";
    public string CountdownFormat { get; set; } = "compact";
    public bool DndBypass { get; set; } = true;
    public List<SavedMosque> SavedMosques { get; set; } = [];
    public Dictionary<string, PrayerNotificationSettings> PrayerNotificationSettings { get; set; } = [];
    public Dictionary<string, int> PrayerOffsets { get; set; } = [];
}

public sealed class SavedMosque
{
    public string Url { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
}

public sealed class PrayerNotificationSettings
{
    public bool Enabled { get; set; } = true;
    public int ReminderMinutes { get; set; }
    public bool? AdhanEnabled { get; set; }
    public bool? DndBypass { get; set; }
}

public sealed class PrayerCache
{
    public List<string> Times { get; set; } = [];
    public string? Shuruq { get; set; }
    public string Name { get; set; } = string.Empty;
    public List<string?>? Iqama { get; set; }
    public bool IqamaEnabled { get; set; }
    public string? Jumua { get; set; }
    public string? Jumua2 { get; set; }
    public string? HijriDate { get; set; }
    public string? QiblaDirection { get; set; }
    public string Date { get; set; } = string.Empty;
}
