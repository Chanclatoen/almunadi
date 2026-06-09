# Al Munadi Mosque Search Worker

This Worker proxies the Mawaqit mosque search endpoint for the static GitHub Pages site.

## Deploy

```bash
cd worker
npx wrangler deploy
```

Set `ALLOWED_ORIGINS` in `wrangler.toml` or the Cloudflare dashboard to the exact GitHub Pages origin and any custom domain used by the site.

After deploy, set `site/config.js`:

```js
window.AL_MUNADI_CONFIG = {
    apiBase: 'https://api.almunadi.net',
    repoUrl: 'https://github.com/Chanclatoen/almunadi',
    releasesUrl: 'https://github.com/Chanclatoen/almunadi/releases',
};
```
