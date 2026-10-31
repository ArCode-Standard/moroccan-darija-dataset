#!/usr/bin/env python3
"""Validate collection metadata and candidate/corpus records against JSON Schemas."""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_file(data_path, schema_path):
    data = load(data_path)
    schema = load(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    return [f"{data_path}: {e.json_path}: {e.message}" for e in errors], data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="data/collection/source-registry.json")
    parser.add_argument("--source-schema", default="schemas/source-registry.schema.json")
    parser.add_argument("--candidates", nargs="*", default=[])
    parser.add_argument("--candidate-schema", default="schemas/lexical-candidate.schema.json")
    parser.add_argument("--documents", nargs="*", default=[])
    parser.add_argument("--document-schema", default="schemas/corpus-document.schema.json")
    args = parser.parse_args()

    errors = []
    checks = [(args.sources, args.source_schema, "sources")]
    checks += [(p, args.candidate_schema, "candidate") for p in args.candidates]
    checks += [(p, args.document_schema, "document") for p in args.documents]

    for data_path, schema_path, kind in checks:
        try:
            found, data = validate_file(data_path, schema_path)
            errors.extend(found)
            if kind == "sources" and isinstance(data, dict):
                for i, source in enumerate(data.get("sources", [])):
                    if source.get("personal_data_collected") is not False:
                        errors.append(f"{data_path}: sources[{i}].personal_data_collected must be false")
                    if source.get("user_tracking_performed") is not False:
                        errors.append(f"{data_path}: sources[{i}].user_tracking_performed must be false")
            if kind == "document" and isinstance(data, dict):
                if data.get("personal_data_present") is True and data.get("publication_status") != "excluded":
                    errors.append(f"{data_path}: documents with personal data must be excluded pending remediation")
                if data.get("publication_status") == "redistributable":
                    for field in ("storage_permission", "redistribution_permission", "privacy_review"):
                        expected = "passed" if field == "privacy_review" else "allowed"
                        if data.get(field) != expected:
                            errors.append(f"{data_path}: redistributable document requires {field}={expected}")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{data_path}: cannot load JSON: {exc}")
        except Exception as exc:
            errors.append(f"{data_path}: validation failed: {exc}")

    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1
    print(f"Validated {len(checks)} collection resource file(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
