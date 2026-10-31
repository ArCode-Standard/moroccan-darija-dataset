#!/usr/bin/env python3
"""Create a reviewable Darija lexical candidate from a JSON contribution."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON contribution file")
    parser.add_argument("--output-dir", default="data/collection/candidates")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        payload = read_json(args.input)
        registry = read_json(ROOT / "data/collection/source-registry.json")
        schema = read_json(ROOT / "schemas/lexical-candidate.schema.json")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read input or project metadata: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("ERROR: contribution must be a JSON object", file=sys.stderr)
        return 2

    source_id = payload.get("source_id")
    known_sources = {s["source_id"] for s in registry.get("sources", [])}
    if source_id not in known_sources:
        print(f"ERROR: unknown source_id {source_id!r}; register and review the source first", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir

    existing_ids = []
    if output_dir.exists():
        for path in output_dir.glob("CAND-*.json"):
            match = re.fullmatch(r"CAND-(\d{6})", path.stem)
            if match:
                existing_ids.append(int(match.group(1)))
    candidate_id = f"CAND-{max(existing_ids, default=0) + 1:06d}"

    # Only accept contributor-supplied fields from the allowlist; never ingest identity/profile fields.
    allowed = {
        "form_original", "script", "variants", "entry_type", "proposed_meaning",
        "part_of_speech", "usage_note", "region_claim", "source_id", "observed_at",
        "collection_method", "privacy_checked", "evidence_note"
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        print("ERROR: unsupported fields (possible personal data or schema mismatch): " + ", ".join(unknown), file=sys.stderr)
        return 2

    candidate = {
        "candidate_id": candidate_id,
        "language": "ary",
        "review_status": "discovered",
        "rights_status": "unknown",
        **payload
    }

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(candidate), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    if errors:
        for error in errors:
            print(f"ERROR: {error.json_path}: {error.message}", file=sys.stderr)
        return 2

    destination = output_dir / f"{candidate_id}.json"
    if destination.exists():
        print(f"ERROR: refusing to overwrite {destination}", file=sys.stderr)
        return 2

    rendered = json.dumps(candidate, ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        print(rendered, end="")
        print(f"DRY RUN: would write {destination}", file=sys.stderr)
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")
    print(f"Created {destination.relative_to(ROOT) if destination.is_relative_to(ROOT) else destination}")
    print("Status: discovered; rights_status: unknown; human review required.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
