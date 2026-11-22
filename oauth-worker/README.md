# OAuth Worker for loveanddevi CMS

Tiny Cloudflare Worker that lets Sveltia CMS log users into GitHub without
exposing the OAuth client secret in the browser.

## One-time setup

Done once by you (the operator) — not by the customer.

### 1. Create a GitHub OAuth App

1. Go to https://github.com/settings/developers → **OAuth Apps** → **New OAuth App**
2. Application name: `Love and Devi CMS`
3. Homepage URL: `https://loveanddevi.pages.dev`
4. Authorization callback URL: `https://loveanddevi-auth.gnosisux.workers.dev/oauth/callback`
   (adjust the subdomain to match your Workers account)
5. Register, then note the **Client ID** and generate a **Client Secret**.

### 2. Deploy the Worker

```bash
cd oauth-worker
npx wrangler login              # first time only
npx wrangler secret put GITHUB_CLIENT_ID
npx wrangler secret put GITHUB_CLIENT_SECRET
npx wrangler deploy
```

Wrangler prints the deployed URL — confirm it matches `base_url` in
`../public/admin/config.yml`. If different, update both the config
and the GitHub OAuth app's callback URL.

### 3. Grant the customer access

She needs to:
1. Create a free GitHub account.
2. Send you her GitHub username.
3. You add her as a collaborator on `614IT/loveanddevi` (Settings → Collaborators → Write).

Then she can log in at `https://loveanddevi.pages.dev/admin/` and edit content.
