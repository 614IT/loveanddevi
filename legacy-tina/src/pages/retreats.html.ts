import type { APIRoute } from 'astro';
import template from '../templates/retreats.html?raw';
import retreatsData from '../content/tina-pages/retreats.json';

export const prerender = true;

// Render the TinaCMS block list into HTML by instantiating Astro components
// isn't straightforward from an API route. For the prerender output we
// pre-render by looping through blocks and emitting HTML strings directly.
// (The visual-editor live view uses the Astro page components via TinaIsland.)

function renderBlocks(blocks: any[]): string {
  if (!blocks || !blocks.length) return '';
  return blocks.map((b) => {
    const t = b._template || b.__typename;
    switch (t) {
      case 'rawHtml':
      case 'PageBlocksRawHtml':
        return b.html || '';
      case 'paragraph':
      case 'PageBlocksParagraph': {
        // Render rich-text content - for now expect HTML string
        const body = typeof b.body === 'string' ? b.body : '';
        return `<div class="paragraph">${body}</div>`;
      }
      case 'heading':
      case 'PageBlocksHeading': {
        const tag = b.level || 'h2';
        return `<${tag} class="wsite-headline">${b.text || ''}</${tag}>`;
      }
      case 'image':
      case 'PageBlocksImage': {
        const align = b.align || 'center';
        const styles: Record<string, string> = {
          left: 'float:left;margin:10px 20px 10px 0;',
          right: 'float:right;margin:10px 0 10px 20px;',
          center: 'text-align:center;margin:20px auto;',
        };
        const caption = b.caption
          ? `<div style="font-size:90%;color:#666;margin-top:6px;">${b.caption}</div>`
          : '';
        return `<div class="wsite-image wsite-image-border-none" style="padding:10px 0;${styles[align]}">
          <img src="${b.src || ''}" alt="${b.alt || ''}" style="max-width:100%;height:auto;" />
          ${caption}
        </div>`;
      }
      case 'bulletList':
      case 'PageBlocksBulletList': {
        const items = (b.items || []).map((i: string) => `<li>${i}</li>`).join('');
        return `<div class="paragraph"><ul>${items}</ul></div>`;
      }
      case 'divider':
      case 'PageBlocksDivider': {
        if (b.style === 'line') return '<hr style="border:0;border-top:1px solid #ddd;margin:2em auto;max-width:200px;">';
        const h = b.style === 'large' ? 60 : 20;
        return `<div class="wsite-spacer" style="height:${h}px;"></div>`;
      }
      default:
        return '';
    }
  }).join('\n');
}

export const GET: APIRoute = async () => {
  const bodyHtml = renderBlocks(retreatsData.blocks || []);
  let html = template as string;
  html = html.replace(/<!--CMS:title-->[\s\S]*?<!--\/CMS:title-->/, retreatsData.title);
  html = html.replace(/<!--CMS:hero_image-->[\s\S]*?<!--\/CMS:hero_image-->/, retreatsData.hero_image);
  html = html.replace(/<!--CMS:body_bg-->[\s\S]*?<!--\/CMS:body_bg-->/, retreatsData.body_bg);
  html = html.replace(/<!--CMS:body_html-->[\s\S]*?<!--\/CMS:body_html-->/, bodyHtml);

  return new Response(html, {
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
};
