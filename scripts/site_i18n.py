"""Publish English UI with explicit translation bindings, preserving article text."""
import html
from html.parser import HTMLParser
import json
import re


class Localize(HTMLParser):
    def __init__(self, source, dictionary):
        super().__init__(convert_charrefs=False)
        self.source, self.dictionary = source, dictionary
        self.offsets = [0]
        self.offsets.extend(match.end() for match in re.finditer("\n", source))
        self.stack, self.edits = [], []
        self.feed(source)

    def position(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        start = self.position()
        raw = self.get_starttag_text()
        skip = (tag in ('script', 'style') or 'article-body' in values.get('class', '').split()
                or 'data-i18n-ignore' in values or any(item[2] for item in self.stack))
        extra = []
        for name in ('aria-label', 'title', 'placeholder', 'content'):
            value = values.get(name)
            if not skip and value in self.dictionary:
                raw = raw.replace(f'{name}="{html.escape(value, quote=True)}"',
                                  f'{name}="{html.escape(self.dictionary[value], quote=True)}"')
                extra.append(f'data-i18n-{name}="{html.escape(value, quote=True)}"')
        if tag == 'html':
            raw = re.sub(r'lang="[^"]+"', 'lang="en"', raw)
        if extra:
            raw = raw[:-1] + ' ' + ' '.join(extra) + '>'
        self.edits.append((start, start + len(self.get_starttag_text()), raw))
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.stack.append((tag, start, skip, values))

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_data(self, data):
        key = data.strip()
        if not self.stack or self.stack[-1][2]:
            return
        binding_key = self.stack[-1][3].get('data-i18n', key)
        if binding_key not in self.dictionary:
            return
        start = self.position() + len(data) - len(data.lstrip())
        params = json.loads(self.stack[-1][3].get('data-i18n-params', '{}'))
        value = html.escape(self.dictionary[binding_key].format_map({k: self.dictionary.get(str(v), str(v)) for k, v in params.items()}))
        binding = f'data-i18n="{html.escape(binding_key, quote=True)}"'
        if 'data-i18n' in self.stack[-1][3]:
            self.edits.append((self.position(), self.position() + len(data), value))
            return
        if self.stack[-1][0] in ('title', 'option'):
            tag_start = self.stack[-1][1]
            for index, (a, b, raw) in enumerate(self.edits):
                if a == tag_start:
                    self.edits[index] = (a, b, raw[:-1] + ' ' + binding + '>')
                    break
        else:
            value = f'<span {binding}>{value}</span>'
        self.edits.append((start, start + len(key), value))

    def result(self):
        result = self.source
        for start, end, replacement in sorted(self.edits, reverse=True):
            result = result[:start] + replacement + result[end:]
        return result


def generate(root):
    translations = json.loads((root / 'data/i18n.json').read_text(encoding='utf-8'))
    dictionary = translations['en']
    embedded = json.dumps(translations, ensure_ascii=True).replace('<', r'\u003c').replace('>', r'\u003e').replace('&', r'\u0026')
    for path in root.rglob('*.html'):
        source = Localize(path.read_text(encoding='utf-8'), dictionary).result()
        source = source.replace('</head>', '<script id="site-translations" type="application/json">' + embedded + '</script>\n</head>', 1)
        path.write_text(source, encoding='utf-8')
