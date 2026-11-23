#!/usr/bin/env python3
"""Extract content from Weebly HTML export into Astro markdown collections."""
import html as htmllib
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as to_md

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_IMAGES = ROOT / "public" / "images"
CONTENT = ROOT / "src" / "content"

PAGE_FILES = {
    # filename -> (title_override, slug_override, hero_image_hint, show_in_nav, nav_order)
    "index.html": ("Love", "home", None, False, None),
    "retreats.html": ("Retreats", "retreats", None, True, 10),
    "the-lodge.html": ("The Lodge", "the-lodge", None, True, 20),
    "prices-and-bookings.html": ("Prices & Bookings", "prices-and-bookings", None, True, 30),
    "retreat-testimonials.html": ("Retreat Testimonials", "retreat-testimonials", None, False, None),
    "past-retreats.html": ("Past Retreats", "past-retreats", None, False, None),
    "peace-love-and-kambo.html": ("Peace, Love, and Kambo", "peace-love-and-kambo", None, True, 40),
    "kambo-practitioners.html": ("Kambo Practitioners", "kambo-practitioners", None, False, None),
    "kambo-testimonials.html": ("Kambo Testimonials", "kambo-testimonials", None, False, None),
    "positivity.html": ("Positivity", "positivity", None, False, None),
    "earth-medicines.html": ("Earth Medicines", "earth-medicines", None, False, None),
    "once-upon-a-time.html": ("Once Upon a Time", "once-upon-a-time", None, True, 5),
    "constructed-thoughts.html": ("Constructed Thoughts", "constructed-thoughts", None, False, None),
    "journey-into-self.html": ("Journey into Self", "journey-into-self", None, False, None),
}


def copy_uploads():
    """Flatten uploaded images into public/images/."""
    PUBLIC_IMAGES.mkdir(parents=True, exist_ok=True)
    src_dir = ROOT / "uploads" / "1" / "1" / "2" / "9" / "112908841"
    count = 0
    for f in src_dir.glob("*"):
        if f.is_file():
            dest = PUBLIC_IMAGES / f.name
            if not dest.exists():
                shutil.copy2(f, dest)
                count += 1
    print(f"Copied {count} uploaded images to public/images/")


def clean_html_text(s: str) -> str:
    s = htmllib.unescape(s)
    # Weebly inserts &nbsp; and zero-width chars everywhere
    s = s.replace("\xa0", " ").replace("​", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def rewrite_img_paths(html: str) -> str:
    # ../uploads/1/1/2/9/112908841/foo.jpg?250 -> /images/foo.jpg
    html = re.sub(
        r'(?:\.\./)*uploads/(?:[^/"\'\s)]+/)+([^/"\'\s)?]+)(?:\?[^"\'\s)]*)?',
        r'/images/\1',
        html,
    )
    # Broken Cloudflare email-protection links: replace link markup with plain text
    html = re.sub(
        r'<a[^>]*href="[^"]*cdn-cgi/l/email-protection[^"]*"[^>]*>.*?</a>',
        '[email protected]',
        html,
        flags=re.DOTALL,
    )
    return html


def extract_blog_content(soup: BeautifulSoup) -> str:
    node = soup.find("div", class_="blog-content")
    if not node:
        return ""
    # Strip social, comments, reply widgets
    for sel in ["blog-social", "blog-comments-bottom", "blog-comment-area", "blog-post-separator"]:
        for el in node.find_all(attrs={"class": lambda c: c and sel in (c if isinstance(c, list) else c.split())}):
            el.decompose()
    return str(node)


def extract_page_content(soup: BeautifulSoup) -> str:
    """Extract everything inside #wsite-content (or first wsite-section-wrap) up to the footer."""
    region = soup.find(id="wsite-content") or soup.find("div", class_="wsite-section-wrap")
    if not region:
        return ""
    # Walk the region but drop nav/footer/headers that may be inside
    for sel in ["wsite-footer", "wsite-header", "wsite-nav", "wsite-menu"]:
        for el in region.find_all(attrs={"class": lambda c: c and any(sel in cc for cc in (c if isinstance(c, list) else c.split()))}):
            el.decompose()
    return str(region)


def extract_title(soup: BeautifulSoup, fallback: str) -> str:
    t = soup.find("title")
    if t:
        txt = t.get_text(strip=True)
        # "Title - LOVE AND DEVI" or "LOVE AND DEVI - Title"
        for sep in [" - LOVE AND DEVI", "LOVE AND DEVI - "]:
            txt = txt.replace(sep, "").strip()
        if txt:
            return txt
    return fallback


def extract_date(soup: BeautifulSoup) -> str | None:
    node = soup.find("div", class_="blog-date") or soup.find(class_="blog-date")
    if node:
        txt = node.get_text(strip=True)
        # Format: "12/17/2017"
        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", txt)
        if m:
            mo, d, y = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


def extract_first_image(html_snippet: str) -> str | None:
    m = re.search(r'<img[^>]+src="([^"]+)"', html_snippet)
    if not m:
        return None
    src = m.group(1)
    src = re.sub(
        r'(?:\.\./)*uploads/(?:[^/"\'\s)]+/)+([^/"\'\s)?]+)(?:\?[^"\'\s)]*)?',
        r'/images/\1',
        src,
    )
    return src if src.startswith("/images/") else None


def html_to_md(html: str) -> str:
    html = rewrite_img_paths(html)
    md = to_md(html, heading_style="ATX", bullets="-", strip=["script", "style"])
    # Remove Weebly empty markdown artifacts
    md = re.sub(r"\n\s*\n\s*\n+", "\n\n", md)
    md = clean_html_text(md)
    return md


def process_blog_dir(src_dir: Path, dest_dir: Path, collection: str):
    dest_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in sorted(src_dir.glob("*.html")):
        # skip the archive/category listing pages
        if "archives" in str(f) or "category" in str(f):
            continue
        soup = BeautifulSoup(f.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        title = extract_title(soup, f.stem.replace("-", " ").title())
        date = extract_date(soup)
        content_html = extract_blog_content(soup)
        md_body = html_to_md(content_html)
        first_img = extract_first_image(content_html)

        slug = f.stem
        fm = ["---", f'title: "{title.replace(chr(34), chr(39))}"']
        if date:
            fm.append(f"date: {date}")
        if first_img:
            fm.append(f'image: "{first_img}"')
        fm.append("draft: false")
        fm.append("---")
        fm.append("")

        out = "\n".join(fm) + md_body + "\n"
        (dest_dir / f"{slug}.md").write_text(out, encoding="utf-8")
        count += 1
    print(f"Wrote {count} entries to {collection}/")


def process_pages():
    dest = CONTENT / "pages"
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for filename, (title, slug, hero, show, order) in PAGE_FILES.items():
        f = ROOT / filename
        if not f.exists():
            print(f"  skip missing: {filename}")
            continue
        soup = BeautifulSoup(f.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        content_html = extract_page_content(soup)
        md_body = html_to_md(content_html)
        hero_img = hero or extract_first_image(content_html)

        fm = ["---", f'title: "{title}"']
        if slug != f.stem:
            fm.append(f'slug: "{slug}"')
        if hero_img:
            fm.append(f'hero_image: "{hero_img}"')
        fm.append(f"show_in_nav: {'true' if show else 'false'}")
        if order is not None:
            fm.append(f"nav_order: {order}")
        fm.append("layout: default")
        fm.append("draft: false")
        fm.append("---")
        fm.append("")

        out = "\n".join(fm) + md_body + "\n"
        (dest / f"{slug}.md").write_text(out, encoding="utf-8")
        count += 1
    print(f"Wrote {count} pages to pages/")


def main():
    copy_uploads()
    process_blog_dir(ROOT / "poems", CONTENT / "poems", "poems")
    process_blog_dir(ROOT / "blog-entries", CONTENT / "blog", "blog")
    process_pages()


if __name__ == "__main__":
    main()
