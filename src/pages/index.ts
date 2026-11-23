import type { APIRoute } from 'astro';
import template from '../templates/index.html?raw';
import pageData from '../content/tina-pages/index.json';

export const prerender = true;

function renderBlocks(blocks: any[]): string {
  if (!blocks || !blocks.length) return '';
  return blocks.map((b: any) => {
    const t = b._template || b.__typename;
    if (t === 'rawHtml' || t === 'PageBlocksRawHtml') return b.html || '';
    return '';
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
