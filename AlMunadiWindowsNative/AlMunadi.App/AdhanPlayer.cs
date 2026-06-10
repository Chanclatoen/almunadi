using System.IO;
using System.Windows.Media;

namespace AlMunadi.App;

public sealed class AdhanPlayer
{
    private readonly MediaPlayer player = new();

    public void Play(string path)
    {
        if (!File.Exists(path))
        {
            throw new FileNotFoundException("Adhan file not found.", path);
        }

        Stop();
        player.Open(new Uri(path, UriKind.Absolute));
        player.Play();
    }

    public void Stop()
    {
        player.Stop();
        player.Close();
    }
}
