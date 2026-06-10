using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace AlMunadi.Core;

public sealed partial class MawaqitClient
{
    private const string ApiBase = "https://mawaqit.net/api/2.0/mosque/search";
    private readonly HttpClient httpClient;

    public MawaqitClient(HttpClient? httpClient = null)
    {
        this.httpClient = httpClient ?? new HttpClient();
        this.httpClient.Timeout = TimeSpan.FromSeconds(15);
        this.httpClient.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        this.httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("AlMunadi/1.0");
    }

    public async Task<PrayerCache> FetchAsync(string mosqueUrl, CancellationToken cancellationToken = default)
    {
        var slug = BehaviorCore.ExtractSlug(mosqueUrl);
        if (slug is not null)
        {
            try
            {
                return await FetchFromApiAsync(slug, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception exception) when (exception is HttpRequestException or JsonException or InvalidDataException)
            {
                // The public page remains the compatibility fallback when the API changes or fails.
            }
        }

        return await FetchFromHtmlAsync(mosqueUrl, cancellationToken).ConfigureAwait(false);
    }

    public async Task<PrayerCache> FetchAndCacheAsync(
        string mosqueUrl,
        AppDataStore store,
        CancellationToken cancellationToken = default)
    {
        var cache = await FetchAsync(mosqueUrl, cancellationToken).ConfigureAwait(false);
        store.SaveCache(cache);
        return cache;
    }

    public async Task<IReadOnlyList<MosqueSearchResult>> SearchAsync(
        string query,
        CancellationToken cancellationToken = default)
    {
        using var response = await httpClient.GetAsync(
            $"{ApiBase}?word={Uri.EscapeDataString(query)}",
            cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false));
        return document.RootElement.EnumerateArray().Select(item => new MosqueSearchResult(
            Text(item, "name"),
            Text(item, "slug"),
            Text(item, "localisation"))).ToList();
    }

    private async Task<PrayerCache> FetchFromApiAsync(string slug, CancellationToken cancellationToken)
    {
        using var response = await httpClient.GetAsync(
            $"{ApiBase}?word={Uri.EscapeDataString(slug)}",
            cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        using var document = JsonDocument.Parse(await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false));
        var mosque = document.RootElement.EnumerateArray().FirstOrDefault();
        if (mosque.ValueKind != JsonValueKind.Object)
        {
            throw new InvalidDataException("No mosque found via API.");
        }

        return ParseMosque(mosque);
    }

    private async Task<PrayerCache> FetchFromHtmlAsync(string mosqueUrl, CancellationToken cancellationToken)
    {
        var slug = BehaviorCore.ExtractSlug(mosqueUrl);
        var fetchUrl = !mosqueUrl.Contains("/w/", StringComparison.OrdinalIgnoreCase) && slug is not null
            ? $"https://mawaqit.net/en/w/{Uri.EscapeDataString(slug)}"
            : mosqueUrl;
        using var response = await httpClient.GetAsync(fetchUrl, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        var html = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        var match = ConfDataRegex().Match(html);
        if (!match.Success)
        {
            throw new InvalidDataException("Mawaqit page did not contain prayer data.");
        }

        using var document = JsonDocument.Parse(match.Groups[1].Value);
        return ParseMosque(document.RootElement);
    }

    private static PrayerCache ParseMosque(JsonElement mosque)
    {
        var apiTimes = mosque.GetProperty("times").EnumerateArray()
            .Select(value => value.GetString() ?? string.Empty)
            .ToList();
        if (apiTimes.Count < 6)
        {
            throw new InvalidDataException("Unexpected Mawaqit prayer time format.");
        }

        return new PrayerCache
        {
            Times = [apiTimes[0], apiTimes[2], apiTimes[3], apiTimes[4], apiTimes[5]],
            Shuruq = apiTimes[1],
            Name = Text(mosque, "name", Text(mosque, "label")),
            Iqama = StringArray(mosque, "iqama"),
            IqamaEnabled = Boolean(mosque, "iqamaEnabled"),
            Jumua = NullableText(mosque, "jumua"),
            Jumua2 = NullableText(mosque, "jumua2"),
            HijriDate = MosqueMetadata.FormatHijriDate(
                DateOnly.FromDateTime(DateTime.Today),
                Integer(mosque, "hijriAdjustment")),
            QiblaDirection = MosqueMetadata.FormatQiblaDirection(
                Number(mosque, "latitude"),
                Number(mosque, "longitude")),
            Date = DateTime.Today.ToString("yyyy-MM-dd"),
        };
    }

    private static string Text(JsonElement element, string property, string fallback = "") =>
        element.TryGetProperty(property, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString() ?? fallback
            : fallback;

    private static string? NullableText(JsonElement element, string property)
    {
        var text = Text(element, property);
        return text.Length == 0 ? null : text;
    }

    private static bool Boolean(JsonElement element, string property) =>
        element.TryGetProperty(property, out var value) && value.ValueKind == JsonValueKind.True;

    private static int Integer(JsonElement element, string property) =>
        element.TryGetProperty(property, out var value) && value.TryGetInt32(out var number) ? number : 0;

    private static double? Number(JsonElement element, string property)
    {
        if (!element.TryGetProperty(property, out var value))
        {
            return null;
        }

        if (value.ValueKind == JsonValueKind.Number && value.TryGetDouble(out var number))
        {
            return number;
        }

        return value.ValueKind == JsonValueKind.String
            && double.TryParse(value.GetString(), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out number)
            ? number
            : null;
    }

    private static List<string?>? StringArray(JsonElement element, string property) =>
        element.TryGetProperty(property, out var value) && value.ValueKind == JsonValueKind.Array
            ? value.EnumerateArray().Select(item => item.ValueKind == JsonValueKind.Null ? null : item.ToString()).ToList()
            : null;

    [GeneratedRegex(@"confData\s*=\s*(\{.*?\});", RegexOptions.Singleline)]
    private static partial Regex ConfDataRegex();
}

public sealed record MosqueSearchResult(string Name, string Slug, string Localisation)
{
    public string DisplayName => string.IsNullOrWhiteSpace(Localisation) ? Name : $"{Name} - {Localisation}";
}
