import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tina from '@tinacms/astro/integration';

export default defineConfig({
  site: 'https://loveanddevi.pages.dev',
  trailingSlash: 'ignore',
  // SSR-enabled: TinaCMS's visual editor + /admin dashboard need server routes.
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  integrations: [tina({ tinaDirectory: 'tina' })],
  // Our Weebly HTML output pages are explicitly marked `prerender = true`
  // so the build still emits static HTML files for Cloudflare Pages.
});
