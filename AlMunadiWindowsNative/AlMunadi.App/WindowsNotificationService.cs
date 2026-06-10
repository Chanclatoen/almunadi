using Microsoft.Windows.AppNotifications;
using Microsoft.Windows.AppNotifications.Builder;

namespace AlMunadi.App;

public static class WindowsNotificationService
{
    private static bool registered;

    public static void Register()
    {
        if (registered)
        {
            return;
        }

        try
        {
            AppNotificationManager.Default.Register();
            registered = true;
        }
        catch (Exception)
        {
            registered = false;
        }
    }

    public static void Unregister()
    {
        if (!registered)
        {
            return;
        }

        AppNotificationManager.Default.Unregister();
        registered = false;
    }

    public static void Send(string title, string body, bool bypassDnd)
    {
        if (!registered)
        {
            return;
        }

        var builder = new AppNotificationBuilder()
            .AddText(title)
            .AddText(body);
        if (bypassDnd)
        {
            builder.SetScenario(AppNotificationScenario.Alarm)
                .AddButton(new AppNotificationButton("Al Munadi").AddArgument("action", "dismiss"));
        }

        AppNotificationManager.Default.Show(builder.BuildNotification());
    }
}
