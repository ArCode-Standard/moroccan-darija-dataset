#!/usr/bin/env python3
"""Validate the AWAL bilingual collection seed without granting training eligibility."""
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/collection/awal-seed-v0.1.jsonl"
SCHEMA = ROOT / "data/schemas/awal-collection-record.schema.json"
REGISTRY = ROOT / "data/sources/registry.json"


def main():
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        lines = DATA.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read AWAL collection files: {exc}", file=sys.stderr)
        return 2

    sources = {item.get("source_id"): item for item in registry.get("sources", []) if isinstance(item, dict)}
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    seen_ids, seen_text = set(), set()
    errors, records = [], []

    for line_no, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc}")
            continue
        records.append(record)
        for error in validator.iter_errors(record):
            errors.append(f"line {line_no} {error.json_path}: {error.message}")
        if not isinstance(record, dict):
            continue
        ident = record.get("record_id")
        if ident in seen_ids:
            errors.append(f"line {line_no}: duplicate record_id {ident}")
        seen_ids.add(ident)
        for field in ("text_ar", "text_latin"):
            value = record.get(field)
            if isinstance(value, str):
                key = (field, " ".join(value.casefold().split()))
                if key in seen_text:
                    errors.append(f"line {line_no}: duplicate normalized {field}")
                seen_text.add(key)
        source = sources.get(record.get("source_id"))
        if source is None:
            errors.append(f"line {line_no}: unregistered source_id {record.get('source_id')!r}")
        if record.get("origin") == "synthetic":
            if not record.get("generator") or not record.get("generator_version") or not record.get("prompt_version"):
                errors.append(f"line {line_no}: synthetic record lacks generator provenance")
            if record.get("review_status") != "pending":
                errors.append(f"line {line_no}: synthetic seed must remain pending")
            if record.get("rights_review_status") != "unknown":
                errors.append(f"line {line_no}: synthetic seed rights must remain unknown")
            if record.get("training_permission") != "unknown":
                errors.append(f"line {line_no}: synthetic seed cannot be pre-approved for training")
            if record.get("evaluation_permission") != "not_allowed":
                errors.append(f"line {line_no}: synthetic seed cannot be used as evaluation data")
            if source and source.get("evidence_status") == "verified":
                errors.append(f"line {line_no}: synthetic source must not be treated as independently verified")

    if not records:
        errors.append("collection seed is empty")
    if errors:
        print(f"FAILED: {len(errors)} AWAL collection issue(s)")
        for error in errors:
            print("- " + error)
        return 1
    print(f"OK: {len(records)} AWAL collection records; bilingual fields and provenance valid")
    print("Policy: synthetic seed remains pending, training permission unknown, evaluation prohibited")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
