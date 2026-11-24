"""Language bindings cover interface text and preserve contributor content."""
import json
from pathlib import Path
import unittest

from scripts.site_i18n import Localize

ROOT = Path(__file__).resolve().parents[1]


class LanguageTests(unittest.TestCase):
    def test_default_english_and_explicit_content_boundary(self):
        source = ('<html lang="zh-CN"><head><title>首页</title>'
                  '<meta name="description" content="首页" data-i18n-ignore></head>'
                  '<body><a aria-label="首页">首页</a><select><option>首页</option></select>'
                  '<h1 data-i18n-ignore>首页</h1><div class="article-body"><p>首页 / My story</p><a title="首页">My link</a></div>'
                  '<script>const title = "首页";</script></body></html>')
        result = Localize(source, {'首页': 'Home'}).result()
        self.assertIn('<html lang="en">', result)
        self.assertIn('<title data-i18n="首页">Home</title>', result)
        self.assertIn('<option data-i18n="首页">Home</option>', result)
        self.assertIn('aria-label="Home" data-i18n-aria-label="首页"', result)
        self.assertIn('<h1 data-i18n-ignore>首页</h1>', result)
        self.assertIn('<p>首页 / My story</p>', result)
        self.assertIn('<a title="首页">My link</a>', result)
        self.assertIn('content="首页" data-i18n-ignore', result)
        self.assertIn('const title = "首页";', result)

    def test_translation_coverage_for_schema_owned_interface(self):
        translations = json.loads((ROOT / 'data/i18n.json').read_text(encoding='utf-8'))
        self.assertEqual(translations['en'].keys(), translations['zh'].keys())
        dictionary = translations['en']
        schema = json.loads((ROOT / 'data/schema.json').read_text(encoding='utf-8'))
        for category in schema['categories']:
            for name in ('label', 'description'):
                self.assertTrue(dictionary[category[name]])
        for field in schema['fields']:
            for name in ('label', 'hint', 'group', 'suffix'):
                if field.get(name):
                    self.assertTrue(dictionary[field[name]])
            for value in [field.get('placeholder'), *field.get('placeholders', {}).values()]:
                if value and value != '2026':
                    self.assertTrue(dictionary[value])

    def test_template_parameters_are_translated_and_escaped(self):
        source = '<p><span data-i18n="返回{category}" data-i18n-params="{&quot;category&quot;:&quot;就业&quot;}">返回就业</span></p>'
        result = Localize(source, {'返回{category}': 'Back to {category}', '就业': 'Careers'}).result()
        self.assertIn('>Back to Careers</span>', result)
