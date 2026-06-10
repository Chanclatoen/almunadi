using System.Windows;

namespace AlMunadi.App;

public partial class App : System.Windows.Application
{
    private TrayHost? trayHost;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        ThemeManager.ApplyCurrentTheme();
        WindowsNotificationService.Register();
        trayHost = new TrayHost();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        trayHost?.Dispose();
        WindowsNotificationService.Unregister();
        base.OnExit(e);
    }
}
