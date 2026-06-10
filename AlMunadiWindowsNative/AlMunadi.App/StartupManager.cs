using System.IO;
using System.Reflection;
using Microsoft.Win32;

namespace AlMunadi.App;

public static class StartupManager
{
    private const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
    private const string ValueName = "AlMunadi";

    public static bool IsEnabled()
    {
        using var key = Registry.CurrentUser.OpenSubKey(RunKey);
        return key?.GetValue(ValueName) is string value && value.Length > 0;
    }

    public static void SetEnabled(bool enabled)
    {
        using var key = Registry.CurrentUser.CreateSubKey(RunKey);
        if (!enabled)
        {
            key.DeleteValue(ValueName, false);
            return;
        }

        var executable = Environment.ProcessPath ?? throw new InvalidOperationException("Application path is unavailable.");
        var command = Path.GetFileNameWithoutExtension(executable).Equals("dotnet", StringComparison.OrdinalIgnoreCase)
            ? $"\"{executable}\" \"{Assembly.GetEntryAssembly()?.Location}\""
            : $"\"{executable}\"";
        key.SetValue(ValueName, command);
    }
}
