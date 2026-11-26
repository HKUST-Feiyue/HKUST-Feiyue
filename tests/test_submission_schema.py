"""Ten-field contract, safe contacts and actual JS→Python signed publication."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.submission_schema import SCHEMA, validate_fields
from scripts.import_completed_submission import import_event
from scripts.build import parse, render, display_title, excerpt
ROOT = Path(__file__).resolve().parents[1]

def record():
    return dict(version=1, author="Alex <script>", campus="gz", year="2024", term="fall", degree="MPhil", field="AI & Robotics", category="research", destination="Example Lab", body="## Preparation\n\nActual Markdown **experience**.\n\n## Advice\n\nUseful advice.", contact=[dict(type="Email",value="contact-unique@example.com")])

class ContractTests(unittest.TestCase):
    def test_contact_rows_normalize_without_losing_order(self):
        value = record()
        value["contact"] = [{"type":" ","value":""},{"type":" 微信 ","value":" id "},{"type":"Email","value":"a@example.com"}]
        self.assertEqual(validate_fields(value)["contact"], [{"type":"微信","value":"id"},{"type":"Email","value":"a@example.com"}])
        value.pop("contact")
        self.assertEqual(validate_fields(value)["contact"], [])

    def test_invalid_contacts_rejected(self):
        for contacts in ("text", {}, [dict(type="Email",value="")], [dict(type="",value="id")], [dict(type="a",value="x",extra="z")], [dict(type="a",value="\x00")], [dict(type="a",value="x"*501)], [dict(type="a",value="b")]*11):
            with self.subTest(contacts=contacts), self.assertRaises(ValueError):
                validate_fields(dict(record(),contact=contacts))

    def test_all_enums_and_required_fields(self):
        value=record()
        for field in SCHEMA["fields"]:
            if field["required"]:
                with self.subTest(missing=field["name"]), self.assertRaises(ValueError):
                    validate_fields({k:v for k,v in value.items() if k != field["name"]})
            for option in field.get("options", []):
                self.assertEqual(validate_fields(dict(value, **{field["name"]:option["value"]}))[field["name"]], option["value"])
        for name,item in (("year",2024),("year","24"),("campus","other"),("degree","Bachelor"),("category","legacy")):
            with self.subTest(name=name,item=item), self.assertRaises(ValueError):
                validate_fields(dict(value, **{name:item}))

    def test_worker_signature_import_and_build(self):
        for category in SCHEMA["categories"]:
            value=dict(record(),category=category["id"])
            generated=json.loads(subprocess.check_output(["node",str(ROOT/"tests/signed_fixture.mjs"),json.dumps(value)],text=True,encoding="utf-8"))
            issue=dict(generated["issue"],number=57,state_reason="completed",closed_at="2026-11-25T00:00:00Z")
            event=dict(action="closed",repository={"full_name":"HKUST-Feiyue/HKUST-Feiyue"},issue=issue)
            with tempfile.TemporaryDirectory() as directory:
                target,created=import_event(event,Path(directory),generated["pem"])
                self.assertTrue(created)
                meta,body=parse(target)
                self.assertEqual(meta["year"],"2024")
                self.assertEqual(meta["term"],"fall")
                self.assertEqual(meta["published_at"],issue["closed_at"])
                self.assertEqual(meta["contact"],value["contact"])
                page=render(meta,body,"articles/issue-57.html")
                self.assertIn('2024 Fall',page)
                self.assertIn('class="article-contact" data-pagefind-ignore',page)
                self.assertIn('data-copy="contact-unique@example.com"',page)
                self.assertIn('>Example Lab</h1>',page)
                self.assertIn('>Alex &lt;script&gt;</p>',page)
                self.assertNotIn('<script> · Example Lab',page)
                self.assertNotIn('contact-unique',excerpt(body))
                self.assertFalse(import_event(event,Path(directory),generated["pem"])[1])
