using System.Windows.Media;
using Microsoft.Win32;

namespace AlMunadi.App;

public static class ThemeManager
{
    public static void ApplyCurrentTheme()
    {
        using var key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize");
        var light = key?.GetValue("AppsUseLightTheme") as int? != 0;
        var colors = light
            ? new Dictionary<string, string>
            {
                ["BackgroundBrush"] = "#F8F6F0", ["CardBrush"] = "#FFFFFF", ["AccentBrush"] = "#0F5D47",
                ["TextPrimaryBrush"] = "#1C241F", ["TextSecondaryBrush"] = "#58635C", ["TextDimBrush"] = "#7C857F",
                ["SaffronBrush"] = "#9A6A17", ["DividerBrush"] = "#DDD8CB",
            }
            : new Dictionary<string, string>
            {
                ["BackgroundBrush"] = "#14130F", ["CardBrush"] = "#1F1D17", ["AccentBrush"] = "#46C79E",
                ["TextPrimaryBrush"] = "#F1EDE2", ["TextSecondaryBrush"] = "#AAB0A3", ["TextDimBrush"] = "#6E7466",
                ["SaffronBrush"] = "#E3B15A", ["DividerBrush"] = "#2D2B23",
            };

        foreach (var (resourceName, value) in colors)
        {
            System.Windows.Application.Current.Resources[resourceName] = new SolidColorBrush(
                (System.Windows.Media.Color)System.Windows.Media.ColorConverter.ConvertFromString(value));
        }
    }
}
