# Al Munadi Website

This is the static project website and mosque finder. It deploys to Cloudflare Pages (almunadi.net) through `.github/workflows/site-deploy.yml`, with GitHub Pages as a mirror.

## Local preview

```bash
cd site
python3 -m http.server 8000
```

Open `http://localhost:8000`.

## Search API

The site calls `GET /api/search?q=<query>` through the API origin configured in `config.js`.

- Leave `apiBase` empty when the Cloudflare Worker is mounted under the same domain.
- Set `apiBase` to the Worker origin when using the default `workers.dev` URL.

The direct Mawaqit search endpoint does not expose browser CORS headers, so the static site needs the Worker for live search.
