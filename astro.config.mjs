import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';
import tina from '@tinacms/astro/integration';

export default defineConfig({
  site: 'https://loveanddevi.pages.dev',
  trailingSlash: 'ignore',
  // SSR-enabled: TinaCMS's visual editor + /admin dashboard need server routes.
  // Our Weebly HTML pages (e.g. retreats.html) are explicitly prerendered to
  // static files via `export const prerender = true` so most of the site is
  // still served as static HTML.
  output: 'server',
  adapter: cloudflare({
    platformProxy: { enabled: true },
  }),
  integrations: [tina({ tinaDirectory: 'tina' })],
});
