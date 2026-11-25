"""Canonical validation for signed submissions and article frontmatter."""
import json
import re
from pathlib import Path
SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "data/schema.json").read_text(encoding="utf-8"))
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

def validate_fields(values):
    result = {}
    for field in SCHEMA["fields"]:
        name = field["name"]
        value = values.get(name, [] if name == "contact" else "")
        if name == "contact":
            if not isinstance(value, list) or len(value) > field["maxItems"]:
                raise ValueError("Invalid contacts")
            contacts = []
            for row in value:
                if not isinstance(row, dict) or set(row) != {"type", "value"}:
                    raise ValueError("Invalid contact row")
                clean = {}
                for key, limit in (("type", field["typeMaxLength"]), ("value", field["valueMaxLength"])):
                    item = row[key]
                    if not isinstance(item, str) or CONTROL.search(item) or len(item.strip()) > limit:
                        raise ValueError("Invalid contact value")
                    clean[key] = item.strip()
                if not any(clean.values()):
                    continue
                if not all(clean.values()):
                    raise ValueError("Incomplete contact")
                contacts.append(clean)
            result[name] = contacts
            continue
        if not isinstance(value, str) or CONTROL.search(value):
            raise ValueError("Invalid " + name)
        value = value.strip()
        if field["required"] and not value:
            raise ValueError("Missing " + name)
        if field.get("maxLength") and len(value) > field["maxLength"]:
            raise ValueError("Oversized " + name)
        if field.get("pattern") and not re.fullmatch(field["pattern"], value):
            raise ValueError("Invalid " + name)
        options = [{"value": x["id"]} for x in SCHEMA["categories"]] if name == "category" else field.get("options", [])
        if options and value not in {x["value"] for x in options}:
            raise ValueError("Invalid " + name)
        result[name] = value
    return result
