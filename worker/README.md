# Next Prayer Mosque Search Worker

This Worker proxies the Mawaqit mosque search endpoint for the static GitHub Pages site.

## Deploy

```bash
cd worker
npx wrangler deploy
```

Set `ALLOWED_ORIGINS` in `wrangler.toml` or the Cloudflare dashboard to the exact GitHub Pages origin and any custom domain used by the site.

After deploy, set `site/config.js`:

```js
window.NEXT_PRAYER_CONFIG = {
    apiBase: 'https://next-prayer-mawaqit-search.your-subdomain.workers.dev',
    repoUrl: 'https://github.com/Chanclatoen/next-prayer-mawaqit',
    releasesUrl: 'https://github.com/Chanclatoen/next-prayer-mawaqit/releases',
};
```
