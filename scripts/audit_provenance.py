#!/usr/bin/env python3
"""Audit record-level provenance and rights metadata without inferring permission."""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PERMISSIONS = ("redistribution_permission", "training_permission", "commercial_permission")
REQUIRED_PROVENANCE = ("source_type", *PERMISSIONS)
REVIEWED_RIGHTS = {"cleared", "restricted", "pending_verification", "unknown", "excluded"}


def audit_resource(resource, resource_name, registry_ids=None):
    findings = []
    summary = {
        "resource": resource_name,
        "records": 0,
        "source_type_counts": {},
        "review_status_counts": {},
        "permission_counts": {field: {} for field in PERMISSIONS},
        "missing_or_unknown": Counter(),
        "unmapped_source_ids": 0,
        "records_with_permission_evidence": 0,
        "records_with_source_locator": 0,
        "records_with_rights_review_status": 0,
    }
    if not isinstance(resource, dict):
        return summary, [f"{resource_name}: root must be an object"]
    entries_key = "entries" if isinstance(resource.get("entries"), list) else "examples"
    records = resource.get(entries_key)
    if not isinstance(records, list):
        return summary, [f"{resource_name}: expected 'entries' or 'examples' array"]

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            findings.append(f"{resource_name}[{index}]: record must be an object")
            continue
        summary["records"] += 1
        ident = record.get("id", index)
        prefix = f"{resource_name}[{ident}]"
        provenance = record.get("provenance")
        if not isinstance(provenance, dict):
            provenance = {}
            findings.append(f"{prefix}: missing provenance object")
        source_type = provenance.get("source_type", "missing")
        if not isinstance(source_type, str):
            source_type = "invalid"
        summary["source_type_counts"][source_type] = summary["source_type_counts"].get(source_type, 0) + 1
        review = record.get("review")
        review_status = review.get("status", "missing") if isinstance(review, dict) else "missing"
        if not isinstance(review_status, str):
            review_status = "invalid"
        summary["review_status_counts"][review_status] = summary["review_status_counts"].get(review_status, 0) + 1

        for field in REQUIRED_PROVENANCE:
            value = provenance.get(field)
            if value in (None, "", "unknown"):
                summary["missing_or_unknown"][field] += 1
        for field in PERMISSIONS:
            value = provenance.get(field, "missing")
            if not isinstance(value, str):
                value = "invalid"
            counts = summary["permission_counts"][field]
            counts[value] = counts.get(value, 0) + 1
        source_id = provenance.get("source_id")
        if isinstance(source_id, str) and source_id:
            if registry_ids is not None and source_id not in registry_ids:
                summary["unmapped_source_ids"] += 1
                findings.append(f"{prefix}: source_id '{source_id}' is not present in the source registry")
        else:
            summary["missing_or_unknown"]["source_id"] += 1
        if isinstance(provenance.get("permission_evidence"), str) and provenance.get("permission_evidence").strip():
            summary["records_with_permission_evidence"] += 1
        else:
            summary["missing_or_unknown"]["permission_evidence"] += 1
        if isinstance(provenance.get("source_locator"), str) and provenance.get("source_locator").strip():
            summary["records_with_source_locator"] += 1
        elif source_type in {"dictionary", "corpus", "web", "other"}:
            summary["missing_or_unknown"]["source_locator"] += 1
        if isinstance(provenance.get("rights_review_status"), str) and provenance.get("rights_review_status") in REVIEWED_RIGHTS:
            summary["records_with_rights_review_status"] += 1
        else:
            summary["missing_or_unknown"]["rights_review_status"] += 1

        for field in PERMISSIONS:
            value = provenance.get(field)
            if value == "allowed" and not (isinstance(provenance.get("permission_evidence"), str) and provenance.get("permission_evidence").strip()):
                findings.append(f"{prefix}: {field}=allowed but permission_evidence is absent")
    summary["source_type_counts"] = dict(sorted(summary["source_type_counts"].items()))
    summary["review_status_counts"] = dict(sorted(summary["review_status_counts"].items()))
    summary["permission_counts"] = {
        field: dict(sorted(counts.items())) for field, counts in summary["permission_counts"].items()
    }
    summary["missing_or_unknown"] = dict(sorted(summary["missing_or_unknown"].items()))
    return summary, findings


def build_report(resources, registry):
    source_ids = None
    if isinstance(registry, dict) and isinstance(registry.get("sources"), list):
        source_ids = {
            source.get("source_id") for source in registry["sources"]
            if isinstance(source, dict) and isinstance(source.get("source_id"), str)
        }
    summaries, findings = [], []
    for name, resource in resources:
        summary, resource_findings = audit_resource(resource, name, source_ids)
        summaries.append(summary)
        findings.extend(resource_findings)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "Unknown or missing permission is not permission. This report is a metadata audit, not legal clearance.",
        "resources": summaries,
        "findings": findings,
    }


def render_markdown(report):
    lines = [
        "# Provenance and Rights Metadata Audit",
        "",
        f"Generated: {report['generated_at']}",
        "",
        f"> {report['policy']}",
        "",
        "| Resource | Records | Source types | Review statuses | Missing/unknown fields |",
        "|---|---:|---|---|---|",
    ]
    for item in report["resources"]:
        sources = ", ".join(f"{k}: {v}" for k, v in item["source_type_counts"].items()) or "—"
        reviews = ", ".join(f"{k}: {v}" for k, v in item["review_status_counts"].items()) or "—"
        gaps = ", ".join(f"{k}: {v}" for k, v in item["missing_or_unknown"].items()) or "—"
        lines.append(f"| {item['resource']} | {item['records']} | {sources} | {reviews} | {gaps} |")
    lines += ["", f"## Findings ({len(report['findings'])})", ""]
    lines += [f"- {finding}" for finding in report["findings"]] or ["- No structural findings."]
    lines += ["", "This report does not determine whether a use is lawful. Human rights review and source evidence remain necessary."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/moroccan-darija.json")
    parser.add_argument("--contexts", default="data/context-examples.json")
    parser.add_argument("--regional", default="data/regions/north.json")
    parser.add_argument("--registry", default="data/sources/registry.json")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--strict", action="store_true", help="return non-zero when findings exist")
    args = parser.parse_args()
    try:
        resources = []
        for name, path in (("lexicon", args.dataset), ("contexts", args.contexts), ("regional_north", args.regional)):
            file_path = Path(path)
            if file_path.exists():
                resources.append((name, json.loads(file_path.read_text(encoding="utf-8"))))
        registry_path = Path(args.registry)
        registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else None
        report = build_report(resources, registry)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.json_out:
            Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_out).write_text(rendered, encoding="utf-8")
        if args.markdown_out:
            Path(args.markdown_out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.markdown_out).write_text(render_markdown(report), encoding="utf-8")
        print(render_markdown(report))
        return 1 if args.strict and report["findings"] else 0
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
