// COM widget provider for the Windows 11 Widget Board.
// Activated by the Widget Service when the user adds a widget; receives
// CreateWidget/Activate/Deactivate/DeleteWidget callbacks via IWidgetProvider.
// We render each widget as an Adaptive Card v1.5 populated from
// %APPDATA%\AlMunadi\cache.json -- no network calls, no Mawaqit fetches.

using System;
using System.Collections.Concurrent;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading;
using Microsoft.Windows.Widgets.Providers;

namespace AlMunadi.Widget;

[ComVisible(true)]
[ClassInterface(ClassInterfaceType.None)]
[Guid("81b9ff95-40c9-44ca-a8d0-18f34e778b52")] // CLSID -- referenced from Package.appxmanifest
public sealed class AlMunadiWidgetProvider : IWidgetProvider
{
    private sealed record ActiveWidget(string Id, string DefinitionId, string Size, Timer Timer);

    private readonly ConcurrentDictionary<string, ActiveWidget> _widgets = new();
    private readonly FileSystemWatcher? _watcher;

    public AlMunadiWidgetProvider()
    {
        try
        {
            if (Directory.Exists(CacheReader.AppDataDir))
            {
                _watcher = new FileSystemWatcher(CacheReader.AppDataDir, "cache.json")
                {
                    NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.Size,
                    EnableRaisingEvents = true,
                };
                _watcher.Changed += (_, _) => RefreshAll();
            }
        }
        catch (Exception)
        {
            // Watching is a nice-to-have; provider still works on prayer transitions.
        }
    }

    public void CreateWidget(WidgetContext widgetContext)
    {
        Register(widgetContext);
        Update(widgetContext.Id);
    }

    public void Activate(WidgetContext widgetContext)
    {
        Register(widgetContext);
        Program.IncrementActiveWidgetCount();
        Update(widgetContext.Id);
    }

    public void Deactivate(string widgetId)
    {
        if (_widgets.TryRemove(widgetId, out var widget))
        {
            widget.Timer.Dispose();
            Program.DecrementActiveWidgetCount();
        }
    }

    public void DeleteWidget(string widgetId, string customState)
    {
        if (_widgets.TryRemove(widgetId, out var widget))
        {
            widget.Timer.Dispose();
        }
    }

    public void OnActionInvoked(WidgetActionInvokedArgs actionInvokedArgs)
    {
        // The "refresh" verb on the card triggers a re-read of the cache.
        Update(actionInvokedArgs.WidgetContext.Id);
    }

    public void OnWidgetContextChanged(WidgetContextChangedArgs contextChangedArgs)
    {
        var ctx = contextChangedArgs.WidgetContext;
        if (_widgets.TryGetValue(ctx.Id, out var widget))
        {
            widget.Timer.Dispose();
            _widgets[ctx.Id] = new ActiveWidget(ctx.Id, ctx.DefinitionId, ctx.Size, CreateTimer(ctx.Id));
        }
        Update(ctx.Id);
    }

    // ----------------------------------------------------------------------

    private void Register(WidgetContext ctx)
    {
        _widgets[ctx.Id] = new ActiveWidget(ctx.Id, ctx.DefinitionId, ctx.Size, CreateTimer(ctx.Id));
    }

    private Timer CreateTimer(string widgetId)
    {
        // Fires once for the soonest upcoming transition; reschedules itself.
        var timer = new Timer(_ => OnTransition(widgetId));
        ScheduleNext(timer);
        return timer;
    }

    private void ScheduleNext(Timer timer)
    {
        var cache = CacheReader.LoadCache();
        var settings = CacheReader.LoadSettings();
        if (cache == null)
        {
            // Cache not yet available; check again in 30s.
            timer.Change(TimeSpan.FromSeconds(30), Timeout.InfiniteTimeSpan);
            return;
        }
        var next = NextPrayer.PrayerNext(cache, settings, DateTime.Now);
        if (next == null)
        {
            timer.Change(TimeSpan.FromMinutes(5), Timeout.InfiniteTimeSpan);
            return;
        }
        var delay = next.Value.When - DateTime.Now;
        if (delay < TimeSpan.FromSeconds(1)) delay = TimeSpan.FromSeconds(1);
        timer.Change(delay, Timeout.InfiniteTimeSpan);
    }

    private void OnTransition(string widgetId)
    {
        Update(widgetId);
        if (_widgets.TryGetValue(widgetId, out var widget))
        {
            ScheduleNext(widget.Timer);
        }
    }

    private void RefreshAll()
    {
        foreach (var widgetId in _widgets.Keys)
        {
            Update(widgetId);
        }
    }

    private void Update(string widgetId)
    {
        if (!_widgets.TryGetValue(widgetId, out var widget)) return;

        var cache = CacheReader.LoadCache();
        var settings = CacheReader.LoadSettings();
        var template = LoadTemplate(widget.DefinitionId);
        var data = BuildCardData(cache, settings);

        var options = new WidgetUpdateRequestOptions(widgetId)
        {
            Template = template,
            Data = JsonSerializer.Serialize(data),
            CustomState = string.Empty,
        };

        WidgetManager.GetDefault().UpdateWidget(options);
    }

    private static string LoadTemplate(string definitionId)
    {
        var name = definitionId switch
        {
            "AlMunadi.Small" => "small.json",
            "AlMunadi.Medium" => "medium.json",
            "AlMunadi.Large" => "large.json",
            _ => "small.json",
        };
        var dir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
        var path = Path.Combine(dir, "Templates", name);
        return File.Exists(path) ? File.ReadAllText(path) : "{}";
    }

    private static object BuildCardData(CacheData? cache, AppSettings settings)
    {
        var lang = settings.Language;
        if (cache == null)
        {
            return new
            {
                hasData = false,
                noDataLabel = Translations.T("next_prayer", lang),
                mosqueName = "",
            };
        }
        var now = DateTime.Now;
        var prayers = NextPrayer.AdjustedTimes(cache, settings, now);
        var next = NextPrayer.PrayerNext(cache, settings, now);
        var rows = new List<object>();
        for (var i = 0; i < prayers.Count && i < NextPrayer.PrayerKeys.Length; i++)
        {
            rows.Add(new
            {
                name = Translations.T(NextPrayer.PrayerKeys[i], lang),
                time = prayers[i],
                iqama = NextPrayer.Iqama(cache, settings, i, now) ?? "",
                isNext = next?.Index == i,
            });
        }
        var nextLabel = next != null
            ? Translations.T(NextPrayer.PrayerKeys[next.Value.Index], lang)
            : Translations.T("next_prayer", lang);
        var nextTime = next != null && next.Value.Index < prayers.Count ? prayers[next.Value.Index] : "--:--";
        var countdown = next != null
            ? NextPrayer.FormatCountdown(next.Value.When - now, settings)
            : "";

        return new
        {
            hasData = true,
            mosqueName = cache.Name,
            nextPrayerName = nextLabel,
            nextPrayerTime = nextTime,
            countdown,
            shuruq = cache.Shuruq ?? "",
            shuruqLabel = Translations.T("Shuruq", lang),
            qibla = NextPrayer.QiblaArrow(cache.QiblaDirection),
            qiblaLabel = Translations.T("Qibla", lang),
            hijriDate = cache.HijriDate ?? "",
            prayers = rows,
        };
    }
}
