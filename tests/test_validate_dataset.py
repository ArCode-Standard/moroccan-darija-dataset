import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "validator", Path(__file__).parents[1] / "scripts" / "validate_dataset.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Tests(unittest.TestCase):
    def fixture(self):
        return {
            "meta": {"entries_count": 1, "categories_count": 1},
            "categories": [{"category": "تحيات", "count": 1}],
            "entries": [{
                "id": 1, "category": "تحيات", "darija_ar": "سلام",
                "darija_latin": "salam", "fusha_ar": "سلام", "fr": "salut"
            }]
        }

    def registry(self, permission="unknown", status="pending_verification"):
        source = {
            "source_id": "s1", "source_type": "unknown",
            "redistribution_permission": permission,
            "training_permission": "unknown",
            "commercial_permission": "unknown",
            "rights_status": status
        }
        return {"sources": [source]}, {"s1": source}


    def test_json_schema_rejects_unknown_entry_fields(self):
        d = self.fixture()
        d["entries"][0]["invented_field"] = "not allowed"
        schema = {
            "type": "object",
            "properties": {
                "entries": {
                    "type": "array",
                    "items": {"type": "object", "additionalProperties": False}
                }
            }
        }
        errors = module.validate_schema(d, schema)
        self.assertTrue(any("invented_field" in error for error in errors))

    def test_legacy_entry_is_auditable_but_warned(self):
        errors, warnings = module.validate(self.fixture(), {})
        self.assertEqual(errors, [])
        self.assertTrue(any("provenance: missing" in w for w in warnings))

    def test_duplicate_id_fails(self):
        d = self.fixture()
        d["entries"].append(dict(d["entries"][0]))
        d["meta"]["entries_count"] = 2
        d["categories"][0]["count"] = 2
        errors, _ = module.validate(d, {})
        self.assertTrue(any("duplicate id" in e for e in errors))

    def test_count_mismatch_fails(self):
        d = self.fixture()
        d["categories"][0]["count"] = 2
        errors, _ = module.validate(d, {})
        self.assertTrue(any("declared 2, actual 1" in e for e in errors))

    def test_invalid_permission_fails(self):
        registry, _ = self.registry()
        registry["sources"][0]["training_permission"] = "maybe"
        errors, _, _ = module.validate_sources(registry)
        self.assertTrue(any("training_permission" in e for e in errors))

    def test_allowed_without_evidence_fails(self):
        registry, _ = self.registry(permission="allowed")
        errors, _, _ = module.validate_sources(registry)
        self.assertTrue(any("without license or permission evidence" in e for e in errors))

    def test_strict_public_rejects_legacy_entry(self):
        errors, _ = module.validate(self.fixture(), {}, strict_public=True)
        self.assertTrue(any("not publishable without provenance" in e for e in errors))

    def test_cleared_requires_evidence(self):
        registry, _ = self.registry(permission="allowed", status="cleared")
        errors, _, _ = module.validate_sources(registry)
        self.assertTrue(any("permission_evidence" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
