import type { APIRoute } from 'astro';
import { getEntry } from 'astro:content';
import template from '../templates/retreats.html?raw';

export const prerender = true;

export const GET: APIRoute = async () => {
  const entry = await getEntry('pages', 'retreats');
  if (!entry) throw new Error('retreats content entry missing');

  const body = entry.body ?? '';
  let html = template as string;
  html = html.replace(/<!--CMS:title-->[\s\S]*?<!--\/CMS:title-->/, entry.data.title);
  html = html.replace(/<!--CMS:hero_image-->[\s\S]*?<!--\/CMS:hero_image-->/, entry.data.hero_image);
  html = html.replace(/<!--CMS:body_bg-->[\s\S]*?<!--\/CMS:body_bg-->/, entry.data.body_bg);
  html = html.replace(/<!--CMS:body_html-->[\s\S]*?<!--\/CMS:body_html-->/, body);

  return new Response(html, {
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
};
