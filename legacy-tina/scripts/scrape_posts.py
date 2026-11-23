#!/usr/bin/env python3
"""Re-extract blog posts + poems from the git-tracked HTML files on main.

Downloads every referenced image from the live site into public/images/,
rewrites internal links to new URL scheme, produces clean markdown.
"""
import re
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as to_md

BASE = "https://loveanddevi.pages.dev"
ROOT = Path(__file__).resolve().parent.parent
PUBLIC_IMAGES = ROOT / "public" / "images"
CONTENT = ROOT / "src" / "content"
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    except Exception as e:
        print(f"    fetch fail {url}: {e}")
        return None


def download(src):
    """Download src to public/images/, return rewritten path like /images/foo.jpg."""
    # Normalize weird escaped urls
    src = src.replace('&quot;', '').replace('&amp;', '&').strip('"\' ')
    if not src or src.startswith('data:'):
        return None
    # strip query string
    src = re.sub(r'\?.*$', '', src)
    # If protocol-relative
    if src.startswith('//'):
        src = 'https:' + src
    # If relative
    if not src.startswith('http'):
        full = urljoin(BASE + '/', src.lstrip('./'))
    else:
        full = src
    name = Path(urlparse(full).path).name
    if not name: return None
    dest = PUBLIC_IMAGES / name
    if not dest.exists():
        data = fetch(full)
        if data:
            dest.write_bytes(data)
    if dest.exists():
        return f"/images/{name}"
    return None


def rewrite_link(href):
    href = href.strip()
    if 'cdn-cgi/l/email-protection' in href:
        return None  # signal: replace link markup with plain text
    if href.startswith(('mailto:', 'tel:', '#', 'javascript:', 'http')):
        return href
    if re.match(r'(?:\.\./)?blog-entries/', href):
        m = re.search(r'blog-entries/([^/?#]+)\.html', href)
        if m: return f"/blog/{m.group(1)}/"
    if re.match(r'(?:\.\./)?poems/', href):
        m = re.search(r'poems/([^/?#]+)\.html', href)
        if m: return f"/poems/{m.group(1)}/"
    m = re.match(r'^(?:\.\./)?([a-z0-9-]+?)(?:-1)?\.html$', href)
    if m: return f"/{m.group(1)}/"
    if href == 'index.htm' or href == 'index.html' or href == '../index.html':
        return "/"
    return href


def process_content(node):
    """Download referenced images; rewrite img src and a href in-place."""
    for img in node.find_all('img'):
        src = img.get('src') or ''
        new = download(src)
        if new:
            img['src'] = new
    for a in node.find_all('a'):
        href = a.get('href') or ''
        if not href: continue
        new = rewrite_link(href)
        if new is None:
            a.replace_with('[email protected]')
        else:
            a['href'] = new


def clean_main_html(main, kill_classes=None):
    kill_classes = kill_classes or [
        'blog-social', 'blog-comments-bottom', 'blog-comment-area',
        'blog-post-separator', 'blog-feed-link', 'blog-sidebar',
        'wsite-footer', 'wsite-header', 'wsite-menu', 'wsite-nav',
    ]
    for cls in kill_classes:
        for el in main.find_all(class_=lambda c: c and any(cls in cc for cc in (c if isinstance(c, list) else c.split()))):
            el.decompose()
    for tag in main.find_all(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()


def to_markdown(node):
    md = to_md(str(node), heading_style='ATX', bullets='-', strip=['script', 'style', 'noscript', 'iframe'])
    md = re.sub(r'[ \t]+\n', '\n', md)
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = md.replace('\xa0', ' ').replace('​', '')
    return md.strip() + '\n'


def extract_date(soup):
    el = soup.select_one('.blog-date')
    if not el: return None
    txt = el.get_text(' ', strip=True)
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', txt)
    if not m: return None
    mo, d, y = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def extract_title(soup, fallback):
    for sel in ['.blog-title-link', '.blog-title', '.blog-header h2 a', '.blog-header h2']:
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(' ', strip=True)
            if txt: return txt
    # fallback to <title>
    t = soup.find('title')
    if t:
        txt = t.get_text(strip=True)
        for sep in [' - LOVE AND DEVI', 'LOVE AND DEVI - ']:
            txt = txt.replace(sep, '').strip()
        if txt: return txt
    return fallback


def git_ls(dir_path):
    out = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'main'], text=True)
    return [p for p in out.splitlines() if p.startswith(dir_path + '/') and p.endswith('.html')
            and '/archives/' not in p and '/category/' not in p]


def process(kind, html_path):
    name = Path(html_path).name
    slug = name.replace('.html', '')
    print(f"  {kind}: {name}")
    html = subprocess.check_output(['git', 'show', f'main:{html_path}'], text=True, errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.select_one('.blog-content')
    if not body:
        print(f"    no .blog-content; skipping")
        return
    title = extract_title(soup, slug.replace('-', ' ').title())
    date = extract_date(soup)
    clean_main_html(body)
    process_content(body)
    first_img = body.find('img')
    cover = first_img.get('src') if first_img else None
    md = to_markdown(body)

    dest = CONTENT / kind / f"{slug}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    fm = ['---', f'title: "{title.replace(chr(34), chr(39))}"']
    if date: fm.append(f"date: {date}")
    if cover: fm.append(f'image: "{cover}"')
    fm.append('draft: false')
    fm.append('---')
    fm.append('')
    dest.write_text('\n'.join(fm) + md, encoding='utf-8')


def main():
    PUBLIC_IMAGES.mkdir(parents=True, exist_ok=True)
    poems = git_ls('poems')
    blogs = git_ls('blog-entries')
    print(f"poems: {len(poems)}, blog: {len(blogs)}")
    for p in poems:
        process('poems', p)
    for p in blogs:
        process('blog', p)


if __name__ == '__main__':
    main()
