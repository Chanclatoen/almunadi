using System.Net;
using System.Text;
using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class UpdateCheckerTests : IDisposable
{
    private readonly string directory = Path.Combine(Path.GetTempPath(), "almunadi-update-tests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task PersistsCheckWindowAndCachedUpdateAcrossInstances()
    {
        var handler = new CountingHandler();
        var statePath = Path.Combine(directory, "update-check.json");
        var first = new UpdateChecker(new HttpClient(handler), statePath);

        var firstResult = await first.CheckAsync("1.0.9");
        var second = new UpdateChecker(new HttpClient(handler), statePath);
        var secondResult = await second.CheckAsync("1.0.9");

        Assert.Equal("1.0.10", firstResult?.Version);
        Assert.Equal("1.0.10", secondResult?.Version);
        Assert.Equal(1, handler.RequestCount);
    }

    public void Dispose()
    {
        if (Directory.Exists(directory))
        {
            Directory.Delete(directory, true);
        }
    }

    private sealed class CountingHandler : HttpMessageHandler
    {
        public int RequestCount { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            RequestCount++;
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("{\"tag_name\":\"v1.0.10\",\"html_url\":\"https://example.test/release\"}", Encoding.UTF8, "application/json"),
            });
        }
    }
}
