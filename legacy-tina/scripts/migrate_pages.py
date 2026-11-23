#!/usr/bin/env python3
"""Migrate each Weebly HTML page into the Tina block schema.

For each page:
  public/<slug>.html -> src/templates/<slug>.html (with <!--CMS:*--> markers)
                     + src/content/tina-pages/<slug>.json (title, hero_image,
                       body_bg, blocks: [{_template: rawHtml, html: ...}])
                     + src/pages/<slug>.html.ts (Astro endpoint)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
TEMPLATES = ROOT / "src" / "templates"
CONTENT = ROOT / "src" / "content" / "tina-pages"
PAGES = ROOT / "src" / "pages"

# Slug -> (source .html filename in public/, display title)
PAGES_TO_MIGRATE = [
    ("once-upon-a-time", "once-upon-a-time.html", "Once upon a time"),
    ("positivity", "positivity.html", "Positivity"),
    ("earth-medicines", "earth-medicines.html", "Earth Medicines"),
    ("constructed-thoughts", "constructed-thoughts.html", "Constructed Thoughts"),
    ("journey-into-self", "journey-into-self.html", "Journey into Self"),
    ("the-lodge", "the-lodge.html", "The Lodge"),
    ("prices-and-bookings", "prices-and-bookings.html", "Prices and Bookings"),
    ("retreat-testimonials", "retreat-testimonials.html", "Retreat Testimonials"),
    ("past-retreats", "past-retreats.html", "Past Retreats"),
    ("peace-love-and-kambo", "peace-love-and-kambo.html", "Peace Love and Kambo"),
    ("kambo-practitioners", "kambo-practitioners.html", "Kambo Practitioners"),
    ("kambo-testimonials", "kambo-testimonials.html", "Kambo Testimonials"),
]

ENDPOINT_TEMPLATE = '''\
import type { APIRoute } from 'astro';
import template from '../templates/__SLUG__.html?raw';
import pageData from '../content/tina-pages/__SLUG__.json';

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
  }).join('\\n');
}

export const GET: APIRoute = async () => {
  const bodyHtml = renderBlocks((pageData as any).blocks || []);
  let html = template as string;
  html = html.replace(/<!--CMS:title-->[\\s\\S]*?<!--\\/CMS:title-->/, (pageData as any).title);
  if ((pageData as any).hero_image) {
    html = html.replace(/<!--CMS:hero_image-->[\\s\\S]*?<!--\\/CMS:hero_image-->/, (pageData as any).hero_image);
  }
  if ((pageData as any).body_bg) {
    html = html.replace(/<!--CMS:body_bg-->[\\s\\S]*?<!--\\/CMS:body_bg-->/, (pageData as any).body_bg);
  }
  html = html.replace(/<!--CMS:body_html-->[\\s\\S]*?<!--\\/CMS:body_html-->/, bodyHtml);
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
};
'''


def mark_template(html: str, title: str) -> tuple[str, dict]:
    """Insert CMS markers and return (new_html, metadata).
    Metadata contains extracted hero_image and body_bg.
    """
    metadata = {"hero_image": None, "body_bg": None}

    # STEP 1 (order matters): find the content region FIRST, before touching style attrs.
    m = re.search(r'<div[^>]*class="[^"]*wsite-body-section[^"]*"[^>]*>', html)
    if not m:
        raise RuntimeError("no wsite-body-section found")
    body_start = m.end()
    pos = body_start
    depth = 1
    while depth > 0 and pos < len(html):
        om = re.search(r'<div\b[^>]*>', html[pos:])
        cm = re.search(r'</div>', html[pos:])
        if not cm:
            break
        if om and om.start() < cm.start():
            depth += 1
            pos += om.end()
        else:
            depth -= 1
            pos += cm.end()
    body_end = pos - len('</div>')
    body_inner = html[body_start:body_end]

    # STEP 2: title in <title>
    title_m = re.search(r'<title>([^<]*)</title>', html)
    orig_title = title_m.group(1) if title_m else ""
    html = re.sub(
        r'(<title>)[^<]*(</title>)',
        lambda m: m.group(1) + '<!--CMS:title-->' + title + '<!--/CMS:title--> - LOVE AND DEVI' + m.group(2),
        html, count=1,
    )

    # STEP 3: hero image (inside wsite-header-section's style)
    hero_m = re.search(
        r'(wsite-header-section[^>]*style="[^"]*background-image:\s*url\(&quot;)([^&]+)(&quot;\))',
        html
    )
    if hero_m:
        metadata["hero_image"] = "/" + hero_m.group(2) if not hero_m.group(2).startswith('/') else hero_m.group(2)
        html = re.sub(
            r'(wsite-header-section[^>]*style="[^"]*background-image:\s*url\(&quot;)([^&]+)(&quot;\))',
            lambda m: m.group(1) + '<!--CMS:hero_image-->' + m.group(2) + '<!--/CMS:hero_image-->' + m.group(3),
            html, count=1,
        )

    # STEP 4: wrap body region (must recompute positions since title and hero edits shifted indexes)
    m = re.search(r'<div[^>]*class="[^"]*wsite-body-section[^"]*"[^>]*>', html)
    body_start = m.end()
    pos = body_start
    depth = 1
    while depth > 0 and pos < len(html):
        om = re.search(r'<div\b[^>]*>', html[pos:])
        cm = re.search(r'</div>', html[pos:])
        if not cm:
            break
        if om and om.start() < cm.start():
            depth += 1
            pos += om.end()
        else:
            depth -= 1
            pos += cm.end()
    body_end = pos - len('</div>')
    body_inner = html[body_start:body_end]
    html = (html[:body_start]
            + '<!--CMS:body_html-->' + body_inner + '<!--/CMS:body_html-->'
            + html[body_end:])

    # STEP 5: body background color (safe now, but still match before any marker it would overlap)
    bg_m = re.search(
        r'(wsite-body-section[^>]*style="[^"]*background-color:\s*)(#[0-9a-fA-F]+|[a-z]+)([;"])',
        html
    )
    if bg_m:
        metadata["body_bg"] = bg_m.group(2)
        html = re.sub(
            r'(wsite-body-section[^>]*style="[^"]*background-color:\s*)(#[0-9a-fA-F]+|[a-z]+)([;"])',
            lambda m: m.group(1) + '<!--CMS:body_bg-->' + m.group(2) + '<!--/CMS:body_bg-->' + m.group(3),
            html, count=1,
        )

    return html, metadata


def migrate_one(slug: str, source_file: str, title: str) -> None:
    src = PUBLIC / source_file
    if not src.exists():
        print(f"  SKIP {slug}: {source_file} not in public/")
        return
    html = src.read_text(encoding='utf-8')
    try:
        marked_html, metadata = mark_template(html, title)
    except Exception as e:
        print(f"  FAIL {slug}: {e}")
        return

    # Write template
    (TEMPLATES / f"{slug}.html").write_text(marked_html, encoding='utf-8')

    # Extract body_html for content file
    m = re.search(r'<!--CMS:body_html-->(.*?)<!--/CMS:body_html-->', marked_html, re.DOTALL)
    body_inner = m.group(1) if m else ""

    # Content JSON
    content = {
        "title": title,
        "blocks": [{"_template": "rawHtml", "html": body_inner}],
    }
    if metadata["hero_image"]:
        content["hero_image"] = metadata["hero_image"]
    if metadata["body_bg"]:
        content["body_bg"] = metadata["body_bg"]

    (CONTENT / f"{slug}.json").write_text(json.dumps(content, indent=2), encoding='utf-8')

    # Astro endpoint (use replace not .format — template uses JS curly braces)
    endpoint = ENDPOINT_TEMPLATE.replace('__SLUG__', slug)
    (PAGES / f"{slug}.html.ts").write_text(endpoint, encoding='utf-8')

    # Remove the original HTML from public/ so our Astro route takes over
    src.unlink()

    # Also delete the -1 duplicate if exists
    dup = PUBLIC / source_file.replace('.html', '-1.html')
    if dup.exists():
        dup.unlink()

    print(f"  ✓ {slug}: hero={metadata['hero_image'] is not None}, bg={metadata['body_bg']}")


def main():
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    CONTENT.mkdir(parents=True, exist_ok=True)
    PAGES.mkdir(parents=True, exist_ok=True)

    for slug, source, title in PAGES_TO_MIGRATE:
        migrate_one(slug, source, title)


if __name__ == "__main__":
    main()
