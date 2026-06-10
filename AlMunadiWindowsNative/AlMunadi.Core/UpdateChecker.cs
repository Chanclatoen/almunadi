using System.Net.Http.Headers;
using System.Text.Json;

namespace AlMunadi.Core;

public sealed class UpdateChecker
{
    private readonly HttpClient httpClient;
    private readonly string? statePath;
    private UpdateCheckState state;

    public UpdateChecker(HttpClient? httpClient = null, string? statePath = null)
    {
        this.httpClient = httpClient ?? new HttpClient();
        this.statePath = statePath;
        state = LoadState(statePath);
        this.httpClient.Timeout = TimeSpan.FromSeconds(10);
        this.httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));
        this.httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("AlMunadi/1.0");
    }

    public async Task<UpdateInfo?> CheckAsync(string currentVersion, CancellationToken cancellationToken = default)
    {
        if (state.LastCheckedAt is not null && DateTimeOffset.UtcNow - state.LastCheckedAt < TimeSpan.FromHours(24))
        {
            return state.Version is not null && BehaviorCore.IsNewerVersion(currentVersion, state.Version)
                ? new UpdateInfo(state.Version, state.Url ?? string.Empty)
                : null;
        }

        state = state with { LastCheckedAt = DateTimeOffset.UtcNow };
        try
        {
            using var response = await httpClient.GetAsync(
                "https://api.github.com/repos/Chanclatoen/almunadi/releases/latest",
                cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
            using var document = JsonDocument.Parse(await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false));
            var tag = document.RootElement.GetProperty("tag_name").GetString()?.TrimStart('v') ?? string.Empty;
            var url = document.RootElement.GetProperty("html_url").GetString() ?? string.Empty;
            state = state with { Version = tag, Url = url };
            SaveState();
            return BehaviorCore.IsNewerVersion(currentVersion, tag) ? new UpdateInfo(tag, url) : null;
        }
        catch (Exception exception) when (exception is HttpRequestException or JsonException or TaskCanceledException)
        {
            SaveState();
            return null;
        }
    }

    private static UpdateCheckState LoadState(string? path)
    {
        try
        {
            return path is not null && File.Exists(path)
                ? JsonSerializer.Deserialize<UpdateCheckState>(File.ReadAllText(path)) ?? new UpdateCheckState()
                : new UpdateCheckState();
        }
        catch (Exception exception) when (exception is IOException or JsonException)
        {
            return new UpdateCheckState();
        }
    }

    private void SaveState()
    {
        if (statePath is null)
        {
            return;
        }

        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(statePath)!);
            File.WriteAllText(statePath, JsonSerializer.Serialize(state));
        }
        catch (IOException)
        {
            // Update checks are best effort and never affect app startup.
        }
    }

    private sealed record UpdateCheckState(
        DateTimeOffset? LastCheckedAt = null,
        string? Version = null,
        string? Url = null);
}

public sealed record UpdateInfo(string Version, string Url);
