using System.Net;
using System.Text;
using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class MawaqitClientTests
{
    private const string MosqueJson = """
        [{"name":"Example Mosque","times":["05:00","06:30","13:30","17:00","21:00","22:30"],"iqamaEnabled":true,"iqama":["+15",null,null,null,null]}]
        """;

    [Fact]
    public async Task FetchUsesStructuredApiFirst()
    {
        var handler = new StubHandler((request, _) =>
        {
            Assert.Contains("word=example-mosque", request.RequestUri!.Query);
            return Json(MosqueJson);
        });
        var client = new MawaqitClient(new HttpClient(handler));

        var result = await client.FetchAsync("https://mawaqit.net/en/w/example-mosque");

        Assert.Equal("Example Mosque", result.Name);
        Assert.Equal(["05:00", "13:30", "17:00", "21:00", "22:30"], result.Times);
        Assert.Equal("06:30", result.Shuruq);
        Assert.Single(handler.Requests);
    }

    [Fact]
    public async Task FetchFallsBackToHtmlConfData()
    {
        var handler = new StubHandler((request, _) =>
            request.RequestUri!.AbsolutePath.StartsWith("/api/", StringComparison.Ordinal)
                ? new HttpResponseMessage(HttpStatusCode.ServiceUnavailable)
                : new HttpResponseMessage(HttpStatusCode.OK)
                {
                    Content = new StringContent($"<script>confData = {MosqueJson[1..^1]};</script>", Encoding.UTF8, "text/html"),
                });
        var client = new MawaqitClient(new HttpClient(handler));

        var result = await client.FetchAsync("https://mawaqit.net/en/example-mosque");

        Assert.Equal("Example Mosque", result.Name);
        Assert.Equal("/en/w/example-mosque", handler.Requests[1].AbsolutePath);
    }

    [Fact]
    public async Task SearchUrlEncodesQuery()
    {
        var handler = new StubHandler((request, _) => Json("[]"));
        var client = new MawaqitClient(new HttpClient(handler));

        await client.SearchAsync("Utrecht centrum");

        Assert.Contains("word=Utrecht%20centrum", handler.Requests.Single().Query);
    }

    private static HttpResponseMessage Json(string json) => new(HttpStatusCode.OK)
    {
        Content = new StringContent(json, Encoding.UTF8, "application/json"),
    };

    private sealed class StubHandler(Func<HttpRequestMessage, CancellationToken, HttpResponseMessage> responder) : HttpMessageHandler
    {
        public List<Uri> Requests { get; } = [];

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            Requests.Add(request.RequestUri!);
            return Task.FromResult(responder(request, cancellationToken));
        }
    }
}
