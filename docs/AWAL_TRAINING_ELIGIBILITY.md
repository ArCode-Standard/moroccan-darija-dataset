# AWAL Training Eligibility Gate

## Purpose

The eligibility gate is a fail-closed boundary between collected material and any AWAL training/evaluation export. It does not determine legal rights; it enforces that documented, independently reviewed decisions exist before a record can leave intake.

## Mandatory record metadata

Every record submitted to the gate must contain:

- `record_id`: stable unique identifier.
- `text`: the actual training/evaluation text.
- `source_id`: exact key in `data/sources/registry.json`.
- `source_locator`: exact record/page/row/section locator; a source homepage alone is insufficient.
- `permission_evidence`: controlled evidence reference that a reviewer can verify.
- `rights_review_status`: exactly `cleared`.
- `training_permission` and `evaluation_permission`: separate explicit decisions.
- `split`: exactly `train`, `validation`, or `test`.

The registry source must also have `evidence_status=verified` or `independently_verified`, and its `declared_permissions` must explicitly allow the intended use (`training` for train; `evaluation` for validation/test). Missing registry fields are treated as denial.

## Separation and leakage prevention

The gate writes two different files:

- Training output: `train` records only.
- Evaluation output: `validation` and `test` records only.

It rejects duplicate record IDs, normalized-text overlap between training and evaluation, and overlap between validation and test. Normalization is used only to detect leakage; original text is preserved in outputs. Outputs are written only if the entire input passes.

## Usage

Input may be a JSON array, an object containing a `records` array, or JSONL.

```bash
python scripts/awal_training_gate.py \
  --input path/to/curated-records.jsonl \
  --registry data/sources/registry.json \
  --training-output build/awal/train.jsonl \
  --evaluation-output build/awal/evaluation.jsonl
```

Audit without writing:

```bash
python scripts/awal_training_gate.py \
  --input path/to/curated-records.jsonl \
  --check-only \
  --training-output build/awal/train.jsonl \
  --evaluation-output build/awal/evaluation.jsonl
```

## Current repository status

The existing lexicon is not automatically eligible. The current registry contains source families whose evidence or training permissions remain unresolved, and the current records do not yet consistently carry record-level locators and permission evidence. Therefore this gate is expected to reject unresolved records until a human rights review updates both record metadata and the source registry. No legacy record is auto-approved, and no permission is inferred from a repository-level license, public availability, or a source name.

This gate is an engineering control, not legal advice or a substitute for checking the underlying evidence.
