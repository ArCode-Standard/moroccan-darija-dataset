#!/usr/bin/env python3
"""Fail-closed AWAL eligibility gate; emits physically separate train/evaluation files."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

VERIFIED_SOURCE_STATES = {"verified", "independently_verified"}
SPLITS = {"train", "validation", "test"}
PERMISSION_FIELDS = {"train": "training_permission", "validation": "evaluation_permission", "test": "evaluation_permission"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_records(path):
    raw = Path(path).read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        records = []
        for line_no, line in enumerate(raw.splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_no}: {exc}") from exc
        return records
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("input must be a JSON array, an object, a records object, or JSONL")


def normalized_hash(text):
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate(records, registry):
    errors = []
    sources = registry.get("sources", []) if isinstance(registry, dict) else []
    source_by_id = {
        item.get("source_id"): item for item in sources
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    ids = set()
    hashes_by_split = {"train": {}, "validation": {}, "test": {}}
    accepted = {"train": [], "validation": [], "test": []}

    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix}: record must be an object")
            continue
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"{prefix}: record_id is required")
        elif record_id in ids:
            errors.append(f"{prefix}: duplicate record_id {record_id!r}")
        else:
            ids.add(record_id)

        split = record.get("split")
        if not isinstance(split, str) or split not in SPLITS:
            errors.append(f"{prefix}: split must be one of train, validation, test")
            continue

        for field in ("text", "source_id", "source_locator", "permission_evidence"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{prefix}: {field} is required and must be non-empty")

        if record.get("rights_review_status") != "cleared":
            errors.append(f"{prefix}: rights_review_status must be 'cleared'")

        permission_field = PERMISSION_FIELDS[split]
        if record.get(permission_field) != "allowed":
            errors.append(f"{prefix}: {permission_field} must be 'allowed' for split={split}")

        source_id = record.get("source_id")
        source = source_by_id.get(source_id) if isinstance(source_id, str) else None
        if source is None:
            errors.append(f"{prefix}: source_id {source_id!r} is absent from the source registry")
        else:
            if source.get("evidence_status") not in VERIFIED_SOURCE_STATES:
                errors.append(f"{prefix}: source {source_id!r} is not independently verified")
            declared = source.get("declared_permissions")
            expected_use = "training" if split == "train" else "evaluation"
            if not isinstance(declared, dict) or declared.get(expected_use) != "allowed":
                errors.append(f"{prefix}: source {source_id!r} lacks explicit {expected_use} permission")

        text = record.get("text")
        if isinstance(text, str) and text.strip():
            digest = normalized_hash(text)
            hashes_by_split[split].setdefault(digest, []).append(record_id or f"index:{index}")
            accepted[split].append(record)

    train_hashes = set(hashes_by_split["train"])
    for split in ("validation", "test"):
        for digest in sorted(train_hashes.intersection(hashes_by_split[split])):
            errors.append(f"data leakage: normalized text hash {digest} appears in train and {split}")
    for digest in sorted(set(hashes_by_split["validation"]).intersection(hashes_by_split["test"])):
        errors.append(f"split collision: normalized text hash {digest} appears in validation and test")
    return errors, accepted


def write_jsonl(path, records):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rendered = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    destination.write_text(rendered, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON array/object or JSONL with split-tagged records")
    parser.add_argument("--registry", default="data/sources/registry.json")
    parser.add_argument("--training-output", required=True, help="output containing train records only")
    parser.add_argument("--evaluation-output", required=True, help="output containing validation and test records only")
    parser.add_argument("--check-only", action="store_true", help="validate without writing outputs")
    args = parser.parse_args()

    try:
        records = load_records(args.input)
        registry = load_json(args.registry)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors, accepted = validate(records, registry)
    if errors:
        print(f"BLOCKED: {len(errors)} eligibility error(s); no output written.")
        for error in errors:
            print(f"- {error}")
        return 1

    training = accepted["train"]
    evaluation = accepted["validation"] + accepted["test"]
    if not training:
        print("BLOCKED: no eligible training records; no output written.")
        return 1
    if not evaluation:
        print("BLOCKED: no eligible evaluation records; no output written.")
        return 1

    if not args.check_only:
        try:
            write_jsonl(args.training_output, training)
            write_jsonl(args.evaluation_output, evaluation)
        except OSError as exc:
            print(f"ERROR: could not write outputs: {exc}", file=sys.stderr)
            return 2

    print(f"ELIGIBLE: {len(training)} training record(s), {len(accepted['validation'])} validation record(s), {len(accepted['test'])} test record(s).")
    if args.check_only:
        print("Check-only mode: no files written.")
    else:
        print(f"Training output: {args.training_output}")
        print(f"Evaluation output: {args.evaluation_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
