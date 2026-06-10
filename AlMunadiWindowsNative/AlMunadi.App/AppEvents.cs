namespace AlMunadi.App;

public static class AppEvents
{
    public static event Action? StateChanged;

    public static void NotifyStateChanged() => StateChanged?.Invoke();
}
