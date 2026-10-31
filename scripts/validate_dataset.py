#!/usr/bin/env python3
"""Audit and validate the Moroccan Darija dataset and its provenance registry.

Default mode performs structural validation and reports missing rights/context as
warnings so the legacy dataset remains auditable during migration.
Use --strict-public to reject every record that is not explicitly cleared for
redistribution. This mode is intended for release/export gates.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ("id", "category", "darija_ar", "darija_latin", "fusha_ar", "fr")
ENTRY_TYPES = {"word", "expression", "sentence", "proverb", "question", "conversational", "unknown"}
REVIEW = {"pending", "in_review", "reviewed", "rejected", "needs_correction", "unknown"}
PERMISSIONS = {"allowed", "not_allowed", "unknown", "not_applicable"}
RIGHTS_STATUS = {"cleared", "restricted", "pending_verification", "unknown", "excluded"}
SOURCE_TYPES = {"original", "contributor", "dictionary", "corpus", "web", "publication", "other", "unknown"}
COLLECTION_METHODS = {"elicitation", "observation", "manual_entry", "published_resource", "other", "unknown"}
REGISTERS = {"neutral", "formal", "informal", "vulgar", "literary", "religious", "unknown"}

def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid UTF-8 JSON from {path}: {exc}") from exc

def validate_sources(registry):
    errors, warnings = [], []
    if not isinstance(registry, dict) or not isinstance(registry.get("sources"), list):
        return ["sources.json: expected object with a sources array"], warnings, {}
    indexed = {}
    for i, source in enumerate(registry["sources"]):
        p = f"sources[{i}]"
        if not isinstance(source, dict):
            errors.append(f"{p}: expected object")
            continue
        sid = source.get("source_id")
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"{p}.source_id: required non-empty string")
            continue
        if sid in indexed:
            errors.append(f"{p}.source_id: duplicate '{sid}'")
        indexed[sid] = source
        if source.get("source_type") not in SOURCE_TYPES:
            errors.append(f"{p}.source_type: missing or unsupported value")
        for field in ("redistribution_permission", "training_permission", "commercial_permission"):
            if source.get(field) not in PERMISSIONS:
                errors.append(f"{p}.{field}: missing or unsupported permission")
        if source.get("rights_status") not in RIGHTS_STATUS:
            errors.append(f"{p}.rights_status: missing or unsupported value")
        if source.get("redistribution_permission") == "allowed":
            if not source.get("license") and not source.get("permission_evidence"):
                errors.append(f"{p}: redistribution marked allowed without license or permission evidence")
        if source.get("rights_status") == "cleared":
            required = ("rights_holder", "permission_evidence")
            for field in required:
                if not source.get(field):
                    errors.append(f"{p}: cleared source requires {field}")
            if source.get("redistribution_permission") != "allowed":
                errors.append(f"{p}: cleared source must explicitly allow redistribution")
    return errors, warnings, indexed

def validate(data, sources=None, strict_public=False):
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["root: expected a JSON object"], warnings
    for key in ("meta", "categories", "entries"):
        if key not in data:
            errors.append(f"root: missing required key '{key}'")
    if errors:
        return errors, warnings
    meta, categories, entries = data["meta"], data["categories"], data["entries"]
    if not isinstance(meta, dict):
        return ["meta: expected an object"], warnings
    if not isinstance(categories, list):
        return ["categories: expected an array"], warnings
    if not isinstance(entries, list):
        return ["entries: expected an array"], warnings

    declared, actual, ids = {}, Counter(), set()
    for i, item in enumerate(categories):
        if not isinstance(item, dict) or not isinstance(item.get("category"), str) or not isinstance(item.get("count"), int) or isinstance(item.get("count"), bool):
            errors.append(f"categories[{i}]: expected category string and integer count")
            continue
        name = item["category"]
        if not name.strip(): errors.append(f"categories[{i}].category: empty")
        if name in declared: errors.append(f"categories[{i}]: duplicate category '{name}'")
        declared[name] = item["count"]
        if item["count"] < 0: errors.append(f"categories[{i}].count: must be >= 0")

    source_index = sources or {}
    for i, e in enumerate(entries):
        p = f"entries[{i}]"
        if not isinstance(e, dict):
            errors.append(f"{p}: expected object")
            continue
        for field in REQUIRED:
            if field not in e:
                errors.append(f"{p}: missing '{field}'")
            elif field != "id" and (not isinstance(e[field], str) or not e[field].strip()):
                errors.append(f"{p}.{field}: expected non-empty string")
        ident = e.get("id")
        if isinstance(ident, bool) or not isinstance(ident, int) or ident < 1:
            errors.append(f"{p}.id: expected positive integer")
        elif ident in ids:
            errors.append(f"{p}.id: duplicate id {ident}")
        else:
            ids.add(ident)
        cat = e.get("category")
        if isinstance(cat, str):
            actual[cat] += 1
            if cat not in declared: errors.append(f"{p}.category: unknown category '{cat}'")
        if "entry_type" in e and e["entry_type"] not in ENTRY_TYPES:
            errors.append(f"{p}.entry_type: unsupported value")
        if "register" in e and e["register"] not in REGISTERS:
            errors.append(f"{p}.register: unsupported value")
        if "review" in e:
            r = e["review"]
            if not isinstance(r, dict) or r.get("status") not in REVIEW:
                errors.append(f"{p}.review.status: missing or unsupported status")

        prov = e.get("provenance")
        if not isinstance(prov, dict):
            warnings.append(f"{p}.provenance: missing; source and rights unresolved")
            if strict_public: errors.append(f"{p}: not publishable without provenance")
        else:
            sid = prov.get("source_id")
            if not sid:
                errors.append(f"{p}.provenance.source_id: required")
            elif sid not in source_index:
                errors.append(f"{p}.provenance.source_id: '{sid}' not found in data/sources.json")
            for field in ("redistribution_permission", "training_permission", "commercial_permission"):
                value = prov.get(field)
                if value not in PERMISSIONS:
                    errors.append(f"{p}.provenance.{field}: missing or unsupported permission")
                elif value == "unknown":
                    warnings.append(f"{p}.provenance.{field}: unknown")
            status = prov.get("rights_status", "unknown")
            if status not in RIGHTS_STATUS:
                errors.append(f"{p}.provenance.rights_status: unsupported value")
            if status != "cleared" or prov.get("redistribution_permission") != "allowed":
                if strict_public: errors.append(f"{p}: rights not cleared for public redistribution")
            if status == "cleared":
                if not prov.get("permission_evidence") or not prov.get("rights_holder"):
                    errors.append(f"{p}: cleared rights require rights_holder and permission_evidence")
                if prov.get("redistribution_permission") != "allowed":
                    errors.append(f"{p}: cleared status conflicts with redistribution permission")
            if sid in source_index:
                source = source_index[sid]
                for field in ("redistribution_permission", "training_permission", "commercial_permission"):
                    if source.get(field) != prov.get(field):
                        warnings.append(f"{p}: entry {field} differs from registry source '{sid}'")

        if "senses" in e:
            if not isinstance(e["senses"], list):
                errors.append(f"{p}.senses: expected array")
            else:
                seen_senses = set()
                for j, sense in enumerate(e["senses"]):
                    q = f"{p}.senses[{j}]"
                    if not isinstance(sense, dict):
                        errors.append(f"{q}: expected object")
                        continue
                    sid = sense.get("sense_id")
                    if not isinstance(sid, str) or not sid.strip():
                        errors.append(f"{q}.sense_id: required")
                    elif sid in seen_senses:
                        errors.append(f"{q}.sense_id: duplicate within entry")
                    else:
                        seen_senses.add(sid)
                    if "examples" in sense and not isinstance(sense["examples"], list):
                        errors.append(f"{q}.examples: expected array")
                    elif isinstance(sense.get("examples"), list):
                        for k, example in enumerate(sense["examples"]):
                            validate_example(example, f"{q}.examples[{k}]", source_index, errors, warnings, strict_public)

        if "examples" in e:
            if not isinstance(e["examples"], list):
                errors.append(f"{p}.examples: expected array")
            else:
                for j, example in enumerate(e["examples"]):
                    validate_example(example, f"{p}.examples[{j}]", source_index, errors, warnings, strict_public)

        if strict_public and e.get("publication_status") != "publishable":
            errors.append(f"{p}: publication_status must be publishable")
        if not strict_public and e.get("publication_status") in (None, "pending_verification"):
            warnings.append(f"{p}.publication_status: not explicitly approved for publication")

    if len(entries) != meta.get("entries_count):
        errors.append(f"meta.entries_count: declared {meta.get('entries_count')}, actual {len(entries)}")
    if len(categories) != meta.get("categories_count"):
        errors.append(f"meta.categories_count: declared {meta.get('categories_count')}, actual {len(categories)}")
    for cat, count in declared.items():
        if count != actual[cat]: errors.append(f"categories['{cat}'].count: declared {count}, actual {actual[cat]}")
    extra = set(actual) - set(declared)
    if extra: errors.append("entries: undeclared categories: " + ", ".join(sorted(extra)))
    return errors, warnings

def validate_example(example, path, source_index, errors, warnings, strict_public):
    if not isinstance(example, dict):
        errors.append(f"{path}: expected object")
        return
    if not isinstance(example.get("darija_ar"), str) or not example["darija_ar"].strip():
        errors.append(f"{path}.darija_ar: required non-empty string")
    if not isinstance(example.get("is_attested"), bool):
        errors.append(f"{path}.is_attested: required boolean")
    sid = example.get("source_id")
    if not isinstance(sid, str) or not sid:
        errors.append(f"{path}.source_id: required")
    elif sid not in source_index:
        errors.append(f"{path}.source_id: '{sid}' not found in data/sources.json")
    if strict_public and sid in source_index:
        source = source_index[sid]
        if source.get("rights_status") != "cleared" or source.get("redistribution_permission") != "allowed":
            errors.append(f"{path}: example source is not cleared for redistribution")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", nargs="?", default="data/moroccan-darija.json")
    parser.add_argument("--sources", default="data/sources.json")
    parser.add_argument("--strict-public", action="store_true",
                        help="fail unless every entry/example is explicitly cleared for public redistribution")
    args = parser.parse_args()
    try:
        data = load_json(args.dataset)
        registry = load_json(args.sources)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    source_errors, _, source_index = validate_sources(registry)
    errors, warnings = validate(data, source_index, args.strict_public)
    errors = source_errors + errors
    print(f"Dataset audit: {len(data.get('entries', []))} entries; {len(source_index)} registered sources")
    print(f"Warnings: {len(warnings)}; errors: {len(errors)}")
    if warnings:
        print("WARNINGS:")
        for item in warnings: print("- " + item)
    if errors:
        print("ERRORS:")
        for item in errors: print("- " + item)
        return 1
    print("OK: structural validation passed" + (" (strict publication gate)" if args.strict_public else " (audit mode)"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
