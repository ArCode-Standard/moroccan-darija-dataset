#!/usr/bin/env python3
"""Validate source registry, lexical candidates, and corpus metadata."""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

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
    parser.add_argument("--candidate-dir", default="data/collection/candidates")
    parser.add_argument("--candidates", nargs="*", default=None)
    parser.add_argument("--candidate-schema", default="schemas/lexical-candidate.schema.json")
    parser.add_argument("--document-dir", default="data/collection/documents")
    parser.add_argument("--documents", nargs="*", default=None)
    parser.add_argument("--document-schema", default="schemas/corpus-document.schema.json")
    args = parser.parse_args()

    errors = []
    source_ids = set()
    checks = [(args.sources, args.source_schema, "sources")]
    candidate_paths = args.candidates if args.candidates is not None else sorted(str(p) for p in Path(args.candidate_dir).glob("*.json"))
    document_paths = args.documents if args.documents is not None else sorted(str(p) for p in Path(args.document_dir).glob("*.json"))
    checks += [(p, args.candidate_schema, "candidate") for p in candidate_paths]
    checks += [(p, args.document_schema, "document") for p in document_paths]

    for data_path, schema_path, kind in checks:
        try:
            found, data = validate_file(data_path, schema_path)
            errors.extend(found)
            if kind == "sources" and isinstance(data, dict):
                for i, source in enumerate(data.get("sources", [])):
                    source_id = source.get("source_id")
                    if source_id in source_ids:
                        errors.append(f"{data_path}: duplicate source_id {source_id}")
                    source_ids.add(source_id)
                    if source.get("personal_data_collected") is not False:
                        errors.append(f"{data_path}: sources[{i}].personal_data_collected must be false")
                    if source.get("user_tracking_performed") is not False:
                        errors.append(f"{data_path}: sources[{i}].user_tracking_performed must be false")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{data_path}: cannot load JSON: {exc}")
        except Exception as exc:
            errors.append(f"{data_path}: validation failed: {exc}")

    # Cross-reference records only after loading the registry.
    for data_path, schema_path, kind in checks:
        if kind not in ("candidate", "document"):
            continue
        try:
            data = load(data_path)
            if data.get("source_id") not in source_ids:
                errors.append(f"{data_path}: unknown source_id {data.get('source_id')!r}")
            if kind == "candidate" and data.get("privacy_checked") is not True:
                errors.append(f"{data_path}: privacy_checked must be true before review intake")
            if kind == "document":
                if data.get("personal_data_present") is True and data.get("publication_status") != "excluded":
                    errors.append(f"{data_path}: documents with personal data must be excluded")
                if data.get("publication_status") == "redistributable":
                    for field, expected in (("storage_permission","allowed"),("redistribution_permission","allowed"),("privacy_review","passed")):
                        if data.get(field) != expected:
                            errors.append(f"{data_path}: redistributable document requires {field}={expected}")
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass

    if errors:
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1
    print(f"Validated {len(checks)} collection resource file(s); {len(candidate_paths)} candidate(s), {len(document_paths)} corpus document(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
