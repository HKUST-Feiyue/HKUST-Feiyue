# Engineering principles

Source (`HKUST-Feiyue/HKUST-Feiyue`) owns code, content, workflows, and build logic. Published (`HKUST-Feiyue/HKUST-Feiyue.github.io`) contains generated static output only; never edit it directly. `PUBLISHED_README.md` supplies its README. Do not commit `_site/` to Source. See `README.md` for the publishing topology and `PREVIEW.md` for operating steps.

1. Every line of code should justify its existence. Define once; reuse everywhere.
2. Keep the site static and accessible. Prefer HTML/CSS/vanilla JS. Add dependencies only when a real requirement justifies them.
3. Five editorial categories only: further studies, research, career, exchange, entrepreneurship. Experiences include guidance; do not create a separate guide category.
4. `data/schema.json` owns category labels and submission fields. Never duplicate category definitions in multiple scripts. Article titles are derived from author and destination; do not request a redundant title from contributors.
5. Never pass invented student stories, admission results, testimonials, or counts off as real. Fictional editorial examples are allowed only with `demo: true` and a visible「演示」badge, never invented verifiable credentials or outcomes.
6. No hidden submission side effects. Never claim a submission succeeded until the backend confirms it.
7. Public GitHub Issues expose submitted content including optional contact details. Show a plain-language warning next to the form.
8. Use semantic markup, keyboard-accessible controls, responsive layouts, reduced-motion support, and readable contrast.
9. Browser previews and published pages must reuse `.article-page`, `.article-body`, headings, byline, and TOC structure. Preserve an automated browser comparison against published Markdown and do not add preview-only typography overrides. Use the same native collapsible article table of contents in preview and publication; highlight reading position without custom framework dependencies. Client Marked and server Python Markdown remain different parsers; document unsupported edge syntax rather than claiming byte-identical HTML. Changes must resolve root causes, not accumulate patches. Use one coherent PR for material engineering changes; routine content maintenance may use direct commits.
10. Preserve the inherited site palette; do not claim its values are official HKUST brand colors.

11. Branding: reuse the original `assets/images/hkust-horizontal.svg` unchanged on desktop and mobile. Never split, mask, clip, recolor or filter it, including in dark mode. Reuse `assets/icons/favicon.svg` for favicons and the footer without adding a white disc.
12. Layout: use `assets/images/hkust-campus.jpg` only for the shared top banner, with aspect-preserving `background-size: cover`, never as a fixed full-page background. Keep reading surfaces opaque. Desktop has a viewport-fixed sidebar isolated from document scrolling with a matching page offset; mobile has one viewport-fixed 72px topbar, a matching page offset and a single overlay menu. Keep the header stable at scroll boundaries and during viewport height changes.
13. Navigation: one source of menu open/closed state, with a transition-free reset before internal page navigation and on BFCache restoration. Do not add cross-document root transitions, another menu runtime or a framework.
14. Theme and footer: a single system/light/dark control in the sidebar; initialize the saved theme before CSS paints. The shared footer uses the same design tokens as the site, with no parallel footer palette variables.
15. Styles: group component rules by responsibility, retain one authoritative declaration per selector per context, and collect responsive styles under the existing breakpoints. Prefer deleting superseded code to appending more overrides. Preserve meaningful browser behavior tests rather than testing source formatting.

## Project structure and development

- Root `index.html` and `submit.html` are directly editable UI sources. Keep `assets/`, `content/`, `data/`, `scripts/` and `tests/` organized by their actual project responsibilities. The independent Worker accepts public Issues only after explicit launch. The maintainer-only Completed closure importer owns reviewed Markdown publication; never bypass GitHub review.
- `preview.py` provides local preview and verified artifact replacement; `scripts/site_build.py` runs this project's content pipeline in isolation. Publish `_site/` only. Shared page chrome is drawn from the homepage during generation; do not add a separate framework merely to make this repository resemble another site.
- Pagefind indexes only published article bodies from the generated `_site/` build and is lazy-loaded for full-text search. Keep category/campus/year/degree filters as UI intersection, not a second hand-maintained text index. Use one shared keyboard-accessible Popover select enhancement for submission fields and archive attributes, preserving native select fallback and schema-owned options. Textareas should grow with contents using CSS field-sizing and a tiny legacy fallback, never separate drag handles. Markdown sample insertion must leave the editor visible and show syntax guidance; do not force a preview transition. Schema owns required fields, limits and patterns. Keep the Worker fail-closed by default in version-controlled configuration and preserve the Cloudflare emergency kill switch. The public front-end config identifies the trusted endpoint and public Turnstile Site Key; production launch state is controlled by Cloudflare secrets and environment variables, never client-side security alone.
- Run `python -m unittest discover -s tests -t . -p 'test_*.py'`, `python preview.py --build-only` and `python tests/browser_smoke.py` for structural/UI changes. Each repository can evolve independently after this quality alignment.
- Treat cross-project alignment as a quality baseline, not a fixed repository template. Prefer familiar, purpose-driven organization; reuse proven logic only when it suits this project. Each site may evolve its UI, dependencies and structure independently.

## Bilingual interface

- `data/i18n.json` owns English and Traditional Chinese interface copy. Keep language keys aligned; retain English as the first-visit default, `?lang=zh/en` overrides and saved preferences.
- Contributor names, education details, destinations, article text and contact details are original content. Preserve them in either language, including Simplified Chinese; never translate or convert them as interface text.
- Keep language switching in place so filters, drafts and previews survive. Reuse the existing `hkust:language` event and one responsive language control.
