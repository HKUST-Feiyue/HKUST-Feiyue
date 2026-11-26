"""Build invariants for structured submissions and safe Markdown output."""
import importlib.util
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("hkust_build", ROOT / "scripts" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class SubmissionBuildTests(unittest.TestCase):
    def test_removing_last_article_clears_pages_and_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'content').mkdir()
            for name in ('data', 'scripts', 'assets'):
                shutil.copytree(ROOT / name, root / name)
            shutil.copy2(ROOT / 'PUBLISHED_README.md', root / 'PUBLISHED_README.md')
            for name in ('index.html', 'submit.html', 'community.html'):
                (root / name).write_text((ROOT / name).read_text(encoding='utf-8'), encoding='utf-8')
            meta = dict(author='Fixture', destination='Fixture destination', campus='hk',
                        year='2026', term='fall', degree='BSc', field='Original field',
                        category='career', published_at='2026-11-25T00:00:00Z')
            article = root / 'content/fixture.md'
            article.write_text('---\n' + build.yaml.safe_dump(meta) + '---\n## Body\n\nFixture body', encoding='utf-8')
            with patch.multiple(build, ROOT=root, CONTENT=root / 'content',
                                OUTPUT=root / 'articles', INDEX=root / 'data/articles.json'):
                build.main()
                self.assertTrue((root / 'articles/fixture.html').is_file())
                article.unlink()
                build.main()
            self.assertEqual(list((root / 'articles').glob('*.html')), [])
            self.assertEqual(json.loads((root / 'data/articles.json').read_text(encoding='utf-8')), [])
            self.assertNotIn('class="article-item"', (root / 'index.html').read_text(encoding='utf-8'))
            from scripts.site_build import build as build_site
            build_site(root, root / 'empty-site', {})
            self.assertEqual(json.loads((root / 'empty-site/data/articles.json').read_text(encoding='utf-8')), [])

    def test_archive_rebuild_does_not_duplicate_nested_cards(self):
        entry = dict(author='Test', title='Example', campus='hk', year='2026', term='fall',
                     degree='BSc', field='Computing', category='career', destination='Example',
                     excerpt='Example body', published_at='2026-11-25T00:00:00Z', url='articles/example.html')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'index.html'
            source.write_text((ROOT / 'index.html').read_text(encoding='utf-8'), encoding='utf-8')
            with patch.object(build, 'ROOT', root):
                first = build.render_home([entry])
                source.write_text(first, encoding='utf-8')
                second = build.render_home([entry])
            self.assertEqual(first, second)
            self.assertEqual(second.count('class="article-item"'), 1)
            self.assertEqual(second.count('class="article-item-footer"'), 1)

    def test_unified_theme_background_and_footer(self):
        stylesheet = "".join((ROOT / "assets/css/site.css").read_text(encoding="utf-8").split())
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        self.assertIn('url("../images/hkust-campus.jpg")', stylesheet)
        self.assertIn(".campus-banner{", stylesheet)
        self.assertIn("background-size:cover", stylesheet)
        self.assertIn("height:clamp(270px,30vw,440px)", stylesheet)
        self.assertIn("height:clamp(220px,60vw,320px)", stylesheet)
        self.assertNotIn("@view-transition{navigation:auto}", stylesheet)
        self.assertIn("position:fixed;top:0;left:0;right:0;z-index:50", stylesheet)
        self.assertIn("--mobile-header-height:72px", stylesheet)
        self.assertNotIn(".shell.menu-open::before", stylesheet)
        self.assertRegex(stylesheet, r"body\{[^}]*background:var\(--bg\)")
        self.assertNotIn("background-attachment:fixed", stylesheet)
        self.assertNotIn(".page::before{", stylesheet)
        self.assertIn('rel="preload" as="image"', homepage)
        self.assertNotIn('data-view="home" aria-current="page"', build.render_home([]))
        self.assertIn('rel="preload" as="image"', submission)
        self.assertIn('class="campus-banner"', homepage)
        self.assertIn('class="campus-banner"', submission)
        article = build.render({"category": "career", "author": "同学", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "企业"}, "## 正文", "articles/test.html")
        self.assertIn('class="campus-banner"', article)
        self.assertIn('rel="preload" as="image" href="../assets/images/hkust-campus.jpg"', article)
        self.assertIn(".site-footer{flex:none;background:linear-gradient(tobottom,var(--bg),var(--surface)80px)", stylesheet)
        for page in (homepage, submission):
            self.assertIn('data-site-footer', page)
            self.assertIn('assets/js/theme-init.js', page)
        self.assertNotIn("hero-visual", homepage)
        self.assertNotIn("hero-corner", homepage)
        self.assertIn('theme-init.js', build.render({"category": "career", "author": "同学", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "企业"}, "## 正文", "articles/test.html"))

    def test_mobile_chrome_is_shared_across_routes(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        article = build.render({"category": "career", "author": "同学", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z",
                                "destination": "企业"}, "## 正文", "articles/test.html")
        for source in (homepage, submission, article):
            self.assertIn('class="topbar" aria-label="移动端导航栏"', source)
            self.assertIn('class="menu-lines"', source)
            self.assertIn('aria-controls="sidebar"', source)

    def test_pagefind_indexing_and_sidebar_chrome(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        renderer = (ROOT / "scripts/site_build.py").read_text(encoding="utf-8")
        article = build.render({"category": "career", "author": "同学", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "企业"}, "## 搜索正文", "articles/sample.html")
        for html_source in (homepage, submission):
            self.assertIn("<body data-pagefind-ignore>", html_source)
            self.assertEqual(html_source.count('id="theme-toggle"'), 1)
            self.assertNotIn('id="theme-toggle-mobile"', html_source)
        self.assertIn('data-pagefind-body', article)
        self.assertIn('"pagefind"', renderer)
        self.assertNotIn('data-search=', homepage)
        self.assertIn('id="search-dialog"', homepage)

    def test_year_menu_and_editor_contract(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        source = (ROOT / "assets/js/submit.js").read_text(encoding="utf-8")
        site = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
        css = "".join((ROOT / "assets/css/site.css").read_text(encoding="utf-8").split())
        schema = json.loads((ROOT / "data/schema.json").read_text(encoding="utf-8"))
        self.assertIn('id="year-filter"', homepage)
        self.assertIn("window.HKUSTSelect.enhance(archive)", site)
        self.assertIn("panel.hidePopover()", (ROOT / "assets/js/select.js").read_text(encoding="utf-8"))
        self.assertIn("field-sizing:content", css)
        self.assertNotIn("textarea-grip", css + source)
        self.assertIn("markdown-help-content", source)
        self.assertIn("control.hidden = showing", source)
        self.assertIn("textarea", source)
        self.assertIn('id="preview-text"', submission)
        fields = {entry["name"]: entry for entry in schema["fields"]}
        self.assertIn("hello@example.com", fields["contact"]["valuePlaceholder"])
        self.assertEqual(fields["year"]["pattern"], "[0-9]{4}")

    def test_shared_theme_toc_and_form_layout(self):
        stylesheet = "".join((ROOT / "assets/css/site.css").read_text(encoding="utf-8").split())
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        submission = (ROOT / "submit.html").read_text(encoding="utf-8")
        js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
        for document in (homepage, submission):
            self.assertIn('data-mode="system"', document)
            for mode in ("system", "light", "dark"):
                self.assertIn('data-theme-icon="' + mode + '"', document)
        self.assertIn("prefers-color-scheme:dark", stylesheet)
        self.assertIn("['system', 'light', 'dark']", js)
        self.assertIn('class="year-select"', homepage)
        self.assertIn('.select-trigger{', stylesheet)
        self.assertIn('.article-tocsummary{', stylesheet)
        self.assertIn(".form-wrap{max-width:820px;padding:0;", stylesheet)
        article = build.render({"category": "career", "author": "同学", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "企业"},
                               "## 第一章\n\n正文\n\n## 第二章\n\n正文", "articles/test.html")
        self.assertIn('<details class="article-toc">', article)
        self.assertIn('<summary>本页目录</summary>', article)

    def test_published_article_brand_assets(self):
        meta = {"category": "career", "author": "同学", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "企业"}
        page = build.render(meta, "## 正文", "articles/example.html")
        self.assertIn('../assets/icons/favicon.svg', page)
        self.assertIn('class="brand-logo" src="../assets/images/hkust-horizontal.svg"', page)
        self.assertIn('class="mobile-brand-logo" src="../assets/images/hkust-horizontal.svg"', page)
        self.assertNotIn('brand-wordmark', page)
        self.assertNotIn('brand-seal', page)
        stylesheet = "".join((ROOT / "assets/css/site.css").read_text(encoding="utf-8").split())
        self.assertIn('.footer-logo{display:block;width:52px;height:52px;flex:none;object-fit:contain;', stylesheet)
        for rule in stylesheet.split("}"):
            if "-logo" in rule.partition("{")[0]:
                self.assertNotIn("mask-image:", rule)
                self.assertNotIn("clip-path:", rule)

    def test_no_redundant_title_field(self):
        schema = json.loads((ROOT / "data/schema.json").read_text(encoding="utf-8"))
        names = {field["name"] for field in schema["fields"]}
        self.assertNotIn("title", names)
        self.assertTrue({"author", "campus", "year", "degree", "field", "category", "destination", "body", "contact"} <= names)

    def test_title_auto_generated(self):
        meta = {"author": "张同学", "destination": "香港中文大学"}
        self.assertEqual(build.display_title(meta), "香港中文大学")

    def test_render_heading_table_and_sanitize(self):
        meta = {"category": "further-studies", "author": "张同学", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "香港中文大学"}
        body = "# 一级标题\\n\\n| 项目 | 说明 |\\n| --- | --- |\\n| A | B |\\n\\n~~删除文字~~\\n\\n- [x] 已完成\\n\\n<script>alert(1)</script>".replace("\\n", "\n")
        page = build.render(meta, body, "articles/sample.html")
        self.assertIn("<h1", page)
        self.assertIn("<table>", page)
        self.assertIn("<del>", page)
        self.assertIn('type="checkbox"', page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_schema_required_fields_and_limits_are_enforced_before_publication(self):
        meta = {"category": "career", "author": "Test author", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "Example"}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test.md"
            for field in build.SCHEMA["fields"]:
                if field.get("required"):
                    values = dict(meta)
                    body = "Article body"
                    if field["name"] == "body":
                        body = ""
                    else:
                        values.pop(field["name"], None)
                    source.write_text("---\n" + build.yaml.safe_dump(values) + "---\n" + body, encoding="utf-8")
                    with self.subTest(field=field["name"]), self.assertRaises(ValueError):
                        build.parse(source)
                if field.get("maxLength"):
                    excessive = "x" * (field["maxLength"] + 1)
                    values = dict(meta)
                    body = "Body"
                    if field["name"] == "body":
                        body = excessive
                    else:
                        values[field["name"]] = excessive
                    source.write_text("---\n" + build.yaml.safe_dump(values) + "---\n" + body, encoding="utf-8")
                    with self.subTest(limit=field["name"]), self.assertRaises(ValueError):
                        build.parse(source)

    def test_schema_category_and_year_patterns_reject_invalid_content(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "test.md"
            for category, year in (("unknown", "2026"), ("career", "abcd"), ("career", True)):
                values = {"category": category, "year": year, "author": "Test", "destination": "Example"}
                source.write_text("---\n" + build.yaml.safe_dump(values) + "---\nBody", encoding="utf-8")
                with self.subTest(category=category, year=year), self.assertRaises(ValueError):
                    build.parse(source)

    def test_article_metadata_and_author_are_separate(self):
        meta = {"category": "career", "author": "Test author", "year": "2026", "term": "fall", "campus": "hk", "degree": "BSc", "field": "Computing", "published_at": "2026-11-25T00:00:00Z", "destination": "Example"}
        page = build.render(meta, "Article body", "articles/example.html")
        self.assertIn(">Example</h1>", page)
        self.assertIn(">Test author · 2026 Fall</p>", page)

    def test_preview_reuses_article_styles(self):
        source = "".join((ROOT / "assets/css/site.css").read_text(encoding="utf-8").split())
        form = (ROOT / "submit.html").read_text(encoding="utf-8")
        self.assertIn('id="preview-text" class="article-page"', form)
        self.assertNotIn(".preview .article-body{font-size", source)
        self.assertNotIn(".preview h3{", source)

    def test_demo_is_not_represented_as_real_story(self):
        sample = (ROOT / "data/demo-submission.md").read_text(encoding="utf-8")
        self.assertIn("不是真實投稿", sample)


if __name__ == "__main__":
    unittest.main()
