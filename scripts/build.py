#!/usr/bin/env python3
"""Generate static article pages and a search index from Markdown content."""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

import yaml
from scripts.markdown_render import render_markdown
from scripts.submission_schema import validate_fields
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
OUTPUT = ROOT / "articles"
INDEX = ROOT / "data" / "articles.json"
SCHEMA = json.loads((ROOT / "data" / "schema.json").read_text(encoding="utf-8"))
CATEGORIES = {item["id"]: item["label"] for item in SCHEMA["categories"]}
YEAR_SUFFIX = next(field.get("suffix", "") for field in SCHEMA["fields"] if field["name"] == "year")


def parse(path):
    source = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", source, re.S)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    meta = yaml.safe_load(match.group(1))
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: invalid metadata")
    body = match.group(2).strip()
    if meta.get("category") not in CATEGORIES:
        raise ValueError(f"{path}: unknown category {meta.get('category')}")
    allowed = {x["name"] for x in SCHEMA["fields"]} - {"body"}
    if set(meta) - allowed - {"demo", "source_issue", "published_at"}:
        raise ValueError(f"{path}: unexpected metadata")
    clean = validate_fields(dict(meta, body=body))
    meta.update({k: v for k, v in clean.items() if k != "body"})
    published = meta.get("published_at")
    if not isinstance(published, str):
        raise ValueError(f"{path}: missing publication date")
    datetime.fromisoformat(published.replace("Z", "+00:00"))
    if path.stem == "README":
        raise ValueError("README cannot be an article")
    return meta, body


def excerpt(body):
    from html.parser import HTMLParser
    class Text(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)
    parser = Text()
    parser.feed(render_markdown(body))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()[:150]


def entry_period(meta):
    field = next(field for field in SCHEMA["fields"] if field["name"] == "term")
    label = next(option["label"] for option in field["options"] if option["value"] == meta["term"])
    return meta["year"] + " " + label


def display_title(meta):
    """One title convention shared by archive cards and article pages."""
    return str(meta["author"]).strip() + " · " + str(meta["destination"]).strip()


def ui(key, **params):
    value = key.format_map(params)
    return f'<span data-i18n="{html.escape(key, quote=True)}" data-i18n-params="{html.escape(json.dumps(params, ensure_ascii=False), quote=True)}">{html.escape(value)}</span>'


def original(value):
    return f'<span data-i18n-ignore>{html.escape(str(value))}</span>'


def shared_chrome(source, page, prefix="./", category=None):
    """Reuse the homepage's navigation/header/footer without a separate UI framework."""
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    icon_pattern = r'<link rel="(?:icon|apple-touch-icon|manifest)"[^>]*>'
    icons = '\n'.join(re.findall(icon_pattern, home))
    source = re.sub(icon_pattern + r'\s*', '', source)
    source = source.replace('</head>', icons + '\n</head>', 1)
    sidebar = re.search(r'<aside class="sidebar".*?</aside>', home, re.S)[0]
    links = [f'<a href="{prefix}" data-view="home">首页</a>',
             f'<a href="{prefix}?view=all" data-category="all">全部经历</a>']
    for item in SCHEMA["categories"]:
        selected = ' aria-current="page"' if category == item["id"] else ''
        links.append(f'<a href="{prefix}?category={quote(item["id"])}" data-category="{html.escape(item["id"], quote=True)}" data-category-label="{html.escape(item["label"], quote=True)}" data-category-description="{html.escape(item["description"], quote=True)}"{selected}>{html.escape(item["label"])}</a>')
    links.append(f'<a href="{prefix}submit.html" class="nav-contribute"' + (' aria-current="page"' if page == "submit" else '') + '>投稿分享 <span class="link-arrow" aria-hidden="true"></span></a>')
    links.append(f'<a href="{prefix}community.html" class="nav-community"' + (' aria-current="page"' if page == "community" else '') + '>共建与联系 <span class="link-arrow" aria-hidden="true"></span></a>')
    sidebar = re.sub(r'(<nav class="nav"[^>]*>).*?(</nav>)', lambda m: m[1] + ''.join(links) + m[2], sidebar, flags=re.S)
    header = re.search(r'<header class="topbar"[^>]*>.*?</header>', home, re.S)[0]
    if page != "index":
        search_button = re.search(r'<button[^>]*class="search-open".*?</button>', home, re.S)[0].replace(' hidden', '')
        header = header.replace('</header>', search_button + '</header>')
        dialog = re.search(r'<dialog class="search-dialog".*?</dialog>', home, re.S)[0]
        if 'id="search-dialog"' not in source:
            source = source.replace('</body>', dialog + '</body>')
    footer = re.search(r'<footer class="site-footer".*?</footer>', home, re.S)[0]
    footer_links = f'<a href="{prefix}?view=all">全部经历</a>' + ''.join(
        f'<a href="{prefix}?category={quote(item["id"])}">{html.escape(item["label"])}</a>' for item in SCHEMA["categories"])
    footer_links += f'<a href="{prefix}submit.html">投稿分享</a><a href="{prefix}community.html">共建与联系</a>'
    footer = re.sub(r'(<nav class="footer-links"[^>]*>).*?(</nav>)', lambda m: m[1] + footer_links + m[2], footer, flags=re.S)
    footer = footer.replace('class="footer-copyright" href="./community.html"', f'class="footer-copyright" href="{prefix}community.html"')
    for pattern, fragment in ((r'<aside class="sidebar".*?</aside>', sidebar),
                              (r'<header class="topbar"[^>]*>.*?</header>', header),
                              (r'<footer class="site-footer".*?</footer>', footer)):
        source = re.sub(pattern, lambda _: fragment, source, count=1, flags=re.S)
    source = re.sub(r'((?:src|href)=")(?:(?:\./)?assets/)', lambda m: m[1] + prefix + 'assets/', source)
    if prefix != "./":
        source = source.replace('href="./"', f'href="{prefix}"')
    if page != "index":
        source = source.replace('class="page is-home"', 'class="page"')
    return source


def render(meta, body, url):
    clean = render_markdown(body)
    byline = " · ".join([ui(next(x["label"] for x in next(field for field in SCHEMA["fields"] if field["name"] == "campus")["options"] if x["value"] == meta["campus"])), original(entry_period(meta)), original(meta["degree"])])
    headings = re.findall(r'<h([23]) id="([^"]+)">(.+?)</h[23]>', clean)
    toc = '<details class="article-toc"><summary>本页目录</summary><div class="article-toc-panel"><div class="article-toc-clip"><ul>' + ''.join(f'<li class="toc-depth-{level}"><a data-i18n-ignore href="#{html.escape(anchor, quote=True)}">{text}</a></li>' for level, anchor, text in headings) + '</ul></div></div></details>' if len(headings) >= 2 else ''
    demo = '<span class="demo-badge">演示</span>' if meta.get('demo') is True else ''
    contact = ''
    if meta.get("contact"):
        rows = ''.join('<p><span data-i18n-ignore>' + html.escape(row["type"]) + '：' + html.escape(row["value"]) + '</span> <button type="button" class="copy-contact" data-copy="' + html.escape(row["value"], quote=True) + '">复制</button></p>' for row in meta["contact"])
        contact = '<aside class="article-contact" data-pagefind-ignore><strong>联系作者</strong>' + rows + '</aside>'
    source = shared_chrome((ROOT / "index.html").read_text(encoding="utf-8"), "article", "../", meta["category"])
    source = source.replace("<body data-pagefind-ignore>", "<body>", 1)
    title = html.escape(display_title(meta))
    source = re.sub(r'<title>.*?</title>', lambda _: f'<title data-i18n-ignore>{title} · HKUST Feiyue</title>', source, count=1, flags=re.S)
    description = html.escape(excerpt(body), quote=True)
    source = re.sub(r'<meta name="description"[^>]*>', lambda _: f'<meta name="description" content="{description}" data-i18n-ignore>', source, count=1)
    content = f'<article class="article-page" data-pagefind-body><a class="article-back" href="../?category={quote(str(meta["category"]))}"><span class="link-arrow link-arrow-left" aria-hidden="true"></span> {ui("返回{category}", category=CATEGORIES[meta["category"]])}</a><h1 data-pagefind-meta="title" data-i18n-ignore>{title}</h1>{demo}<p class="article-byline" data-pagefind-meta="byline">{byline}</p><p class="article-field" data-i18n-ignore>{html.escape(meta["field"])}</p><time datetime="{html.escape(meta["published_at"], quote=True)}">{html.escape(meta["published_at"][:10])}</time>{toc}<div class="article-body">{clean}</div>{contact}</article>'
    return re.sub(r'(<main[^>]*>).*?(</main>)', lambda m: m[1] + content + m[2], source, count=1, flags=re.S)


def render_home(entries):
    source = shared_chrome((ROOT / "index.html").read_text(encoding="utf-8"), "index")
    cards = []
    for entry in entries:
        badge = '<span class="demo-badge">演示</span>' if entry["demo"] else ''
        esc = lambda value: html.escape(str(value), quote=True)
        label = ' · '.join([ui(next(x["label"] for x in next(field for field in SCHEMA["fields"] if field["name"] == "campus")["options"] if x["value"] == entry["campus"])), original(entry_period(entry)), original(entry["degree"])])
        cards.append(f'<article class="article-item" data-category="{esc(entry["category"])}" data-campus="{esc(entry["campus"])}" data-degree="{esc(entry["degree"])}" data-year="{esc(entry["year"])}" data-demo="{str(entry["demo"]).lower()}">{badge}<h3 data-i18n-ignore><a href="./{esc(entry["url"])}">{esc(entry["title"])}</a></h3><p class="article-meta">{label}</p><p class="article-field" data-i18n-ignore>{esc(entry["field"])}</p><p class="article-excerpt" data-i18n-ignore>{esc(entry["excerpt"])}</p><div class="article-item-footer"><time datetime="{esc(entry["published_at"])}">{esc(entry["published_at"][:10])}</time><a class="article-more" href="./{esc(entry["url"])}">阅读全文<span class="link-arrow"></span></a></div></article>')
    source = re.sub(r'(<div id="articles"[^>]*>).*?(</div>\s*<div id="empty-state")', lambda m: m[1] + ''.join(cards) + m[2], source, count=1, flags=re.S)
    years = ''.join(f'<option value="{html.escape(year, quote=True)}">{html.escape(year)}</option>' for year in sorted({entry["year"] for entry in entries}, reverse=True))
    source = re.sub(r'(<select\b[^>]*\bid="year-filter"[^>]*>).*?(</select>)', lambda m: m[1] + '<option value="all">全部年份</option>' + years + m[2], source, count=1, flags=re.S)
    for name, default in (("campus", "全部校区"), ("degree", "全部学位")):
        field = next(x for x in SCHEMA["fields"] if x["name"] == name)
        available = {entry[name] for entry in entries}
        options = ''.join(f'<option value="{html.escape(x["value"], quote=True)}">{html.escape(x["label"])}</option>' for x in field["options"] if name == "campus" or x["value"] in available)
        source = re.sub(r'(<select\b[^>]*\bid="' + name + r'-filter"[^>]*>).*?(</select>)', lambda m: m[1] + '<option value="all">' + default + '</option>' + options + m[2], source, count=1, flags=re.S)
    count = ui('{count} 篇经历', count=len(entries)) + (ui(' · 含演示内容') if any(entry["demo"] for entry in entries) else '')
    return re.sub(r'(<p id="results-count"[^>]*>).*?(</p>)', lambda m: m[1] + count + m[2], source, count=1, flags=re.S)



def main():
    paths = sorted(CONTENT.rglob("*.md"))
    entries = []
    pages = {}
    for path in paths:
        if path.name == "README.md":
            continue
        meta, body = parse(path)
        slug = path.stem
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            raise ValueError(f"{path}: filename must be lowercase ascii slug")
        filename = slug + ".html"
        if filename in pages:
            raise ValueError(f"duplicate article slug: {slug}")
        url = "articles/" + filename
        pages[filename] = render(meta, body, url)
        entries.append({
            "demo": meta.get("demo") is True,
            "title": display_title(meta),
            "category": meta["category"],
            "author": str(meta["author"]),
            "year": str(meta["year"]),
            **{key: meta[key] for key in ("campus", "term", "degree", "field", "published_at")},
            "destination": str(meta.get("destination", "")),
            "excerpt": excerpt(body),
            "url": url,
        })
    entries.sort(key=lambda entry: entry["published_at"], reverse=True)
    OUTPUT.mkdir(exist_ok=True)
    for old in OUTPUT.glob("*.html"):
        if old.name not in pages:
            old.unlink()
    for name, page in pages.items():
        (OUTPUT / name).write_text(page, encoding="utf-8")
    INDEX.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "index.html").write_text(render_home(entries), encoding="utf-8")
    submission = (ROOT / "submit.html").read_text(encoding="utf-8")
    (ROOT / "submit.html").write_text(shared_chrome(submission, "submit"), encoding="utf-8")
    community = (ROOT / "community.html").read_text(encoding="utf-8")
    (ROOT / "community.html").write_text(shared_chrome(community, "community"), encoding="utf-8")
    print(f"Generated {len(entries)} articles")


if __name__ == "__main__":
    main()
