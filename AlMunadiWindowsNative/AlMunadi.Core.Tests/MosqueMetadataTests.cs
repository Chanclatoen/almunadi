using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class MosqueMetadataTests
{
    [Fact]
    public void FormatsStableHijriDate()
    {
        Assert.Equal("25 Dhu al-Hijjah 1447 AH", MosqueMetadata.FormatHijriDate(new DateOnly(2026, 6, 10)));
    }

    [Fact]
    public void FormatsQiblaBearingAndHandlesMissingCoordinates()
    {
        Assert.Equal("125°", MosqueMetadata.FormatQiblaDirection(51.9244, 4.4777));
        Assert.Null(MosqueMetadata.FormatQiblaDirection(null, 4.4777));
    }
}
