import { defineConfig } from 'astro/config';
import tina from '@tinacms/astro/integration';

export default defineConfig({
  site: 'https://loveanddevi.pages.dev',
  trailingSlash: 'ignore',
  // Static output — no SSR, no adapter. TinaCMS admin UI is static HTML +
  // client-side JS that talks to TinaCloud directly from the browser.
  // Weebly HTML pages (retreats.html etc.) are prerendered to static files
  // and served as-is by Cloudflare Pages.
  output: 'static',
  integrations: [tina({ tinaDirectory: 'tina' })],
});
