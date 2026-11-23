import type { APIRoute } from 'astro';
import template from '../templates/constructed-thoughts.html?raw';
import pageData from '../content/tina-pages/constructed-thoughts.json';

export const prerender = true;

function renderBlocks(blocks: any[]): string {
  if (!blocks || !blocks.length) return '';
  return blocks.map((b: any) => {
    const t = b._template || b.__typename;
    switch (t) {
      case 'rawHtml':
      case 'PageBlocksRawHtml':
        return b.html || '';
      case 'paragraph':
      case 'PageBlocksParagraph':
        return `<div class="paragraph">${typeof b.body === 'string' ? b.body : ''}</div>`;
      case 'heading':
      case 'PageBlocksHeading': {
        const tag = b.level || 'h2';
        return `<${tag} class="wsite-headline">${b.text || ''}</${tag}>`;
      }
      case 'image':
      case 'PageBlocksImage': {
        const align = b.align || 'center';
        const s: Record<string, string> = {
          left: 'float:left;margin:10px 20px 10px 0;',
          right: 'float:right;margin:10px 0 10px 20px;',
          center: 'text-align:center;margin:20px auto;',
        };
        const cap = b.caption ? `<div style="font-size:90%;color:#666;margin-top:6px;">${b.caption}</div>` : '';
        return `<div class="wsite-image wsite-image-border-none" style="padding:10px 0;${s[align]}"><img src="${b.src || ''}" alt="${b.alt || ''}" style="max-width:100%;height:auto;"/>${cap}</div>`;
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
  const bodyHtml = renderBlocks((pageData as any).blocks || []);
  let html = template as string;
  html = html.replace(/<!--CMS:title-->[\s\S]*?<!--\/CMS:title-->/, (pageData as any).title);
  if ((pageData as any).hero_image) {
    html = html.replace(/<!--CMS:hero_image-->[\s\S]*?<!--\/CMS:hero_image-->/, (pageData as any).hero_image);
  }
  if ((pageData as any).body_bg) {
    html = html.replace(/<!--CMS:body_bg-->[\s\S]*?<!--\/CMS:body_bg-->/, (pageData as any).body_bg);
  }
  html = html.replace(/<!--CMS:body_html-->[\s\S]*?<!--\/CMS:body_html-->/, bodyHtml);
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
};
