using System.Text.Json;
using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class BehaviorFixtureTests
{
    private static readonly JsonDocument Fixtures = JsonDocument.Parse(
        File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "behavior-fixtures.json")));

    [Theory]
    [InlineData("compact")]
    [InlineData("full")]
    public void CountdownMatchesFixtures(string format)
    {
        foreach (var fixture in Cases("countdown", format))
        {
            Assert.Equal(
                fixture.GetProperty("expected").GetString(),
                BehaviorCore.FormatCountdown(fixture.GetProperty("remaining_minutes").GetInt32(), format));
        }
    }

    [Theory]
    [InlineData("compact")]
    [InlineData("full")]
    public void ElapsedMatchesFixtures(string format)
    {
        foreach (var fixture in Cases("elapsed_since", format))
        {
            Assert.Equal(
                fixture.GetProperty("expected").GetString(),
                BehaviorCore.FormatElapsed(fixture.GetProperty("elapsed_minutes").GetInt32(), format));
        }
    }

    [Fact]
    public void TrayTitleMatchesFixtures()
    {
        foreach (var fixture in Cases("tray_title"))
        {
            Assert.Equal(
                fixture.GetProperty("expected").GetString(),
                BehaviorCore.FormatTrayTitle(
                    fixture.GetProperty("mode").GetString()!,
                    fixture.GetProperty("name").GetString()!,
                    fixture.GetProperty("time").GetString()!,
                    fixture.GetProperty("countdown").GetString()!));
        }
    }

    [Fact]
    public void IqamaMatchesFixtures()
    {
        foreach (var fixture in Cases("iqama"))
        {
            var iqama = fixture.GetProperty("iqama");
            var expected = fixture.GetProperty("expected");
            Assert.Equal(
                expected.ValueKind == JsonValueKind.Null ? null : expected.GetString(),
                BehaviorCore.ResolveIqama(
                    fixture.GetProperty("prayer_time").GetString()!,
                    iqama.ValueKind == JsonValueKind.Null ? null : iqama.GetString()));
        }
    }

    [Fact]
    public void OffsetsMatchFixtures()
    {
        var apply = Fixtures.RootElement.GetProperty("prayer_offsets").GetProperty("apply");
        var times = apply.GetProperty("times").EnumerateArray().ToArray();
        var expected = apply.GetProperty("expected").EnumerateArray().ToArray();
        var offsets = apply.GetProperty("offsets");
        for (var index = 0; index < times.Length; index++)
        {
            var offset = offsets.TryGetProperty(BehaviorCore.PrayerNames[index], out var value) ? value.GetInt32() : 0;
            Assert.Equal(expected[index].GetString(), BehaviorCore.ApplyOffset(times[index].GetString()!, offset));
        }

        foreach (var fixture in Cases("prayer_offsets", "clamp"))
        {
            var input = fixture.GetProperty("input");
            object? value = input.ValueKind == JsonValueKind.Number ? input.GetInt32() : null;
            Assert.Equal(fixture.GetProperty("expected").GetInt32(), BehaviorCore.ClampOffset(value));
        }
    }

    [Fact]
    public void JumuahKeyMatchesFixtures()
    {
        foreach (var fixture in Cases("jumuah_notification_key"))
        {
            Assert.Equal(
                fixture.GetProperty("expected").GetString(),
                BehaviorCore.NotificationKey(
                    fixture.GetProperty("index").GetInt32(),
                    fixture.GetProperty("is_friday").GetBoolean(),
                    fixture.GetProperty("has_jumua").GetBoolean()));
        }
    }

    [Fact]
    public void VersionCompareMatchesFixtures()
    {
        foreach (var fixture in Cases("version_compare"))
        {
            Assert.Equal(
                fixture.GetProperty("is_newer").GetBoolean(),
                BehaviorCore.IsNewerVersion(
                    fixture.GetProperty("current").GetString()!,
                    fixture.GetProperty("latest").GetString()!));
        }
    }

    [Fact]
    public void SlugExtractionMatchesFixtures()
    {
        foreach (var fixture in Cases("slug_extraction"))
        {
            var expected = fixture.GetProperty("expected");
            Assert.Equal(
                expected.ValueKind == JsonValueKind.Null ? null : expected.GetString(),
                BehaviorCore.ExtractSlug(fixture.GetProperty("input").GetString()));
        }
    }

    private static IEnumerable<JsonElement> Cases(params string[] path)
    {
        var node = Fixtures.RootElement;
        foreach (var segment in path)
        {
            node = node.GetProperty(segment);
        }

        return node.EnumerateArray().ToArray();
    }
}
