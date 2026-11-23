#!/usr/bin/env python3
"""Intake a privacy-screened lexical candidate into the AWAL review quarantine."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_INPUT = {
    "form_original", "script", "variants", "proposed_meaning", "usage_note",
    "region_claim", "source_id", "source_locator", "observed_at",
    "collection_method", "privacy_checked", "evidence_note",
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="data/collection/candidates")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        payload = read_json(args.input)
        registry = read_json(ROOT / "data/sources/registry.json")
        schema = read_json(ROOT / "data/schemas/awal-candidate.schema.json")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read input or project metadata: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("ERROR: contribution must be a JSON object", file=sys.stderr)
        return 2
    unknown = sorted(set(payload) - ALLOWED_INPUT)
    if unknown:
        print("ERROR: unsupported fields (identity or unapproved metadata may be present): " + ", ".join(unknown), file=sys.stderr)
        return 2

    source_id = payload.get("source_id")
    known_sources = {
        item.get("source_id") for item in registry.get("sources", [])
        if isinstance(item, dict)
    }
    if not isinstance(source_id, str) or source_id not in known_sources:
        print(f"ERROR: source_id {source_id!r} is not registered; register and review the source first", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    existing = []
    if output_dir.exists():
        for path in output_dir.glob("CAND-*.json"):
            match = re.fullmatch(r"CAND-(\\d{6})", path.stem)
            if match:
                existing.append(int(match.group(1)))
    candidate_id = f"CAND-{max(existing, default=0) + 1:06d}"
    candidate = {
        "candidate_id": candidate_id,
        "language": "ary",
        "review_status": "discovered",
        "rights_review_status": "unknown",
        "training_permission": "unknown",
        "evaluation_permission": "unknown",
        "permission_evidence": None,
        **payload,
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
    rendered = json.dumps(candidate, ensure_ascii=False, indent=2) + "\\n"
    if args.dry_run:
        print(rendered, end="")
        print(f"DRY RUN: would write {destination}", file=sys.stderr)
        return 0
    output_dir.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")
    print(f"Created {destination.relative_to(ROOT) if destination.is_relative_to(ROOT) else destination}")
    print("Quarantined: discovered; rights unknown; never eligible for training without independent clearance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
