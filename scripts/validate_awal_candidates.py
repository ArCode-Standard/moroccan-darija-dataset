#!/usr/bin/env python3
"""Validate quarantined AWAL candidate records and their source references."""
import argparse
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="data/sources/registry.json")
    parser.add_argument("--schema", default="data/schemas/awal-candidate.schema.json")
    parser.add_argument("--candidate-dir", default="data/collection/candidates")
    args = parser.parse_args()
    try:
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    sources = {s.get("source_id") for s in registry.get("sources", []) if isinstance(s, dict)}
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    paths = sorted(Path(args.candidate_dir).glob("CAND-*.json"))
    errors = []
    for path in paths:
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: cannot read JSON: {exc}")
            continue
        errors.extend(f"{path}: {e.json_path}: {e.message}" for e in validator.iter_errors(item))
        if isinstance(item, dict) and item.get("source_id") not in sources:
            errors.append(f"{path}: source_id is not registered")
        if isinstance(item, dict) and item.get("privacy_checked") is not True:
            errors.append(f"{path}: privacy_checked must be true")
    if errors:
        print("\n".join("ERROR: " + e for e in errors))
        return 1
    print(f"Validated {len(paths)} quarantined candidate(s); none is auto-approved for training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
